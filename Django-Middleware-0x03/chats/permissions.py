from rest_framework import permissions 
from .models import Conversation, Message


class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission class that enforces conversation-based access control.
    
    Ensures that only authenticated users who are participants in a conversation
    can perform operations on that conversation and its messages.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to perform the requested action on the object.
        """
        user = request.user
        
        if isinstance(obj, Conversation):
            return obj.participants.filter(user_id=user.user_id).exists()
            
        elif isinstance(obj, Message):
            is_participant = obj.conversation.participants.filter(user_id=user.user_id).exists()
            if not is_participant:
                return False

            if request.method in ['PUT', 'PATCH', 'DELETE']:
                return obj.sender.user_id == user.user_id
                
            return True
        
        return False