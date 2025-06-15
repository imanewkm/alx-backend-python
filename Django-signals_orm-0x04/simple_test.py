#!/usr/bin/env python3
"""
Simple test script for Task 2: User Deletion with Signals
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messaging_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from messaging.models import Message, Conversation, Notification, MessageHistory

User = get_user_model()

def test_basic_functionality():
    """Test basic model creation and deletion"""
    print("🧪 Testing basic user deletion functionality...")
    
    # Create a test user
    user = User.objects.create_user(
        username='simple_test_user',
        email='simple_test@example.com',
        password='testpass123'
    )
    print(f"✅ Created user: {user.email}")
    
    # Create a conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(user)
    print(f"✅ Created conversation: {conversation.conversation_id}")
    
    # Create a message
    message = Message.objects.create(
        content="Test message",
        sender=user,
        conversation=conversation
    )
    print(f"✅ Created message: {message.message_id}")
    
    # Create notification
    notification = Notification.objects.create(
        user=user,
        message=message,
        notification_type='new_message'
    )
    print(f"✅ Created notification: {notification.notification_id}")
    
    # Create message history
    history = MessageHistory.objects.create(
        message=message,
        old_content="Original content"
    )
    print(f"✅ Created message history: {history.history_id}")
    
    # Count data before deletion
    user_id = user.user_id
    print(f"\n📊 Data before deletion:")
    print(f"   Messages: {Message.objects.filter(sender=user).count()}")
    print(f"   Notifications: {Notification.objects.filter(user=user).count()}")
    print(f"   Message Histories: {MessageHistory.objects.filter(message__sender=user).count()}")
    print(f"   Conversations: {user.messaging_conversations.count()}")
    
    # Delete the user (this should trigger the signal)
    print(f"\n🗑️  Deleting user: {user.email}")
    user.delete()
    print("✅ User deleted")
    
    # Check if data was cleaned up
    print(f"\n📊 Data after deletion:")
    print(f"   Messages from deleted user: {Message.objects.filter(sender_id=user_id).count()}")
    print(f"   Notifications for deleted user: {Notification.objects.filter(user_id=user_id).count()}")
    print(f"   Message Histories for deleted user: {MessageHistory.objects.filter(message__sender_id=user_id).count()}")
    
    # Check for empty conversations
    empty_conversations = Conversation.objects.filter(participants__isnull=True).count()
    print(f"   Empty conversations: {empty_conversations}")
    
    print("\n🎉 Simple test completed!")

if __name__ == '__main__':
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
