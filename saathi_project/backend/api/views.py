"""
API Views for Saathi backend.
"""

import logging
import tempfile
import json
from typing import Dict, Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser

from .models import UserProfile, Conversation, ScreeningResult, UserMemory, UploadedDocument, CrisisEvent
from .langgraph import get_ai_pipeline
from .ai_services import get_rag_service, get_transcription_service
from .serializers import (
    UserProfileSerializer, ConversationSerializer, 
    ScreeningResultSerializer, UserMemorySerializer
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(APIView):
    """Main chat endpoint - processes conversations through AI pipeline."""
    
    def post(self, request):
        try:
            data = request.data
            uid = data.get('uid')
            message = data.get('message')
            history = data.get('history', [])
            context = data.get('context', {})
            
            if not uid or not message:
                return Response(
                    {'error': 'uid and message are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create user profile
            user_profile, created = UserProfile.objects.get_or_create(
                uid=uid,
                defaults={'consent_data_storage': True}  # Default consent
            )
            
            # Process through AI pipeline
            ai_pipeline = get_ai_pipeline()
            pipeline_result = ai_pipeline.process_conversation(
                uid=uid,
                message=message,
                history=history,
                context=context
            )
            
            # Save conversation if user has consented
            if user_profile.consent_data_storage:
                conversation = Conversation.objects.create(
                    user_profile=user_profile,
                    session_id=data.get('session_id', f'session_{uid}'),
                    user_message=message,
                    ai_response=pipeline_result['reply'],
                    crisis_detected=pipeline_result['crisis'],
                    context_data=context,
                    memory_updates=pipeline_result.get('memory_update', {}),
                    response_time_ms=0  # TODO: Track actual response time
                )
                
                # Save crisis event if detected
                if pipeline_result['crisis'] and pipeline_result.get('crisis_log'):
                    CrisisEvent.objects.create(
                        user_profile=user_profile,
                        conversation=conversation,
                        crisis_type=pipeline_result['crisis_log']['crisis_type'],
                        severity_score=pipeline_result['crisis_log']['severity_score'],
                        trigger_keywords=pipeline_result['crisis_log']['trigger_keywords'],
                        emergency_resources_provided=True
                    )
                
                # Update user memories
                memory_updates = pipeline_result.get('memory_update', {})
                for memory_type, items in memory_updates.items():
                    if isinstance(items, list):
                        for item in items:
                            UserMemory.objects.update_or_create(
                                user_profile=user_profile,
                                memory_type=memory_type,
                                key=item.lower().replace(' ', '_'),
                                defaults={
                                    'value': item,
                                    'source_conversation': conversation
                                }
                            )
            
            return Response({
                'reply': pipeline_result['reply'],
                'crisis': pipeline_result['crisis'],
                'suggested_coping': pipeline_result.get('suggested_coping', []),
                'memory_update': pipeline_result.get('memory_update', {}),
                'escalation': pipeline_result.get('escalation')
            })
            
        except Exception as e:
            logger.error(f"Chat API error: {e}")
            return Response(
                {
                    'error': 'Internal server error',
                    'reply': "I'm having some technical difficulties. Please try again, or if you're in crisis, contact emergency services."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class TranscribeAPIView(APIView):
    """Audio transcription endpoint."""
    
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        try:
            if 'audio' not in request.FILES:
                return Response(
                    {'error': 'Audio file is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            audio_file = request.FILES['audio']
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            try:
                # Transcribe using AI service
                transcription_service = get_transcription_service()
                result = transcription_service.transcribe_audio(temp_path)
                
                if result['success']:
                    return Response({
                        'text': result['text'],
                        'service': result.get('service', 'unknown')
                    })
                else:
                    return Response(
                        {
                            'error': result.get('error', 'Transcription failed'),
                            'text': ''
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            finally:
                # Clean up temp file
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Transcription API error: {e}")
            return Response(
                {'error': 'Transcription service error', 'text': ''},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class IngestFileAPIView(APIView):
    """Document ingestion endpoint for RAG."""
    
    def post(self, request):
        try:
            data = request.data
            file_url = data.get('fileUrl')
            uid = data.get('uid')
            filename = data.get('filename', 'uploaded_document')
            
            if not file_url or not uid:
                return Response(
                    {'error': 'fileUrl and uid are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user profile
            user_profile = UserProfile.objects.filter(uid=uid).first()
            if not user_profile:
                return Response(
                    {'error': 'User profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create document record
            document = UploadedDocument.objects.create(
                user_profile=user_profile,
                filename=filename,
                file_url=file_url,
                processing_status='processing'
            )
            
            try:
                # Process document with RAG service
                rag_service = get_rag_service()
                result = rag_service.ingest_document(file_url, uid, filename)
                
                if result['success']:
                    document.processing_status = 'completed'
                    document.chunk_count = result['chunks_added']
                    document.extracted_text = result.get('extracted_text', '')
                    document.save()
                    
                    return Response({
                        'success': True,
                        'message': f'Document processed successfully. Added {result["chunks_added"]} chunks.',
                        'chunks_added': result['chunks_added'],
                        'document_id': document.id
                    })
                else:
                    document.processing_status = 'failed'
                    document.error_message = result['error']
                    document.save()
                    
                    return Response({
                        'success': False,
                        'error': result['error'],
                        'chunks_added': 0
                    })
                    
            except Exception as e:
                document.processing_status = 'failed'
                document.error_message = str(e)
                document.save()
                raise
                
        except Exception as e:
            logger.error(f"File ingestion API error: {e}")
            return Response(
                {'error': 'File ingestion failed', 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileAPIView(APIView):
    """User profile management."""
    
    def get(self, request):
        uid = request.query_params.get('uid')
        if not uid:
            return Response({'error': 'uid parameter required'}, status=400)
        
        user_profile = UserProfile.objects.filter(uid=uid).first()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=404)
        
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)
    
    def post(self, request):
        try:
            data = request.data
            uid = data.get('uid')
            
            if not uid:
                return Response({'error': 'uid is required'}, status=400)
            
            user_profile, created = UserProfile.objects.update_or_create(
                uid=uid,
                defaults={
                    'email': data.get('email'),
                    'display_name': data.get('display_name'),
                    'consent_data_storage': data.get('consent_data_storage', True),
                    'consent_screening_storage': data.get('consent_screening_storage', False),
                    'theme_preference': data.get('theme_preference', 'light')
                }
            )
            
            serializer = UserProfileSerializer(user_profile)
            return Response({
                'profile': serializer.data,
                'created': created
            })
            
        except Exception as e:
            logger.error(f"Profile API error: {e}")
            return Response({'error': 'Profile update failed'}, status=500)


class ScreeningAPIView(APIView):
    """Mental health screening assessments."""
    
    def post(self, request):
        try:
            data = request.data
            uid = data.get('uid')
            screening_type = data.get('screening_type')
            responses = data.get('responses', [])
            
            if not all([uid, screening_type, responses]):
                return Response(
                    {'error': 'uid, screening_type, and responses are required'},
                    status=400
                )
            
            user_profile = UserProfile.objects.filter(uid=uid).first()
            if not user_profile:
                return Response({'error': 'User profile not found'}, status=404)
            
            # Calculate score based on screening type
            scoring_result = self._calculate_screening_score(screening_type, responses)
            
            # Only save if user has consented to screening data storage
            if user_profile.consent_screening_storage:
                screening_result = ScreeningResult.objects.create(
                    user_profile=user_profile,
                    screening_type=screening_type,
                    total_score=scoring_result['total_score'],
                    max_possible_score=scoring_result['max_score'],
                    severity_level=scoring_result['severity'],
                    responses=responses,
                    recommendations=scoring_result['recommendations'],
                    follow_up_needed=scoring_result['follow_up_needed']
                )
                
                serializer = ScreeningResultSerializer(screening_result)
                saved_data = serializer.data
            else:
                saved_data = None
            
            return Response({
                'result': scoring_result,
                'saved': saved_data,
                'consent_required': not user_profile.consent_screening_storage
            })
            
        except Exception as e:
            logger.error(f"Screening API error: {e}")
            return Response({'error': 'Screening processing failed'}, status=500)
    
    def _calculate_screening_score(self, screening_type: str, responses: list) -> dict:
        """Calculate screening scores based on type."""
        
        if screening_type == 'PHQ9':
            return self._calculate_phq9_score(responses)
        elif screening_type == 'GAD7':
            return self._calculate_gad7_score(responses)
        elif screening_type == 'GHQ12':
            return self._calculate_ghq12_score(responses)
        else:
            return {
                'total_score': 0,
                'max_score': 0,
                'severity': 'unknown',
                'recommendations': 'Unknown screening type',
                'follow_up_needed': False
            }
    
    def _calculate_phq9_score(self, responses: list) -> dict:
        """Calculate PHQ-9 depression screening score."""
        total_score = sum(responses[:9])  # First 9 questions
        max_score = 27
        
        if total_score <= 4:
            severity = 'minimal'
            recommendations = 'Monitor symptoms. Consider lifestyle improvements.'
            follow_up = False
        elif total_score <= 9:
            severity = 'mild'
            recommendations = 'Consider counseling or therapy. Monitor closely.'
            follow_up = True
        elif total_score <= 14:
            severity = 'moderate'
            recommendations = 'Counseling recommended. Consider professional help.'
            follow_up = True
        elif total_score <= 19:
            severity = 'moderately_severe'
            recommendations = 'Professional therapy strongly recommended.'
            follow_up = True
        else:
            severity = 'severe'
            recommendations = 'Immediate professional help recommended. Consider psychiatrist consultation.'
            follow_up = True
        
        return {
            'total_score': total_score,
            'max_score': max_score,
            'severity': severity,
            'recommendations': recommendations,
            'follow_up_needed': follow_up
        }
    
    def _calculate_gad7_score(self, responses: list) -> dict:
        """Calculate GAD-7 anxiety screening score."""
        total_score = sum(responses[:7])  # First 7 questions
        max_score = 21
        
        if total_score <= 4:
            severity = 'minimal'
            recommendations = 'Anxiety symptoms are minimal. Continue healthy habits.'
            follow_up = False
        elif total_score <= 9:
            severity = 'mild'
            recommendations = 'Mild anxiety. Consider stress management techniques.'
            follow_up = True
        elif total_score <= 14:
            severity = 'moderate'
            recommendations = 'Moderate anxiety. Professional support recommended.'
            follow_up = True
        else:
            severity = 'severe'
            recommendations = 'Severe anxiety. Professional treatment strongly recommended.'
            follow_up = True
        
        return {
            'total_score': total_score,
            'max_score': max_score,
            'severity': severity,
            'recommendations': recommendations,
            'follow_up_needed': follow_up
        }
    
    def _calculate_ghq12_score(self, responses: list) -> dict:
        """Calculate GHQ-12 general health screening score."""
        # GHQ-12 scoring: 0-0-1-1 for each question
        binary_responses = [1 if r >= 2 else 0 for r in responses[:12]]
        total_score = sum(binary_responses)
        max_score = 12
        
        if total_score <= 3:
            severity = 'minimal'
            recommendations = 'Good general mental health. Maintain current habits.'
            follow_up = False
        elif total_score <= 6:
            severity = 'mild'
            recommendations = 'Some areas of concern. Consider wellness strategies.'
            follow_up = True
        elif total_score <= 9:
            severity = 'moderate'
            recommendations = 'Multiple areas of concern. Professional consultation recommended.'
            follow_up = True
        else:
            severity = 'severe'
            recommendations = 'Significant concerns across multiple areas. Professional help recommended.'
            follow_up = True
        
        return {
            'total_score': total_score,
            'max_score': max_score,
            'severity': severity,
            'recommendations': recommendations,
            'follow_up_needed': follow_up
        }


class ConversationHistoryAPIView(APIView):
    """Get conversation history for a user."""
    
    def get(self, request):
        uid = request.query_params.get('uid')
        if not uid:
            return Response({'error': 'uid parameter required'}, status=400)
        
        user_profile = UserProfile.objects.filter(uid=uid).first()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=404)
        
        conversations = Conversation.objects.filter(
            user_profile=user_profile
        ).order_by('-created_at')[:20]
        
        serializer = ConversationSerializer(conversations, many=True)
        return Response({'conversations': serializer.data})


class ScreeningHistoryAPIView(APIView):
    """Get screening history for a user."""
    
    def get(self, request):
        uid = request.query_params.get('uid')
        if not uid:
            return Response({'error': 'uid parameter required'}, status=400)
        
        user_profile = UserProfile.objects.filter(uid=uid).first()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=404)
        
        screenings = ScreeningResult.objects.filter(
            user_profile=user_profile
        ).order_by('-created_at')[:10]
        
        serializer = ScreeningResultSerializer(screenings, many=True)
        return Response({'screenings': serializer.data})


class UserMemoryAPIView(APIView):
    """User memory management."""
    
    def get(self, request):
        uid = request.query_params.get('uid')
        if not uid:
            return Response({'error': 'uid parameter required'}, status=400)
        
        user_profile = UserProfile.objects.filter(uid=uid).first()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=404)
        
        memories = UserMemory.objects.filter(
            user_profile=user_profile
        ).order_by('-updated_at')
        
        serializer = UserMemorySerializer(memories, many=True)
        return Response({'memories': serializer.data})


class SendOTPAPIView(APIView):
    """Send OTP via email for magic link authentication."""
    
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=400)
            
            # Generate OTP (6-digit code)
            import random
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store OTP in session or cache (simplified for demo)
            request.session[f'otp_{email}'] = otp
            
            # Send email
            send_mail(
                'Your Saathi Login Code',
                f'Your login code is: {otp}\n\nThis code will expire in 10 minutes.',
                None,  # Use DEFAULT_FROM_EMAIL
                [email],
                fail_silently=False,
            )
            
            return Response({
                'success': True,
                'message': 'OTP sent successfully'
            })
            
        except Exception as e:
            logger.error(f"Send OTP error: {e}")
            return Response({
                'success': False,
                'error': 'Failed to send OTP'
            }, status=500)


class VerifyOTPAPIView(APIView):
    """Verify OTP for authentication."""
    
    def post(self, request):
        try:
            email = request.data.get('email')
            otp = request.data.get('otp')
            
            if not email or not otp:
                return Response({'error': 'Email and OTP are required'}, status=400)
            
            # Check OTP from session
            stored_otp = request.session.get(f'otp_{email}')
            
            if not stored_otp or stored_otp != otp:
                return Response({
                    'success': False,
                    'error': 'Invalid OTP'
                }, status=400)
            
            # Clear OTP from session
            del request.session[f'otp_{email}']
            
            # Create or get user profile
            user_profile, created = UserProfile.objects.get_or_create(
                email=email,
                defaults={'uid': f'email_{hash(email)}'}
            )
            
            return Response({
                'success': True,
                'uid': user_profile.uid,
                'created': created
            })
            
        except Exception as e:
            logger.error(f"Verify OTP error: {e}")
            return Response({
                'success': False,
                'error': 'OTP verification failed'
            }, status=500)


class HealthCheckAPIView(APIView):
    """Health check endpoint."""
    
    def get(self, request):
        try:
            # Check database
            UserProfile.objects.count()
            
            # Check AI services
            ai_pipeline = get_ai_pipeline()
            rag_service = get_rag_service()
            transcription_service = get_transcription_service()
            
            return Response({
                'status': 'healthy',
                'services': {
                    'database': 'ok',
                    'ai_pipeline': 'ok' if ai_pipeline else 'error',
                    'rag_service': 'ok' if rag_service.initialized else 'fallback',
                    'transcription': 'ok' if transcription_service else 'error'
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e)
            }, status=500)