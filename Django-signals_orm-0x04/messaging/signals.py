import logging
from django.db.models.signals import post_save, pre_save, post_delete
from .models import Message, Notification, MessageHistory
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def message_post_save_receiver(sender, instance, created, **kwargs):
    """
    Triggers a notification when a new Message instance is created.
    listens for new messages and automatically creates a notification for the receiving user.
    """
    if created:
        try:
            Notification.objects.create(
                detail=f"You have a new message from {instance.sender.username}!",
                user=instance.receiver,
                message=instance
                )
            logger.info(
                f"Notification created for {instance.receiver.username} "
                f"due to new message from {instance.sender.username} (ID: {instance.id})"
            )

        except Exception as e:
            logger.error(f"Error creating notification for message ID: {instance.id}: {e}")


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal for logging message edits before message is saved
    Captures old content if message is being updated
    """
    if instance.pk: # Check if instance exists already, won't run if message is being created
        try:
            old_message = sender.objects.get(pk=instance.pk)

            # Check if content has actually changed
            if old_message.content != instance.content:
                with transaction.atomic():
                    MessageHistory.objects.create(
                        message=old_message,
                        edited_by=old_message.sender,
                        old_content=old_message.content
                    )
                    instance.edited = True
                    logger.info(
                        f"Message ID: '{instance.id}' content changed"
                        f"Old content logged to history. New content {instance.content[:50]}..."
                        )
                    
            else:
                logger.info(f"Message ID: '{instance.id}' saved, but content did not change. No history logged  ")
        
        except sender.DoesNotExist:
            logger.warning(f"Message with ID '{instance.pk}' not found for history logging during pre_save. Was it deleted?")
        except Exception as e:
            logger.error(f"Error logging edit details for message ID: {instance.id}: {e}")

    else:
        logger.info(f"New message (ID will be {instance.pk if instance.pk else 'unkown'}) being created. No history logged yet.")


@receiver(post_delete, sender=User)
def deleted_user_signal(sender, instance, **kwargs):
    """
    Automatically clean up related data when a user deletes their account
    """
    
    user_messages = Message.objects.filter(sender=instance) # This id redundant because message deletion is handled by on_delete=models.CASCADE
    user_messages.delete()
    logger.warning("User '{instance.username}' with ID {instance.id} and related data has been deleted suceesfully")
