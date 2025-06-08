#!/usr/bin/env python3
"""
Custom permissions for messaging_app.chats.
"""

from rest_framework import permissions
from .models import Conversation

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to allow only authenticated users who are participants
    of a conversation to view, send, update, or delete messages.
    """

    def has_permission(self, request, view):
        # Require authentication globally
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission:
        Only participants of the conversation can perform:
        - GET (view), POST (send), PUT/PATCH (update), DELETE (delete)
        """

        user_is_participant = False

        # If checking a Conversation object
        if isinstance(obj, Conversation):
            user_is_participant = request.user in obj.participants.all()

        else:
            # If checking a Message object — assume it has a 'conversation' FK
            user_is_participant = request.user in obj.conversation.participants.all()

        # For safe methods (GET, HEAD, OPTIONS), allow if participant
        if request.method in permissions.SAFE_METHODS:
            return user_is_participant

        # Explicitly check unsafe methods: PUT, PATCH, DELETE
        if request.method in ("PUT", "PATCH", "DELETE"):
            return user_is_participant

        # For other methods (POST or anything else), also check participant
        return user_is_participant
