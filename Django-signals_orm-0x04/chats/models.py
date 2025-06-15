from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid


# Custom Manager for Unread Messages
class UnreadMessagesManager(models.Manager):
    """Custom manager to filter unread messages for a user."""
    
    def for_user(self, user):
        """Get unread messages for a specific user."""
        user_conversations = user.conversations.all()
        return self.get_queryset().filter(
            conversation__in=user_conversations,
            read=False
        ).exclude(sender=user).select_related('sender', 'conversation')
    
    def mark_as_read(self, user, conversation=None):
        """Mark messages as read for a user, optionally in a specific conversation."""
        queryset = self.for_user(user)
        if conversation:
            queryset = queryset.filter(conversation=conversation)
        return queryset.update(read=True)


class User(AbstractUser):
    """Extended User model with additional fields for messaging functionality."""
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    password = models.CharField(max_length=128)  # Explicitly define password field
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Conversation(models.Model):
    """Model to track conversations between users."""
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
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
    """Model for individual messages within conversations."""
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        null=True,
        blank=True,
        help_text="Direct message receiver (for 1-on-1 messages)"
    )
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    message_body = models.TextField(help_text="Message content")
    sent_at = models.DateTimeField(auto_now_add=True, help_text="Message timestamp")
    edited = models.BooleanField(default=False)
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
        ordering = ['sent_at']
    
    def __str__(self):
        return f"Message from {self.sender} at {self.sent_at}: {self.message_body[:50]}..."
    
    def get_receivers(self):
        """Get all users who should receive notifications for this message."""
        if self.receiver:
            # Direct message - single receiver
            return [self.receiver]
        else:
            # Group conversation - all participants except sender
            return self.conversation.participants.exclude(user_id=self.sender.user_id)


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
    
    def __str__(self):
        return f"History for message {self.message.message_id} at {self.edited_at}"


class Notification(models.Model):
    """Model for user notifications."""
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=[
            ('new_message', 'New Message'),
            ('message_edit', 'Message Edited'),
            ('mention', 'Mentioned'),
        ],
        default='new_message'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user} - {self.notification_type}"
