"""
Django admin configuration for the messaging app - Task 0: User Notifications

This module provides admin interface for managing messages and notifications.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Conversation, Message, Notification, MessageHistory

User = get_user_model()


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin configuration for Conversation model."""
    list_display = ('conversation_id', 'get_participants', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__email', 'participants__username')
    readonly_fields = ('conversation_id', 'created_at', 'updated_at')
    filter_horizontal = ('participants',)
    
    def get_participants(self, obj):
        return ", ".join([str(user) for user in obj.participants.all()[:3]])
    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for Message model.
    
    Displays message details including sender, receiver, content, and timestamp
    as specified in the requirements. Enhanced with edit history information.
    """
    list_display = (
        'message_id', 
        'sender', 
        'receiver', 
        'content_preview', 
        'timestamp', 
        'edited', 
        'edit_count_display',
        'read'
    )
    list_filter = ('timestamp', 'edited', 'read')
    search_fields = (
        'sender__email', 
        'sender__username', 
        'receiver__email', 
        'receiver__username', 
        'content'
    )
    readonly_fields = ('message_id', 'timestamp', 'edit_history_display')
    
    fieldsets = (
        ('Message Information', {
            'fields': ('message_id', 'sender', 'receiver', 'conversation', 'content')
        }),
        ('Status', {
            'fields': ('edited', 'read', 'timestamp')
        }),
        ('Edit History', {
            'fields': ('edit_history_display',),
            'classes': ('collapse',),
        }),
    )
    
    def content_preview(self, obj):
        """Show a preview of the message content."""
        preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        if obj.edited:
            preview = f"✏️ {preview}"
        return preview
    content_preview.short_description = 'Content Preview'
    
    def edit_count_display(self, obj):
        """Display the number of edits for this message."""
        count = obj.get_edit_count()
        if count > 0:
            return f"{count} edits"
        return "No edits"
    edit_count_display.short_description = 'Edit Count'
    
    def edit_history_display(self, obj):
        """Display detailed edit history in admin."""
        if not obj.edited:
            return "This message has never been edited."
        
        history = obj.get_edit_history()
        if not history.exists():
            return "No edit history available."
        
        html_parts = ['<div style="max-height: 300px; overflow-y: auto;">']
        html_parts.append('<table style="width: 100%; border-collapse: collapse;">')
        html_parts.append('<tr style="background: #f0f0f0;"><th>Version</th><th>Content</th><th>Edited At</th></tr>')
        
        # Current version
        html_parts.append(f'''
            <tr style="background: #e8f5e8;">
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Current</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{obj.content[:100]}{"..." if len(obj.content) > 100 else ""}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{obj.timestamp}</td>
            </tr>
        ''')
        
        # Previous versions
        for i, hist in enumerate(history):
            version_num = len(history) - i
            bg_color = "#fff3cd" if i == 0 else "#f8f9fa"
            html_parts.append(f'''
                <tr style="background: {bg_color};">
                    <td style="padding: 8px; border: 1px solid #ddd;">Version {version_num}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{hist.old_content[:100]}{"..." if len(hist.old_content) > 100 else ""}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{hist.edited_at}</td>
                </tr>
            ''')
        
        html_parts.append('</table></div>')
        
        from django.utils.safestring import mark_safe
        return mark_safe(''.join(html_parts))
    
    edit_history_display.short_description = 'Edit History'
    
    def get_queryset(self, request):
        """Optimize queries by selecting related objects."""
        return super().get_queryset(request).select_related('sender', 'receiver', 'conversation').prefetch_related('history')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Notification model.
    
    Shows notifications linking User and Message models as specified in requirements.
    """
    list_display = (
        'notification_id', 
        'user', 
        'message_preview', 
        'notification_type', 
        'is_read', 
        'created_at'
    )
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = (
        'user__email', 
        'user__username', 
        'message__content'
    )
    readonly_fields = ('notification_id', 'created_at')
    
    def message_preview(self, obj):
        """Show a preview of the related message."""
        return f"From {obj.message.sender}: {obj.message.content[:30]}..."
    message_preview.short_description = 'Message'
    
    def get_queryset(self, request):
        """Optimize queries by selecting related objects."""
        return super().get_queryset(request).select_related(
            'user', 
            'message', 
            'message__sender', 
            'message__receiver'
        )
    
    # Add actions for bulk operations
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    """
    Enhanced admin configuration for MessageHistory model.
    Provides detailed view of message edit history with comparison features.
    """
    list_display = (
        'history_id', 
        'message_preview', 
        'sender_info',
        'old_content_preview', 
        'content_length_change',
        'edited_at'
    )
    list_filter = ('edited_at', 'message__sender', 'message__conversation')
    search_fields = ('message__content', 'old_content', 'message__sender__email')
    readonly_fields = ('history_id', 'edited_at', 'content_comparison')
    
    fieldsets = (
        ('History Information', {
            'fields': ('history_id', 'message', 'edited_at')
        }),
        ('Content', {
            'fields': ('old_content',)
        }),
        ('Comparison', {
            'fields': ('content_comparison',),
            'classes': ('collapse',),
        }),
    )
    
    def message_preview(self, obj):
        """Show a preview of the related message."""
        current_content = obj.message.content[:30] + "..." if len(obj.message.content) > 30 else obj.message.content
        return f"Message: {current_content}"
    message_preview.short_description = 'Message'
    
    def sender_info(self, obj):
        """Display sender information."""
        return f"{obj.message.sender.first_name} {obj.message.sender.last_name}"
    sender_info.short_description = 'Sender'
    
    def old_content_preview(self, obj):
        """Enhanced preview of old content."""
        preview = obj.get_content_preview(50)
        return f"📄 {preview}"
    old_content_preview.short_description = 'Old Content'
    
    def content_length_change(self, obj):
        """Show the change in content length."""
        diff = obj.get_content_diff_length()
        if diff > 0:
            return f"📈 +{diff} chars"
        elif diff < 0:
            return f"📉 {diff} chars"
        else:
            return "➖ No change"
    content_length_change.short_description = 'Length Change'
    
    def content_comparison(self, obj):
        """Display a side-by-side comparison of old and new content."""
        old_content = obj.old_content
        new_content = obj.message.content
        
        html = '''
        <div style="display: flex; gap: 20px; max-height: 400px; overflow-y: auto;">
            <div style="flex: 1; background: #fff3cd; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">📄 Old Content</h4>
                <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9em;">%s</div>
                <p style="margin: 10px 0 0 0; font-size: 0.8em; color: #856404;">
                    Length: %d characters
                </p>
            </div>
            <div style="flex: 1; background: #d1ecf1; padding: 15px; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0; color: #0c5460;">📝 Current Content</h4>
                <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9em;">%s</div>
                <p style="margin: 10px 0 0 0; font-size: 0.8em; color: #0c5460;">
                    Length: %d characters
                </p>
            </div>
        </div>
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <strong>Summary:</strong>
            <ul style="margin: 5px 0;">
                <li>Content length change: %s</li>
                <li>Edited at: %s</li>
                <li>Message ID: %s</li>
            </ul>
        </div>
        ''' % (
            old_content,
            len(old_content),
            new_content,
            len(new_content),
            f"+{obj.get_content_diff_length()}" if obj.get_content_diff_length() >= 0 else str(obj.get_content_diff_length()),
            obj.edited_at,
            obj.message.message_id
        )
        
        from django.utils.safestring import mark_safe
        return mark_safe(html)
    
    content_comparison.short_description = 'Content Comparison'
    
    def get_queryset(self, request):
        """Optimize queries."""
        return super().get_queryset(request).select_related('message', 'message__sender', 'message__receiver')
    
    # Add custom admin actions
    actions = ['export_edit_history']
    
    def export_edit_history(self, request, queryset):
        """Export selected edit history entries."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="message_edit_history.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['History ID', 'Message ID', 'Sender', 'Old Content', 'Current Content', 'Edited At'])
        
        for history in queryset.select_related('message', 'message__sender'):
            writer.writerow([
                str(history.history_id),
                str(history.message.message_id),
                f"{history.message.sender.first_name} {history.message.sender.last_name}",
                history.old_content,
                history.message.content,
                history.edited_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    export_edit_history.short_description = "Export selected edit history to CSV"


# Customize admin site headers
admin.site.site_header = "Messaging System Administration"
admin.site.site_title = "Messaging Admin"
admin.site.index_title = "Welcome to Messaging System Administration"
