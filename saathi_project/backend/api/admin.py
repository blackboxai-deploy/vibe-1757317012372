"""
Django admin configuration for Saathi models.
"""

from django.contrib import admin
from .models import UserProfile, Conversation, ScreeningResult, UserMemory, UploadedDocument, CrisisEvent


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['uid', 'email', 'display_name', 'consent_data_storage', 'created_at']
    list_filter = ['consent_data_storage', 'consent_screening_storage', 'theme_preference', 'created_at']
    search_fields = ['uid', 'email', 'display_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('uid', 'email', 'display_name')
        }),
        ('Privacy & Preferences', {
            'fields': ('consent_data_storage', 'consent_screening_storage', 'theme_preference')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_profile', 'crisis_detected', 'response_time_ms', 'created_at']
    list_filter = ['crisis_detected', 'escalation_triggered', 'created_at']
    search_fields = ['user_profile__uid', 'user_message', 'ai_response']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user_profile', 'session_id')
        }),
        ('Conversation', {
            'fields': ('user_message', 'ai_response')
        }),
        ('Metadata', {
            'fields': ('crisis_detected', 'escalation_triggered', 'response_time_ms')
        }),
        ('Data', {
            'fields': ('context_data', 'memory_updates'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )


@admin.register(ScreeningResult)
class ScreeningResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_profile', 'screening_type', 'total_score', 'severity_level', 'follow_up_needed', 'created_at']
    list_filter = ['screening_type', 'severity_level', 'follow_up_needed', 'created_at']
    search_fields = ['user_profile__uid']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user_profile', 'screening_type')
        }),
        ('Results', {
            'fields': ('total_score', 'max_possible_score', 'severity_level')
        }),
        ('Assessment', {
            'fields': ('responses', 'recommendations', 'follow_up_needed')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )


@admin.register(UserMemory)
class UserMemoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_profile', 'memory_type', 'key', 'confidence', 'updated_at']
    list_filter = ['memory_type', 'created_at', 'updated_at']
    search_fields = ['user_profile__uid', 'key', 'value']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('user_profile', 'memory_type', 'key', 'value', 'confidence')
        }),
        ('Source', {
            'fields': ('source_conversation',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_profile', 'filename', 'processing_status', 'chunk_count', 'created_at']
    list_filter = ['processing_status', 'mime_type', 'created_at']
    search_fields = ['user_profile__uid', 'filename']
    readonly_fields = ['created_at', 'processed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user_profile', 'filename', 'file_url')
        }),
        ('File Info', {
            'fields': ('file_size', 'mime_type')
        }),
        ('Processing', {
            'fields': ('processing_status', 'chunk_count', 'error_message')
        }),
        ('Content', {
            'fields': ('extracted_text',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        })
    )


@admin.register(CrisisEvent)
class CrisisEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_profile', 'crisis_type', 'severity_score', 'emergency_resources_provided', 'created_at']
    list_filter = ['crisis_type', 'emergency_resources_provided', 'follow_up_scheduled', 'human_notified', 'created_at']
    search_fields = ['user_profile__uid']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user_profile', 'conversation')
        }),
        ('Crisis Details', {
            'fields': ('crisis_type', 'severity_score', 'trigger_keywords')
        }),
        ('Response Actions', {
            'fields': ('emergency_resources_provided', 'follow_up_scheduled', 'human_notified')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    # Custom actions
    def mark_human_notified(self, request, queryset):
        updated = queryset.update(human_notified=True)
        self.message_user(request, f'{updated} crisis events marked as human notified.')
    mark_human_notified.short_description = "Mark selected events as human notified"
    
    actions = [mark_human_notified]


# Customize admin site header
admin.site.site_header = "Saathi Admin"
admin.site.site_title = "Saathi Admin Portal"
admin.site.index_title = "Welcome to Saathi Administration"