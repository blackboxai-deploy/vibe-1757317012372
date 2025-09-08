"""
Serializers for Saathi API models.
"""

from rest_framework import serializers
from .models import UserProfile, Conversation, ScreeningResult, UserMemory, UploadedDocument, CrisisEvent


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""
    
    class Meta:
        model = UserProfile
        fields = [
            'uid', 'email', 'display_name', 
            'consent_data_storage', 'consent_screening_storage',
            'theme_preference', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversations."""
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'session_id', 'user_message', 'ai_response',
            'crisis_detected', 'escalation_triggered', 'response_time_ms',
            'context_data', 'memory_updates', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ScreeningResultSerializer(serializers.ModelSerializer):
    """Serializer for screening results."""
    
    class Meta:
        model = ScreeningResult
        fields = [
            'id', 'screening_type', 'total_score', 'max_possible_score',
            'severity_level', 'responses', 'recommendations', 
            'follow_up_needed', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserMemorySerializer(serializers.ModelSerializer):
    """Serializer for user memories."""
    
    class Meta:
        model = UserMemory
        fields = [
            'id', 'memory_type', 'key', 'value', 'confidence',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UploadedDocumentSerializer(serializers.ModelSerializer):
    """Serializer for uploaded documents."""
    
    class Meta:
        model = UploadedDocument
        fields = [
            'id', 'filename', 'file_url', 'file_size', 'mime_type',
            'processing_status', 'chunk_count', 'error_message',
            'created_at', 'processed_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']


class CrisisEventSerializer(serializers.ModelSerializer):
    """Serializer for crisis events."""
    
    class Meta:
        model = CrisisEvent
        fields = [
            'id', 'crisis_type', 'severity_score', 
            'emergency_resources_provided', 'follow_up_scheduled',
            'human_notified', 'trigger_keywords', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']