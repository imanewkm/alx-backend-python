#!/usr/bin/env python3
"""
Simple test script to verify Django signals and ORM implementation.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/home/fadel/Workspaces/ALX PROJECT/alx-backend-python/Django-signals_orm-0x04')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messaging_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from chats.models import Conversation, Message, Notification, MessageHistory
import uuid

User = get_user_model()

def test_signals_implementation():
    """Test the signals implementation."""
    print("🧪 Testing Django Signals Implementation...")
    
    # Create test users
    user1 = User.objects.create_user(
        user_id=uuid.uuid4(),
        username='testuser1',
        email='test1@example.com',
        first_name='Test',
        last_name='User1',
        password='testpass123'
    )
    
    user2 = User.objects.create_user(
        user_id=uuid.uuid4(),
        username='testuser2',
        email='test2@example.com',
        first_name='Test',
        last_name='User2',
        password='testpass123'
    )
    
    # Create conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(user1, user2)
    
    print("✅ Users and conversation created successfully")
    
    # Test 1: Message notification signal
    print("\n📧 Testing message notification signal...")
    message = Message.objects.create(
        sender=user1,
        conversation=conversation,
        message_body="Hello, this is a test message!"
    )
    
    # Check if notification was created
    notification = Notification.objects.filter(
        user=user2,
        message=message,
        notification_type='new_message'
    ).first()
    
    if notification:
        print("✅ Notification created successfully for new message")
    else:
        print("❌ Notification not created for new message")
    
    # Test 2: Message edit history signal
    print("\n📝 Testing message edit history signal...")
    original_content = message.message_body
    message.message_body = "Updated message content"
    message.save()
    
    # Check if history was created
    history = MessageHistory.objects.filter(message=message).first()
    if history and history.old_content == original_content:
        print("✅ Message edit history created successfully")
        print(f"   Original: {history.old_content}")
        print(f"   Updated: {message.message_body}")
    else:
        print("❌ Message edit history not created")
    
    # Check if message is marked as edited
    message.refresh_from_db()
    if message.edited:
        print("✅ Message marked as edited")
    else:
        print("❌ Message not marked as edited")
    
    # Test 3: Custom unread messages manager
    print("\n📬 Testing custom unread messages manager...")
    
    # Create an unread message
    unread_message = Message.objects.create(
        sender=user2,
        conversation=conversation,
        message_body="This is an unread message",
        read=False
    )
    
    # Test unread manager
    unread_messages = Message.unread.for_user(user1)
    if unread_messages.exists():
        print(f"✅ Found {unread_messages.count()} unread messages for user1")
    else:
        print("❌ No unread messages found")
    
    # Test mark as read
    marked_count = Message.unread.mark_as_read(user1)
    print(f"✅ Marked {marked_count} messages as read")
    
    # Test 4: Threaded conversations
    print("\n🧵 Testing threaded conversations...")
    
    # Create parent message
    parent_message = Message.objects.create(
        sender=user1,
        conversation=conversation,
        message_body="This is the parent message"
    )
    
    # Create reply
    reply = Message.objects.create(
        sender=user2,
        conversation=conversation,
        message_body="This is a reply",
        parent_message=parent_message
    )
    
    # Test threading
    if parent_message.replies.count() > 0:
        print("✅ Threaded conversation created successfully")
        print(f"   Parent: {parent_message.message_body}")
        print(f"   Reply: {reply.message_body}")
    else:
        print("❌ Threaded conversation not working")
    
    # Test 5: User deletion cleanup
    print("\n🗑️ Testing user deletion cleanup...")
    
    initial_message_count = Message.objects.count()
    initial_notification_count = Notification.objects.count()
    
    # Delete user1
    user1.delete()
    
    final_message_count = Message.objects.count()
    final_notification_count = Notification.objects.count()
    
    if final_message_count < initial_message_count:
        print("✅ User messages deleted successfully")
    else:
        print("❌ User messages not deleted")
    
    if final_notification_count < initial_notification_count:
        print("✅ User notifications cleaned up successfully")
    else:
        print("❌ User notifications not cleaned up")
    
    print(f"\n📊 Summary:")
    print(f"   Initial messages: {initial_message_count}")
    print(f"   Final messages: {final_message_count}")
    print(f"   Initial notifications: {initial_notification_count}")
    print(f"   Final notifications: {final_notification_count}")
    
    # Cleanup
    user2.delete()
    conversation.delete()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_signals_implementation()
