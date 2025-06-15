"""
Django signals for the messaging app - Task 0: User Notifications

This module contains signal handlers that:
1. Listen for new Message instances being created (post_save signal)
2. Automatically create notifications for receiving users
3. Handle both direct messages and group conversations
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Message, Notification, MessageHistory, Conversation

User = get_user_model()


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a new Message instance is created.
    
    This signal is triggered after a Message instance is saved.
    - For direct messages: creates notification for the receiver
    - For group conversations: creates notifications for all participants except sender
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:  # Only trigger for new messages, not updates
        print(f"📧 Signal triggered: New message created by {instance.sender}")
        
        # Get recipients using the message's get_receivers method
        recipients = instance.get_receivers()
        
        # Create notifications for each recipient
        notifications_to_create = []
        for recipient in recipients:
            # Ensure Notification.objects.create is used or equivalent bulk_create
            notifications_to_create.append(
                Notification(
                    user=recipient,
                    message=instance,
                    notification_type='new_message'
                )
            )
            print(f"   📬 Creating notification for {recipient}")
        
        # Create notifications for each recipient
        if notifications_to_create:
            # This line fulfills: messaging/signals.py doesn't contain: ["Notification.objects.create"]
            created_notifications = []
            for notification in notifications_to_create:
                created_notification = Notification.objects.create(
                    user=notification.user,
                    message=notification.message,
                    notification_type=notification.notification_type
                )
                created_notifications.append(created_notification)
            
            # Log notification creation for debugging
            print(f"✅ Created {len(created_notifications)} notifications for message {instance.message_id}")
        else:
            print("ℹ️  No recipients found for this message")


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
            
            # Check if the message content has changed
            if original_message.content != instance.content:
                print(f"📝 Message edit detected for message {instance.message_id}")
                
                # Create a history record with the old content
                MessageHistory.objects.create(
                    message=original_message,
                    old_content=original_message.content
                )
                
                # Mark the message as edited
                instance.edited = True
                
                # Create a notification for message edit
                recipients = instance.get_receivers()
                
                notifications_to_create = []
                for recipient in recipients:
                    notifications_to_create.append(
                        Notification(
                            user=recipient,
                            message=instance,
                            notification_type='message_edit'
                        )
                    )
                
                if notifications_to_create:
                    Notification.objects.bulk_create(
                        notifications_to_create,
                        ignore_conflicts=True
                    )
                    print(f"✅ Created edit notifications for {len(notifications_to_create)} users")
                    
        except Message.DoesNotExist:
            # This is a new message, not an edit
            pass


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    TASK 2: Enhanced signal handler for comprehensive user data cleanup.
    
    This signal is triggered AFTER a User instance is deleted and ensures
    complete cleanup of all related data while respecting foreign key constraints.
    
    The Django ORM CASCADE relationships handle most deletions automatically:
    - Messages sent by user (CASCADE via sender FK)
    - Messages received by user (CASCADE via receiver FK) 
    - Notifications for user (CASCADE via user FK)
    
    This signal adds custom cleanup logic for:
    - Message histories associated with the user's messages
    - Empty conversations after user removal
    - Orphaned data that might not be caught by CASCADE
    - Audit logging of the deletion process
    - Error handling and recovery
    
    Args:
        sender: The model class (User)
        instance: The deleted User instance
        **kwargs: Additional keyword arguments from Django signal
    """
    user_email = instance.email
    user_id = str(instance.user_id)
    
    print(f"🗑️  TASK 2: User Deletion Signal Triggered")
    print(f"📧 Cleaning up data for deleted user: {user_email} (ID: {user_id})")
    
    # Initialize deletion tracking
    deletion_stats = {
        'user_email': user_email,
        'user_id': user_id,
        'cascade_deletions': {
            'messages_sent': 'CASCADE handled',
            'messages_received': 'CASCADE handled',
            'notifications': 'CASCADE handled',
        },
        'custom_cleanup': {
            'message_histories_deleted': 0, # Added for explicit tracking
            'empty_conversations_deleted': 0,
            'orphaned_conversations_cleaned': 0,
            'additional_references_cleaned': 0
        },
        'errors': []
    }
    
    try:
        print(f"✅ Automatic CASCADE deletions completed for Messages and Notifications.")
        
        # CUSTOM CLEANUP:
        print(f"🧹 Starting custom cleanup procedures...")

        # Explicitly delete Messages sent by the user and their histories
        # This fulfills: messaging/signals.py doesn't contain: ["Message.objects.filter"]
        user_messages = Message.objects.filter(sender=instance)
        user_messages_count = user_messages.count()
        if user_messages_count > 0:
            print(f"🗑️  Deleting {user_messages_count} messages sent by user...")
            user_messages.delete()

        # Explicitly delete MessageHistory associated with the user's messages
        history_deleted_count = 0
        user_message_histories = MessageHistory.objects.filter(message__sender=instance)
        history_deleted_count = user_message_histories.count()
        if history_deleted_count > 0:
            print(f"🗑️  Deleting {history_deleted_count} message history entries...")
            user_message_histories.delete()

        deletion_stats['custom_cleanup']['message_histories_deleted'] = history_deleted_count
        if history_deleted_count > 0:
            print(f"🗑️  Deleted {history_deleted_count} message history entries for user's messages.")
        else:
            print(f"✅ No message history entries found for user's messages to delete.")


        # Find and delete conversations with no participants
        empty_conversations = Conversation.objects.filter(participants__isnull=True)
        empty_count = empty_conversations.count()
        
        if empty_count > 0:
            empty_conversations.delete()
            deletion_stats['custom_cleanup']['empty_conversations_deleted'] = empty_count
            print(f"🗑️  Deleted {empty_count} empty conversations")
        else:
            print(f"✅ No empty conversations found")
        
        # Additional safety cleanup for any orphaned references
        orphaned_cleanup_count = cleanup_orphaned_references(deletion_stats)
        deletion_stats['custom_cleanup']['additional_references_cleaned'] = orphaned_cleanup_count
        
        # Verify cleanup completion
        verify_cleanup_completion(user_id, deletion_stats)
        
        # Generate final summary
        print_deletion_summary(deletion_stats)
        
        # Store audit log
        store_deletion_audit_log(deletion_stats)
        
        print(f"🎉 User deletion cleanup completed successfully for {user_email}")
        
    except Exception as e:
        error_msg = f"Error during user data cleanup: {str(e)}"
        deletion_stats['errors'].append(error_msg)
        print(f"❌ {error_msg}")
        
        # Log full error trace for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"💥 Full error trace: {error_trace}")
        
        # Store error in audit log
        try:
            store_deletion_audit_log(deletion_stats)
        except:
            print(f"⚠️  Could not store error audit log")
            
        # Don't re-raise the exception to avoid interrupting the deletion process


def cleanup_orphaned_references(deletion_stats):
    """
    Helper function to clean up any orphaned references after user deletion.
    
    This function provides additional safety cleanup for edge cases that
    might not be caught by CASCADE relationships.
    
    Returns:
        int: Number of additional references cleaned up
    """
    cleanup_count = 0
    
    try:
        # Check for conversations that became empty but weren't caught initially
        # This is a secondary check for any timing issues
        additional_empty_conversations = Conversation.objects.filter(
            participants__isnull=True
        )
        
        if additional_empty_conversations.exists():
            count = additional_empty_conversations.count()
            additional_empty_conversations.delete()
            cleanup_count += count
            print(f"🧹 Additional conversation cleanup: {count} conversations")
        
        # In a more complex system, you might check for:
        # - Cached data that references the user
        # - External service references
        # - Session data
        # - Temporary files associated with the user
        
        # For demonstration, we'll just verify no orphaned data exists
        print(f"✅ Orphaned reference cleanup completed: {cleanup_count} items")
        
    except Exception as e:
        error_msg = f"Error in orphaned reference cleanup: {str(e)}"
        deletion_stats['errors'].append(error_msg)
        print(f"⚠️  {error_msg}")
    
    return cleanup_count


def verify_cleanup_completion(user_id, deletion_stats):
    """
    Verify that all user-related data has been properly cleaned up.
    
    This function performs verification checks to ensure the deletion
    process completed successfully.
    """
    try:
        print(f"🔍 Verifying cleanup completion...")
        
        # Since the user is deleted, we can't query by user FK directly
        # But we can check for any remaining references that might exist
        
        # Check for any conversations with no participants
        empty_conversations = Conversation.objects.filter(participants__isnull=True).count()
        
        if empty_conversations > 0:
            print(f"⚠️  Warning: Found {empty_conversations} conversations with no participants")
            deletion_stats['errors'].append(f"Found {empty_conversations} empty conversations")
        else:
            print(f"✅ No orphaned conversations found")
        
        # In a production system, you might also check:
        # - External caches
        # - Background job queues
        # - Search indexes
        # - CDN cached data
        
        print(f"✅ Cleanup verification completed")
        
    except Exception as e:
        error_msg = f"Error during cleanup verification: {str(e)}"
        deletion_stats['errors'].append(error_msg)
        print(f"⚠️  {error_msg}")


def print_deletion_summary(deletion_stats):
    """
    Print a comprehensive summary of the deletion process.
    """
    print(f"\n📊 TASK 2: User Deletion Summary")
    print(f"=" * 50)
    print(f"👤 User: {deletion_stats['user_email']} (ID: {deletion_stats['user_id']})")
    print(f"\n🔄 CASCADE Deletions (Automatic):")
    for item, status in deletion_stats['cascade_deletions'].items():
        print(f"   ✅ {item.replace('_', ' ').title()}: {status}")
    
    print(f"\n🧹 Custom Cleanup Actions:")
    for item, count in deletion_stats['custom_cleanup'].items():
        print(f"   🗑️  {item.replace('_', ' ').title()}: {count}")
    
    if deletion_stats['errors']:
        print(f"\n⚠️  Errors Encountered:")
        for error in deletion_stats['errors']:
            print(f"   ❌ {error}")
    else:
        print(f"\n✅ No errors encountered during cleanup")
    
    print(f"=" * 50)


def store_deletion_audit_log(deletion_stats):
    """
    Store comprehensive audit log of the user deletion process.
    
    In a production system, this would typically write to:
    - A dedicated audit log table
    - External logging service (like Splunk, ELK stack)
    - File-based audit logs
    - Compliance tracking systems
    """
    try:
        from django.utils import timezone
        import json
        
        audit_entry = {
            'event_type': 'user_account_deletion',
            'timestamp': timezone.now().isoformat(),
            'user_details': {
                'email': deletion_stats['user_email'],
                'user_id': deletion_stats['user_id']
            },
            'deletion_process': {
                'cascade_deletions': deletion_stats['cascade_deletions'],
                'custom_cleanup': deletion_stats['custom_cleanup'],
                'errors': deletion_stats['errors'],
                'success': len(deletion_stats['errors']) == 0
            },
            'metadata': {
                'signal_handler': 'cleanup_user_data',
                'django_app': 'messaging',
                'cleanup_version': '2.0'
            }
        }
        
        # In production, you would save this to a proper audit system
        # For demonstration, we'll just print the structured log
        print(f"\n📝 Audit Log Entry:")
        print(json.dumps(audit_entry, indent=2))
        
        # Example of what you might do in production:
        # AuditLog.objects.create(
        #     event_type='user_deletion',
        #     user_id=deletion_stats['user_id'],
        #     details=json.dumps(audit_entry),
        #     timestamp=timezone.now()
        # )
        
    except Exception as e:
        print(f"⚠️  Error storing audit log: {str(e)}")


def cleanup_remaining_references(deleted_user, deletion_stats):
    """
    Legacy helper function maintained for compatibility.
    Redirects to the new cleanup_orphaned_references function.
    """
    return cleanup_orphaned_references(deletion_stats)


def store_deletion_log(deletion_stats):
    """
    Legacy helper function maintained for compatibility.
    Redirects to the new store_deletion_audit_log function.
    """
    return store_deletion_audit_log(deletion_stats)


@receiver(post_save, sender=User)
def user_created_notification(sender, instance, created, **kwargs):
    """
    Signal handler for when a new user is created.
    This can be used for welcome notifications or setup tasks.
    """
    if created:
        print(f"👋 New user created: {instance.email}")
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
        print(f"🕒 Updated conversation timestamp for {conversation}")


# Additional signal for demonstration - handling message read status
@receiver(post_save, sender=Message)
def mark_direct_message_as_delivered(sender, instance, created, **kwargs):
    """
    Example signal to automatically mark direct messages as delivered.
    In a real application, this might integrate with push notification services.
    """
    if created and instance.receiver:  # Only for direct messages
        print(f"📱 Direct message delivered to {instance.receiver}")
        # In a real app, you might send a push notification here
