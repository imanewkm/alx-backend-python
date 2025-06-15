"""
Tests for Django signals implementation - User Notifications

This test suite specifically covers Task 0: Implement Signals for User Notifications
Testing the automatic notification system when users receive new messages.
"""

import uuid
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Conversation, Message, Notification
from .signals import create_message_notification

User = get_user_model()


class MessageNotificationSignalTestCase(TransactionTestCase):
    """Test case for message notification signals."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.sender = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='sender_user',
            email='sender@example.com',
            first_name='Sender',
            last_name='User',
            password='testpass123'
        )
        
        self.receiver = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='receiver_user',
            email='receiver@example.com',
            first_name='Receiver',
            last_name='User',
            password='testpass123'
        )
        
        self.user3 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='user3',
            email='user3@example.com',
            first_name='User',
            last_name='Three',
            password='testpass123'
        )
        
        # Create a conversation for group messaging
        self.group_conversation = Conversation.objects.create()
        self.group_conversation.participants.add(self.sender, self.receiver, self.user3)
        
        # Create a direct conversation
        self.direct_conversation = Conversation.objects.create()
        self.direct_conversation.participants.add(self.sender, self.receiver)
    
    def test_direct_message_notification_creation(self):
        """Test that notifications are created for direct messages."""
        # Create a direct message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            conversation=self.direct_conversation,
            message_body="Hello, this is a direct message!"
        )
        
        # Check that notification was created for the receiver
        notification = Notification.objects.filter(
            user=self.receiver,
            message=message,
            notification_type='new_message'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'new_message')
        self.assertFalse(notification.is_read)
        
        # Check that no notification was created for the sender
        sender_notification = Notification.objects.filter(
            user=self.sender,
            message=message
        ).first()
        
        self.assertIsNone(sender_notification)
    
    def test_group_message_notification_creation(self):
        """Test that notifications are created for all participants in group conversations."""
        # Create a group message (no specific receiver)
        message = Message.objects.create(
            sender=self.sender,
            conversation=self.group_conversation,
            message_body="Hello everyone in the group!"
        )
        
        # Check that notifications were created for all participants except sender
        notifications = Notification.objects.filter(
            message=message,
            notification_type='new_message'
        )
        
        # Should have 2 notifications (receiver and user3, but not sender)
        self.assertEqual(notifications.count(), 2)
        
        # Check specific notifications
        receiver_notification = notifications.filter(user=self.receiver).first()
        user3_notification = notifications.filter(user=self.user3).first()
        
        self.assertIsNotNone(receiver_notification)
        self.assertIsNotNone(user3_notification)
        
        # Ensure sender didn't get a notification
        sender_notification = notifications.filter(user=self.sender).first()
        self.assertIsNone(sender_notification)
    
    def test_notification_fields_are_correct(self):
        """Test that notification fields are populated correctly."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            conversation=self.direct_conversation,
            message_body="Test message for field validation"
        )
        
        notification = Notification.objects.get(
            user=self.receiver,
            message=message
        )
        
        # Check all fields
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'new_message')
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
        self.assertIsNotNone(notification.notification_id)
    
    def test_multiple_messages_create_multiple_notifications(self):
        """Test that multiple messages create separate notifications."""
        # Send multiple messages
        message1 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            conversation=self.direct_conversation,
            message_body="First message"
        )
        
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            conversation=self.direct_conversation,
            message_body="Second message"
        )
        
        # Check that two separate notifications were created
        notifications = Notification.objects.filter(
            user=self.receiver,
            notification_type='new_message'
        ).order_by('created_at')
        
        self.assertEqual(notifications.count(), 2)
        self.assertEqual(notifications[0].message, message1)
        self.assertEqual(notifications[1].message, message2)
    
    def test_signal_handles_message_updates_correctly(self):
        """Test that signal only creates notifications on creation, not updates."""
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            conversation=self.direct_conversation,
            message_body="Original message"
        )
        
        initial_notification_count = Notification.objects.filter(
            user=self.receiver,
            message=message
        ).count()
        
        # Update the message
        message.message_body = "Updated message"
        message.save()
        
        # Check that no additional notifications were created
        final_notification_count = Notification.objects.filter(
            user=self.receiver,
            message=message
        ).count()
        
        self.assertEqual(initial_notification_count, final_notification_count)
    
    def test_notification_cascade_deletion(self):
        """Test that notifications are deleted when messages are deleted."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            conversation=self.direct_conversation,
            message_body="Message to be deleted"
        )
        
        # Verify notification was created
        notification_exists = Notification.objects.filter(
            user=self.receiver,
            message=message
        ).exists()
        self.assertTrue(notification_exists)
        
        # Delete the message
        message.delete()
        
        # Verify notification was also deleted (CASCADE)
        notification_exists_after = Notification.objects.filter(
            user=self.receiver,
            message=message
        ).exists()
        self.assertFalse(notification_exists_after)
    
    def test_get_receivers_method_direct_message(self):
        """Test the get_receivers method for direct messages."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            conversation=self.direct_conversation,
            message_body="Direct message test"
        )
        
        receivers = message.get_receivers()
        self.assertEqual(len(receivers), 1)
        self.assertEqual(receivers[0], self.receiver)
    
    def test_get_receivers_method_group_message(self):
        """Test the get_receivers method for group messages."""
        message = Message.objects.create(
            sender=self.sender,
            conversation=self.group_conversation,
            message_body="Group message test"
        )
        
        receivers = list(message.get_receivers())
        self.assertEqual(len(receivers), 2)  # receiver and user3, not sender
        self.assertIn(self.receiver, receivers)
        self.assertIn(self.user3, receivers)
        self.assertNotIn(self.sender, receivers)
    
    def test_bulk_notification_creation_efficiency(self):
        """Test that notifications are created efficiently using bulk_create."""
        # Create a message in a group with multiple participants
        message = Message.objects.create(
            sender=self.sender,
            conversation=self.group_conversation,
            message_body="Bulk notification test"
        )
        
        # Verify all notifications were created
        notifications = Notification.objects.filter(
            message=message,
            notification_type='new_message'
        )
        
        self.assertEqual(notifications.count(), 2)
        
        # Verify that all notifications have the same created_at time
        # (indicating they were created in a single bulk operation)
        created_times = [n.created_at for n in notifications]
        # All times should be very close (within 1 second)
        time_diff = max(created_times) - min(created_times)
        self.assertLess(time_diff.total_seconds(), 1)


class NotificationModelTestCase(TestCase):
    """Test case for the Notification model itself."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        self.sender = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='sender',
            email='sender@example.com',
            first_name='Sender',
            last_name='User',
            password='testpass123'
        )
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user, self.sender)
        
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            conversation=self.conversation,
            message_body="Test message"
        )
    
    def test_notification_string_representation(self):
        """Test the string representation of notifications."""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            notification_type='new_message'
        )
        
        expected_str = f"Notification for {self.user} - new_message"
        self.assertEqual(str(notification), expected_str)
    
    def test_notification_default_values(self):
        """Test that notification default values are set correctly."""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message
        )
        
        self.assertEqual(notification.notification_type, 'new_message')
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
        self.assertIsNotNone(notification.notification_id)
    
    def test_notification_types(self):
        """Test different notification types."""
        # Test all available notification types
        types = ['new_message', 'message_edit', 'mention']
        
        for notif_type in types:
            notification = Notification.objects.create(
                user=self.user,
                message=self.message,
                notification_type=notif_type
            )
            self.assertEqual(notification.notification_type, notif_type)
    
    def test_notification_ordering(self):
        """Test that notifications are ordered by created_at descending."""
        # Create multiple notifications
        notification1 = Notification.objects.create(
            user=self.user,
            message=self.message,
            notification_type='new_message'
        )
        
        # Create another message and notification
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            conversation=self.conversation,
            message_body="Second message"
        )
        
        notification2 = Notification.objects.create(
            user=self.user,
            message=message2,
            notification_type='new_message'
        )
        
        # Get notifications in default order
        notifications = list(Notification.objects.filter(user=self.user))
        
        # Should be ordered by created_at descending (newest first)
        self.assertEqual(notifications[0], notification2)
        self.assertEqual(notifications[1], notification1)
