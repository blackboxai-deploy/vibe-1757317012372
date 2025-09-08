"""
URL configuration for Saathi API endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Main conversation endpoint
    path('chat/', views.ChatAPIView.as_view(), name='chat'),
    
    # Audio transcription
    path('transcribe/', views.TranscribeAPIView.as_view(), name='transcribe'),
    
    # Document ingestion for RAG
    path('ingest-file/', views.IngestFileAPIView.as_view(), name='ingest_file'),
    
    # User profile management
    path('profile/', views.UserProfileAPIView.as_view(), name='user_profile'),
    path('profile/memory/', views.UserMemoryAPIView.as_view(), name='user_memory'),
    
    # Mental health screening
    path('screening/', views.ScreeningAPIView.as_view(), name='screening'),
    path('screening/history/', views.ScreeningHistoryAPIView.as_view(), name='screening_history'),
    
    # Conversation history
    path('conversations/', views.ConversationHistoryAPIView.as_view(), name='conversations'),
    
    # Optional authentication endpoints (magic link OTP)
    path('auth/send-otp/', views.SendOTPAPIView.as_view(), name='send_otp'),
    path('auth/verify-otp/', views.VerifyOTPAPIView.as_view(), name='verify_otp'),
    
    # Health check
    path('health/', views.HealthCheckAPIView.as_view(), name='health_check'),
]