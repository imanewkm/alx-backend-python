"""
Tests for Django signals, ORM optimization, and caching in the messaging app.

These tests cover:
1. Signal handlers for notifications and message history
2. Advanced ORM techniques for threaded conversations
3. Custom managers for unread messages
4. User deletion and cleanup
5. Caching functionality
"""

import uuid
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.cache import cache
from django.test.utils import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Conversation, Message, Notification, MessageHistory
from .signals import (
    create_message_notification, 
    log_message_edit, 
    cleanup_user_data
)

User = get_user_model()


class SignalTestCase(TransactionTestCase):
    """Test case for Django signals functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser1',
            email='test1@example.com',
            first_name='Test',
            last_name='User1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User2',
            password='testpass123'
        )
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
    
    def test_message_notification_signal(self):
        """Test that notifications are created when a new message is sent."""
        # Create a message
        message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Hello, this is a test message!"
        )
        
        # Check that a notification was created for user2
        notification = Notification.objects.filter(
            user=self.user2,
            message=message,
            notification_type='new_message'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.message, message)
        
        # Check that no notification was created for the sender
        sender_notification = Notification.objects.filter(
            user=self.user1,
            message=message
        ).first()
        
        self.assertIsNone(sender_notification)
    
    def test_message_edit_history_signal(self):
        """Test that message edit history is logged when a message is updated."""
        # Create a message
        message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Original content"
        )
        
        # Update the message
        message.message_body = "Updated content"
        message.save()
        
        # Check that message history was created
        history = MessageHistory.objects.filter(message=message).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.old_content, "Original content")
        
        # Check that the message is marked as edited
        message.refresh_from_db()
        self.assertTrue(message.edited)
        
        # Check that edit notification was created
        edit_notification = Notification.objects.filter(
            user=self.user2,
            message=message,
            notification_type='message_edit'
        ).first()
        
        self.assertIsNotNone(edit_notification)
    
    def test_user_deletion_cleanup_signal(self):
        """Test that user-related data is cleaned up when a user is deleted."""
        # Create some data for the user
        message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Test message before deletion"
        )
        
        notification = Notification.objects.create(
            user=self.user2,
            message=message,
            notification_type='new_message'
        )
        
        # Get initial counts
        initial_message_count = Message.objects.count()
        initial_notification_count = Notification.objects.count()
        
        # Delete the user
        user1_id = self.user1.user_id
        self.user1.delete()
        
        # Check that the user is deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(user_id=user1_id)
        
        # Messages should be deleted due to CASCADE
        self.assertEqual(Message.objects.count(), initial_message_count - 1)
        
        # Notifications for the deleted user should be deleted due to CASCADE
        # (notifications by other users about this user's messages are also deleted)
        self.assertLess(Notification.objects.count(), initial_notification_count)


class CustomManagerTestCase(TestCase):
    """Test case for custom managers."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser1',
            email='test1@example.com',
            first_name='Test',
            last_name='User1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User2',
            password='testpass123'
        )
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
    
    def test_unread_messages_manager(self):
        """Test the custom UnreadMessagesManager functionality."""
        # Create messages
        message1 = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="First message",
            read=False
        )
        
        message2 = Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="Second message",
            read=False
        )
        
        message3 = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Third message",
            read=True
        )
        
        # Test unread messages for user1 (should not include own messages)
        unread_for_user1 = Message.unread.for_user(self.user1)
        self.assertEqual(unread_for_user1.count(), 1)
        self.assertEqual(unread_for_user1.first(), message2)
        
        # Test unread messages for user2
        unread_for_user2 = Message.unread.for_user(self.user2)
        self.assertEqual(unread_for_user2.count(), 1)
        self.assertEqual(unread_for_user2.first(), message1)
        
        # Test mark_as_read functionality
        marked_count = Message.unread.mark_as_read(self.user1)
        self.assertEqual(marked_count, 1)
        
        # Check that message2 is now marked as read
        message2.refresh_from_db()
        self.assertTrue(message2.read)
        
        # Check that no more unread messages for user1
        unread_for_user1_after = Message.unread.for_user(self.user1)
        self.assertEqual(unread_for_user1_after.count(), 0)


class ThreadedConversationTestCase(TestCase):
    """Test case for threaded conversation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser1',
            email='test1@example.com',
            first_name='Test',
            last_name='User1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User2',
            password='testpass123'
        )
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
    
    def test_threaded_messages(self):
        """Test threaded message functionality."""
        # Create parent message
        parent_message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="This is the parent message"
        )
        
        # Create replies
        reply1 = Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="This is reply 1",
            parent_message=parent_message
        )
        
        reply2 = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="This is reply 2",
            parent_message=parent_message
        )
        
        # Create nested reply
        nested_reply = Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="This is a nested reply",
            parent_message=reply1
        )
        
        # Test that replies are properly linked
        self.assertEqual(parent_message.replies.count(), 2)
        self.assertEqual(reply1.replies.count(), 1)
        self.assertEqual(reply2.replies.count(), 0)
        
        # Test that parent references are correct
        self.assertEqual(reply1.parent_message, parent_message)
        self.assertEqual(reply2.parent_message, parent_message)
        self.assertEqual(nested_reply.parent_message, reply1)
        
        # Test optimized query for threaded messages
        messages_with_replies = Message.objects.filter(
            conversation=self.conversation
        ).prefetch_related('replies__sender')
        
        # This should trigger only a few queries due to prefetch_related
        for message in messages_with_replies:
            replies = message.replies.all()
            for reply in replies:
                # Accessing sender shouldn't trigger additional queries
                sender_name = reply.sender.first_name


class CachingTestCase(TestCase):
    """Test case for caching functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser1',
            email='test1@example.com',
            first_name='Test',
            last_name='User1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User2',
            password='testpass123'
        )
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
        
        # Create some messages
        for i in range(5):
            Message.objects.create(
                sender=self.user1 if i % 2 == 0 else self.user2,
                conversation=self.conversation,
                message_body=f"Test message {i+1}"
            )
    
    def test_cache_configuration(self):
        """Test that cache is properly configured."""
        # Test basic cache functionality
        cache.set('test_key', 'test_value', 30)
        self.assertEqual(cache.get('test_key'), 'test_value')
        
        # Clear cache
        cache.clear()
        self.assertIsNone(cache.get('test_key'))
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    })
    def test_view_caching(self):
        """Test that views are properly cached."""
        # This would require setting up API test client and testing actual view caching
        # For now, we verify that the cache backend is working
        from django.core.cache import cache as test_cache
        
        test_cache.set('view_cache_test', {'messages': ['test']}, 60)
        cached_data = test_cache.get('view_cache_test')
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['messages'], ['test'])


class APIIntegrationTestCase(APITestCase):
    """Integration tests for the API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser1',
            email='test1@example.com',
            first_name='Test',
            last_name='User1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            user_id=uuid.uuid4(),
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User2',
            password='testpass123'
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user1)
        self.access_token = str(refresh.access_token)
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
    
    def test_user_deletion_endpoint(self):
        """Test the user deletion endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Test deleting own account
        response = self.client.delete(f'/api/users/{self.user1.user_id}/delete_user/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(user_id=self.user1.user_id)
    
    def test_threaded_replies_endpoint(self):
        """Test the threaded replies endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create parent message
        parent_message = Message.objects.create(
            sender=self.user1,
            conversation=self.conversation,
            message_body="Parent message"
        )
        
        # Create reply
        reply = Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="Reply to parent",
            parent_message=parent_message
        )
        
        # Test threaded replies endpoint
        response = self.client.get(f'/api/messages/{parent_message.message_id}/threaded_replies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('threaded_replies', data)
        self.assertEqual(len(data['threaded_replies']), 1)
        self.assertEqual(data['threaded_replies'][0]['message_body'], "Reply to parent")
    
    def test_unread_messages_endpoint(self):
        """Test the unread messages endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create unread message from user2
        Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="Unread message",
            read=False
        )
        
        # Test unread messages endpoint
        response = self.client.get('/api/messages/unread/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertGreater(len(data['results']), 0)
    
    def test_mark_read_endpoint(self):
        """Test the mark as read endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create unread message
        Message.objects.create(
            sender=self.user2,
            conversation=self.conversation,
            message_body="Unread message",
            read=False
        )
        
        # Test mark as read endpoint
        response = self.client.post('/api/messages/mark_read/', {
            'conversation_id': str(self.conversation.conversation_id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('count', data)
        self.assertGreater(data['count'], 0)
