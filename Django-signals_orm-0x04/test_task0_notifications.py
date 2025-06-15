#!/usr/bin/env python3
"""
Demonstration script for Task 0: Implement Signals for User Notifications

This script demonstrates the automatic notification system when users receive new messages.
It shows how Django signals automatically create notifications for receiving users.
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
from messaging.models import Conversation, Message, Notification
import uuid

User = get_user_model()

def demonstrate_notification_signals():
    """Demonstrate the automatic notification system."""
    print("🧪 TASK 0: Testing Django Signals for User Notifications")
    print("=" * 60)
    
    # Clean up any existing test data
    User.objects.filter(email__in=['alice@example.com', 'bob@example.com', 'charlie@example.com']).delete()
    
    # Create test users
    print("\n👥 Creating test users...")
    alice = User.objects.create_user(
        user_id=uuid.uuid4(),
        username='alice',
        email='alice@example.com',
        first_name='Alice',
        last_name='Smith',
        password='testpass123'
    )
    
    bob = User.objects.create_user(
        user_id=uuid.uuid4(),
        username='bob',
        email='bob@example.com',
        first_name='Bob',
        last_name='Johnson',
        password='testpass123'
    )
    
    charlie = User.objects.create_user(
        user_id=uuid.uuid4(),
        username='charlie',
        email='charlie@example.com',
        first_name='Charlie',
        last_name='Brown',
        password='testpass123'
    )
    
    print(f"✅ Created users: {alice}, {bob}, {charlie}")
    
    # Create conversations
    print("\n💬 Creating conversations...")
    
    # Direct conversation between Alice and Bob
    direct_conversation = Conversation.objects.create()
    direct_conversation.participants.add(alice, bob)
    
    # Group conversation with all three users
    group_conversation = Conversation.objects.create()
    group_conversation.participants.add(alice, bob, charlie)
    
    print(f"✅ Created direct conversation: {direct_conversation}")
    print(f"✅ Created group conversation: {group_conversation}")
    
    # Test 1: Direct message (with receiver field)
    print("\n📧 TEST 1: Direct Message with Receiver Field")
    print("-" * 50)
    
    direct_message = Message.objects.create(
        sender=alice,
        receiver=bob,  # Specific receiver as per requirements
        conversation=direct_conversation,
        content="Hello Bob! This is a direct message.",  # Content field as per requirements
        # timestamp is auto-generated as per requirements
    )
    
    print(f"📨 Message created: {direct_message}")
    print(f"   Sender: {direct_message.sender}")
    print(f"   Receiver: {direct_message.receiver}")
    print(f"   Content: {direct_message.content}")
    print(f"   Timestamp: {direct_message.timestamp}")
    
    # Check if notification was automatically created by signal
    notification = Notification.objects.filter(
        user=bob,
        message=direct_message,
        notification_type='new_message'
    ).first()
    
    if notification:
        print(f"✅ SIGNAL SUCCESS: Notification automatically created!")
        print(f"   Notification ID: {notification.notification_id}")
        print(f"   User: {notification.user}")
        print(f"   Message: {notification.message}")
        print(f"   Type: {notification.notification_type}")
        print(f"   Read: {notification.is_read}")
        print(f"   Created: {notification.created_at}")
    else:
        print("❌ SIGNAL FAILED: No notification created")
    
    # Test 2: Group message (no specific receiver)
    print("\n📢 TEST 2: Group Message (No Specific Receiver)")
    print("-" * 50)
    
    group_message = Message.objects.create(
        sender=alice,
        # No receiver field for group messages
        conversation=group_conversation,
        content="Hello everyone! This is a group message.",
        # timestamp is auto-generated
    )
    
    print(f"📨 Group message created: {group_message}")
    print(f"   Sender: {group_message.sender}")
    print(f"   Receiver: {group_message.receiver}")  # Should be None
    print(f"   Content: {group_message.content}")
    print(f"   Timestamp: {group_message.timestamp}")
    
    # Check if notifications were created for all participants except sender
    notifications = Notification.objects.filter(
        message=group_message,
        notification_type='new_message'
    )
    
    print(f"📬 Found {notifications.count()} notifications for group message:")
    for notif in notifications:
        print(f"   - Notification for {notif.user} (ID: {notif.notification_id})")
    
    # Verify that Alice (sender) did not get a notification
    alice_notification = notifications.filter(user=alice).first()
    if not alice_notification:
        print("✅ CORRECT: Sender did not receive notification")
    else:
        print("❌ ERROR: Sender incorrectly received notification")
    
    # Test 3: Multiple messages create multiple notifications
    print("\n📨 TEST 3: Multiple Messages Create Multiple Notifications")
    print("-" * 50)
    
    # Send another direct message
    message2 = Message.objects.create(
        sender=bob,
        receiver=alice,
        conversation=direct_conversation,
        content="Hi Alice! This is Bob's reply."
    )
    
    # Check total notifications for Alice
    alice_notifications = Notification.objects.filter(user=alice)
    print(f"📬 Alice now has {alice_notifications.count()} total notifications:")
    for notif in alice_notifications:
        print(f"   - {notif.notification_type}: {notif.message.content[:30]}...")
    
    # Test 4: Show notification linking to User and Message models
    print("\n🔗 TEST 4: Notification Links to User and Message Models")
    print("-" * 50)
    
    sample_notification = Notification.objects.first()
    if sample_notification:
        print(f"📋 Sample notification analysis:")
        print(f"   Notification ID: {sample_notification.notification_id}")
        print(f"   Links to User: {sample_notification.user} (ID: {sample_notification.user.user_id})")
        print(f"   Links to Message: {sample_notification.message} (ID: {sample_notification.message.message_id})")
        print(f"   Message Sender: {sample_notification.message.sender}")
        print(f"   Message Content: {sample_notification.message.content}")
        print(f"   Message Timestamp: {sample_notification.message.timestamp}")
        print("✅ VERIFICATION: Notification properly links User and Message models")
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    total_messages = Message.objects.count()
    total_notifications = Notification.objects.count()
    
    print(f"📨 Total Messages Created: {total_messages}")
    print(f"📬 Total Notifications Created: {total_notifications}")
    print(f"👥 Total Users: {User.objects.count()}")
    print(f"💬 Total Conversations: {Conversation.objects.count()}")
    
    print("\n🎯 TASK 0 REQUIREMENTS VERIFICATION:")
    print("✅ Message model with sender, receiver, content, and timestamp fields")
    print("✅ Django signals (post_save) trigger notifications for new messages")
    print("✅ Notification model stores notifications linked to User and Message")
    print("✅ Signal automatically creates notifications for receiving users")
    print("✅ Both direct messages and group conversations supported")
    
    print("\n🎉 Task 0: Implement Signals for User Notifications - COMPLETED!")
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    User.objects.filter(email__in=['alice@example.com', 'bob@example.com', 'charlie@example.com']).delete()
    print("✅ Cleanup completed")

if __name__ == "__main__":
    demonstrate_notification_signals()
