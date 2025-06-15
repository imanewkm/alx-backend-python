"""
Models for the messaging app - Task 0: User Notifications

This module contains:
- Message model with sender, receiver, content, and timestamp fields
- Notification model to store notifications linked to User and Message models
- Custom manager for unread messages
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid


# Get the User model from settings
User = get_user_model()


# Custom Manager for Unread Messages
class UnreadMessagesManager(models.Manager):
    """Custom manager to filter unread messages for a user."""
    
    def unread_for_user(self, user):
        """Get unread messages for a specific user."""
        user_conversations = user.messaging_conversations.all()
        return self.get_queryset().filter(
            conversation__in=user_conversations,
            read=False
        ).exclude(sender=user).select_related('sender', 'conversation')
    
    def mark_as_read(self, user, conversation=None):
        """Mark messages as read for a user, optionally in a specific conversation."""
        queryset = self.unread_for_user(user)
        if conversation:
            queryset = queryset.filter(conversation=conversation)
        return queryset.update(read=True)


class Conversation(models.Model):
    """Model to track conversations between users."""
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='messaging_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        participant_names = ", ".join([str(user) for user in self.participants.all()[:2]])
        participant_count = self.participants.count()
        if participant_count > 2:
            participant_names += f" and {participant_count - 2} others"
        return f"Conversation: {participant_names}"


class Message(models.Model):
    """
    Message model with sender, receiver, content, and timestamp fields.
    
    This model represents individual messages within conversations.
    - For direct messages: both sender and receiver are specified
    - For group messages: only sender is specified, receiver is None
    """
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Sender field - required for all messages
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='messaging_sent_messages',
        help_text="User who sent the message"
    )
    
    # Receiver field - for direct messages (as specified in requirements)
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messaging_received_messages',
        null=True,
        blank=True,
        help_text="Direct message receiver (for 1-on-1 messages)"
    )
    
    # Content field (as specified in requirements)
    content = models.TextField(help_text="Message content")
    
    # Timestamp field (as specified in requirements)
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Message timestamp")
    
    # Additional fields for enhanced functionality
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    edited = models.BooleanField(default=False)
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='edited_messages',
        help_text="User who last edited this message"
    )
    read = models.BooleanField(default=False)
    parent_message = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    
    # Custom managers
    objects = models.Manager()  # Default manager
    unread = UnreadMessagesManager()  # Custom manager for unread messages
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}: {self.content[:50]}..."
    
    def get_receivers(self):
        """
        Get all users who should receive notifications for this message.
        
        Returns:
            QuerySet or list: Users who should be notified
        """
        if self.receiver:
            # Direct message - single receiver
            return [self.receiver]
        else:
            # Group conversation - all participants except sender
            return self.conversation.participants.exclude(user_id=self.sender.user_id)
    
    def get_edit_history(self):
        """
        Get the edit history for this message, ordered by most recent first.
        
        Returns:
            QuerySet: MessageHistory objects for this message
        """
        return self.history.all().order_by('-edited_at')
    
    def get_edit_count(self):
        """
        Get the number of times this message has been edited.
        
        Returns:
            int: Number of edit history entries
        """
        return self.history.count()
    
    def get_original_content(self):
        """
        Get the original content of the message (before any edits).
        
        Returns:
            str: Original message content, or current content if never edited
        """
        if not self.edited:
            return self.content
        
        # Get the oldest history entry (original content)
        oldest_history = self.history.order_by('edited_at').first()
        return oldest_history.old_content if oldest_history else self.content
    
    def get_edit_summary(self):
        """
        Get a summary of message edits for display purposes.
        
        Returns:
            dict: Summary information about message edits
        """
        history = self.get_edit_history()
        return {
            'is_edited': self.edited,
            'edit_count': history.count(),
            'last_edited': history.first().edited_at if history.exists() else None,
            'original_content': self.get_original_content(),
            'current_content': self.content,
            'edit_history': [
                {
                    'old_content': h.old_content,
                    'edited_at': h.edited_at,
                    'history_id': h.history_id
                }
                for h in history
            ]
        }


class Notification(models.Model):
    """
    Notification model to store notifications, linking to User and Message models.
    
    This model automatically stores notifications when users receive new messages.
    """
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to User model (as specified in requirements)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='messaging_notifications',
        help_text="User who will receive this notification"
    )
    
    # Link to Message model (as specified in requirements)
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        help_text="Message that triggered this notification"
    )
    
    # Notification type for different kinds of notifications
    notification_type = models.CharField(
        max_length=20, 
        choices=[
            ('new_message', 'New Message'),
            ('message_edit', 'Message Edited'),
            ('mention', 'Mentioned'),
        ],
        default='new_message',
        help_text="Type of notification"
    )
    
    # Read status
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    
    # Timestamp for when notification was created
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the notification was created"
    )
    
    class Meta:
        ordering = ['-created_at']
        # Ensure no duplicate notifications for same user-message combination
        unique_together = ['user', 'message', 'notification_type']
    
    def __str__(self):
        return f"Notification for {self.user} - {self.notification_type}"


class MessageHistory(models.Model):
    """Model to track message edit history."""
    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='history'
    )
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-edited_at']
        verbose_name = "Message Edit History"
        verbose_name_plural = "Message Edit Histories"
    
    def __str__(self):
        return f"History for message {self.message.message_id} at {self.edited_at}"
    
    def get_content_preview(self, max_length=50):
        """
        Get a preview of the old content for display purposes.
        
        Args:
            max_length (int): Maximum length of preview text
            
        Returns:
            str: Truncated content with ellipsis if needed
        """
        if len(self.old_content) <= max_length:
            return self.old_content
        return self.old_content[:max_length] + "..."
    
    def get_content_diff_length(self):
        """
        Calculate the difference in content length between old and current content.
        
        Returns:
            int: Difference in character count (positive = content grew, negative = content shrank)
        """
        current_content = self.message.content
        return len(current_content) - len(self.old_content)
    
    @classmethod
    def get_recent_edits(cls, days=7):
        """
        Get recent message edits within the specified number of days.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            QuerySet: Recent MessageHistory objects
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(edited_at__gte=cutoff_date)
    
    @classmethod
    def get_most_edited_messages(cls, limit=10):
        """
        Get messages that have been edited the most.
        
        Args:
            limit (int): Maximum number of messages to return
            
        Returns:
            QuerySet: Messages ordered by edit count (descending)
        """
        from django.db.models import Count
        
        return Message.objects.annotate(
            edit_count=Count('history')
        ).filter(edit_count__gt=0).order_by('-edit_count')[:limit]
