"""
Django signals for the messaging app.

This module contains signal handlers for:
1. User notification when new messages are received
2. Logging message edits with history tracking
3. Cleaning up user-related data on account deletion
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Message, Notification, MessageHistory, Conversation

User = get_user_model()


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a new message is created.
    
    This signal is triggered after a Message instance is saved.
    For direct messages: creates notification for the receiver
    For group conversations: creates notifications for all participants except sender
    """
    if created:
        # Get recipients using the message's get_receivers method
        recipients = instance.get_receivers()
        
        # Create notifications for each recipient
        notifications_to_create = []
        for recipient in recipients:
            notifications_to_create.append(
                Notification(
                    user=recipient,
                    message=instance,
                    notification_type='new_message'
                )
            )
        
        # Bulk create notifications for efficiency
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
            
            # Log notification creation for debugging
            print(f"Created {len(notifications_to_create)} notifications for message {instance.message_id}")


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal handler to log message edits before the message is updated.
    
    This signal is triggered before a Message instance is saved.
    If the message already exists and the content has changed,
    it saves the old content to MessageHistory.
    """
    if instance.pk:  # Only for existing messages (updates)
        try:
            # Get the original message from the database
            original_message = Message.objects.get(pk=instance.pk)
            
            # Check if the message body has changed
            if original_message.message_body != instance.message_body:
                # Create a history record with the old content
                MessageHistory.objects.create(
                    message=original_message,
                    old_content=original_message.message_body
                )
                
                # Mark the message as edited
                instance.edited = True
                
                # Create a notification for message edit
                participants = instance.conversation.participants.exclude(
                    user_id=instance.sender.user_id
                )
                
                notifications_to_create = []
                for participant in participants:
                    notifications_to_create.append(
                        Notification(
                            user=participant,
                            message=instance,
                            notification_type='message_edit'
                        )
                    )
                
                if notifications_to_create:
                    Notification.objects.bulk_create(notifications_to_create)
                    
        except Message.DoesNotExist:
            # This is a new message, not an edit
            pass


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal handler to clean up user-related data when a user is deleted.
    
    This signal is triggered after a User instance is deleted.
    It handles the cleanup of:
    1. Messages sent by the user
    2. Notifications for the user
    3. Message histories related to user's messages
    4. Conversations where the user was the only participant
    
    Note: Messages and conversations are handled by CASCADE foreign keys,
    but this provides additional cleanup and logging if needed.
    """
    # Log the deletion for audit purposes
    print(f"Cleaning up data for deleted user: {instance.email}")
    
    # Notifications are automatically deleted via CASCADE
    # Messages are automatically deleted via CASCADE
    # MessageHistory is automatically deleted via CASCADE (related to messages)
    
    # Clean up empty conversations (conversations with no participants)
    # This might happen if this was the last participant
    empty_conversations = Conversation.objects.filter(participants__isnull=True)
    deleted_conversations_count = empty_conversations.count()
    empty_conversations.delete()
    
    if deleted_conversations_count > 0:
        print(f"Deleted {deleted_conversations_count} empty conversations")


@receiver(post_save, sender=User)
def user_created_notification(sender, instance, created, **kwargs):
    """
    Signal handler for when a new user is created.
    This can be used for welcome notifications or setup tasks.
    """
    if created:
        print(f"New user created: {instance.email}")
        # Here you could create a welcome notification or perform initial setup


# Signal to update conversation timestamp when a message is sent
@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """
    Signal handler to update conversation's updated_at timestamp
    when a new message is created.
    """
    if created:
        # Update the conversation's updated_at field
        # This is automatically handled by auto_now=True, but we can
        # add additional logic here if needed
        conversation = instance.conversation
        conversation.save(update_fields=['updated_at'])
