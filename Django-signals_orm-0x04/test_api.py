#!/usr/bin/env python3
"""
Simple test script to verify the messaging app API is working.
Run this after starting the Django server with: python manage.py runserver
"""

import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("🧪 Testing Messaging App API...")
    
    # Test data
    test_user = {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        # 1. Test user registration
        print("\n1. Testing user registration...")
        response = requests.post(f"{BASE_URL}/api/auth/register/", json=test_user)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            access_token = data['access']
            user_id = data['user']['user_id']
            print(f"✅ User registered successfully! User ID: {user_id}")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
        
        # 2. Test authentication
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Test user profile
        print("\n2. Testing user profile...")
        response = requests.get(f"{BASE_URL}/api/auth/profile/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Profile retrieved successfully!")
        else:
            print(f"❌ Profile retrieval failed: {response.text}")
        
        # 4. Test conversation creation
        print("\n3. Testing conversation creation...")
        conversation_data = {"participant_ids": [user_id]}
        response = requests.post(f"{BASE_URL}/api/conversations/", 
                               json=conversation_data, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            conversation_id = response.json()['conversation_id']
            print(f"✅ Conversation created! ID: {conversation_id}")
        else:
            print(f"❌ Conversation creation failed: {response.text}")
            return
        
        # 5. Test message creation
        print("\n4. Testing message creation...")
        message_data = {
            "conversation": conversation_id,
            "message_body": "Hello! This is a test message."
        }
        response = requests.post(f"{BASE_URL}/api/messages/", 
                               json=message_data, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            message_id = response.json()['message_id']
            print(f"✅ Message created! ID: {message_id}")
        else:
            print(f"❌ Message creation failed: {response.text}")
            return
        
        # 6. Test message retrieval
        print("\n5. Testing message retrieval...")
        response = requests.get(f"{BASE_URL}/api/messages/", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Retrieved {messages['count']} messages!")
        else:
            print(f"❌ Message retrieval failed: {response.text}")
        
        # 7. Test unauthorized access
        print("\n6. Testing unauthorized access...")
        response = requests.get(f"{BASE_URL}/api/conversations/")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Unauthorized access properly blocked!")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
        
        print("\n🎉 All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure Django server is running:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_api()
