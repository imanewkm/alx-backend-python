from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from .managers import UnreadMessagesManager

User = get_user_model()

class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name="Sender"
        )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name="Receiver"
        )
    parent_message = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='message_thread'
        )
    content = models.TextField(verbose_name="Message Content")
    timestamp = models.DateTimeField( # field name set in task details same as created_at
        auto_now_add=True, verbose_name="Created At"
        ) 
    edited = models.BooleanField(default=False, verbose_name="Edited")

    edited_at = models.DateTimeField(auto_now=True, verbose_name="Last Edited At")

    unread = models.BooleanField(default=True, verbose_name="Unead")

    objects = models.Manager() # The default manager
    unread_messages = UnreadMessagesManager() # Custom manager

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        content_display = self.content[:75]
        if len(self.content) > 75:
            content_display+='...'
        return f"Msg from {self.sender.username} to {self.receiver.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}: \"{content_display}\""


class Notification(models.Model):
    detail = models.TextField(verbose_name="Notification Detail")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
         verbose_name="User"
         )
    message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL, # Set to null if related message is deleted
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Related Message'
        )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"Notification for {self.user.username} ({status}): {self.detail[:50]}..."


class MessageHistory(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="history_entries",
        verbose_name="Original Message"
        )
    edited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='editor',
        verbose_name="Edited By"
    )
    old_content = models.TextField(verbose_name="Old Content")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Saved At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message History"
        verbose_name_plural = "Message History"

    def __str__(self):
        return f"History for Msg ID {self.message_id} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
