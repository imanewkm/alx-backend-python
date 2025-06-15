from rest_framework import permissions
from rest_framework.permissions import BasePermission
from .models import Conversation


class IsParticipantOfConversation(BasePermission):
    """
    Custom permission to only allow participants of a conversation to access it.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is a participant in the conversation.
        """
        # For Conversation objects
        if isinstance(obj, Conversation):
            return obj.participants.filter(user_id=request.user.user_id).exists()
        
        # For Message objects, check if user is participant in the conversation
        if hasattr(obj, 'conversation'):
            return obj.conversation.participants.filter(user_id=request.user.user_id).exists()
        
        # For other objects, check if it belongs to the user
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        
        return False


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        """
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner of the object
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        
        return obj == request.user


class IsAuthenticatedParticipant(BasePermission):
    """
    Permission class that combines authentication check with conversation participation.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check specific object permissions based on the object type.
        """
        # For Conversation objects
        if isinstance(obj, Conversation):
            return obj.participants.filter(user_id=request.user.user_id).exists()
        
        # For Message objects
        if hasattr(obj, 'conversation'):
            # Check if user is participant in the conversation
            is_participant = obj.conversation.participants.filter(
                user_id=request.user.user_id
            ).exists()
            
            # For unsafe methods (PUT, PATCH, DELETE), also check ownership
            if request.method not in permissions.SAFE_METHODS:
                return is_participant and obj.sender == request.user
            
            return is_participant
        
        return False


class CanCreateMessage(BasePermission):
    """
    Permission to check if user can create a message in a conversation.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and can create message.
        """
        if not (request.user and request.user.is_authenticated):
            return False
        
        # For POST requests, check if user is participant in the conversation
        if request.method == 'POST':
            conversation_id = request.data.get('conversation')
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(conversation_id=conversation_id)
                    return conversation.participants.filter(
                        user_id=request.user.user_id
                    ).exists()
                except Conversation.DoesNotExist:
                    return False
        
        return True
