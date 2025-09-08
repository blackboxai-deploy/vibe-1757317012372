"""
Database models for Saathi API.
Stores user conversations, screening results, and memory updates.
"""

from django.db import models
from django.contrib.auth.models import User
import json


class UserProfile(models.Model):
    """Extended user profile with privacy preferences."""
    uid = models.CharField(max_length=128, unique=True, help_text="Firebase UID")
    email = models.EmailField(blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Privacy settings
    consent_data_storage = models.BooleanField(default=False)
    consent_screening_storage = models.BooleanField(default=False)
    
    # Theme preference
    theme_preference = models.CharField(
        max_length=10, 
        choices=[('light', 'Light'), ('dark', 'Dark')], 
        default='light'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"User {self.uid} ({self.email or 'No email'})"


class Conversation(models.Model):
    """Chat conversation records."""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=128, db_index=True)
    
    # Message content
    user_message = models.TextField()
    ai_response = models.TextField()
    
    # Metadata
    crisis_detected = models.BooleanField(default=False)
    escalation_triggered = models.BooleanField(default=False)
    response_time_ms = models.IntegerField(default=0)
    
    # Context data (JSON)
    context_data = models.JSONField(default=dict, blank=True)
    memory_updates = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {self.user_profile.uid}"


class ScreeningResult(models.Model):
    """Mental health screening assessment results."""
    
    SCREENING_TYPES = [
        ('PHQ9', 'Patient Health Questionnaire-9'),
        ('GAD7', 'Generalized Anxiety Disorder-7'),
        ('GHQ12', 'General Health Questionnaire-12'),
    ]
    
    SEVERITY_LEVELS = [
        ('minimal', 'Minimal'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('moderately_severe', 'Moderately Severe'),
        ('severe', 'Severe'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    screening_type = models.CharField(max_length=10, choices=SCREENING_TYPES)
    
    # Scores and results
    total_score = models.IntegerField()
    max_possible_score = models.IntegerField()
    severity_level = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    
    # Individual responses (JSON array)
    responses = models.JSONField(help_text="Array of individual question responses")
    
    # Recommendations
    recommendations = models.TextField(blank=True)
    follow_up_needed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.screening_type} - {self.user_profile.uid} - {self.severity_level}"


class UserMemory(models.Model):
    """Persistent memory storage for personalized conversations."""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    # Memory categories
    MEMORY_TYPES = [
        ('preference', 'User Preference'),
        ('interest', 'Interest/Hobby'),
        ('goal', 'Goal/Aspiration'),
        ('challenge', 'Challenge/Struggle'),
        ('relationship', 'Relationship'),
        ('academic', 'Academic Info'),
        ('health', 'Health Info'),
        ('coping', 'Coping Strategy'),
    ]
    
    memory_type = models.CharField(max_length=20, choices=MEMORY_TYPES)
    key = models.CharField(max_length=100, help_text="Memory key (e.g., 'favorite_music')")
    value = models.TextField(help_text="Memory value")
    confidence = models.FloatField(default=1.0, help_text="Confidence score 0-1")
    
    # Metadata
    source_conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user_profile', 'memory_type', 'key']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user_profile.uid} - {self.memory_type}: {self.key}"


class UploadedDocument(models.Model):
    """Documents uploaded by users for RAG indexing."""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    # File information
    filename = models.CharField(max_length=255)
    file_url = models.URLField(help_text="Firebase Storage URL")
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Processing status
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    processing_status = models.CharField(
        max_length=15, 
        choices=PROCESSING_STATUS, 
        default='pending'
    )
    
    # Extracted content
    extracted_text = models.TextField(blank=True)
    chunk_count = models.IntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.user_profile.uid} ({self.processing_status})"


class CrisisEvent(models.Model):
    """Log of crisis detection events for safety monitoring."""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    
    # Crisis details
    CRISIS_TYPES = [
        ('suicidal_ideation', 'Suicidal Ideation'),
        ('self_harm', 'Self Harm'),
        ('severe_depression', 'Severe Depression'),
        ('severe_anxiety', 'Severe Anxiety'),
        ('psychosis', 'Psychosis'),
        ('substance_abuse', 'Substance Abuse'),
    ]
    
    crisis_type = models.CharField(max_length=20, choices=CRISIS_TYPES)
    severity_score = models.FloatField(help_text="Crisis severity 0-1")
    
    # Response actions taken
    emergency_resources_provided = models.BooleanField(default=True)
    follow_up_scheduled = models.BooleanField(default=False)
    human_notified = models.BooleanField(default=False)
    
    # Trigger content (store safely)
    trigger_keywords = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Crisis: {self.crisis_type} - {self.user_profile.uid}"