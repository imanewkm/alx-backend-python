from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to:
    - Allow only authenticated users.
    - Allow only participants of a conversation to access it.
    - Allow only message senders to edit or delete their messages.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'participants'):
            # obj is a Conversation
            return request.user in obj.participants.all()

        elif hasattr(obj, 'conversation'):
            # obj is a Message
            # Check participant access for viewing
            if request.method in SAFE_METHODS:
                return request.user in obj.conversation.participants.all()
            # For edits or deletes, only the sender can act
            elif request.method in ['PUT', 'PATCH', 'DELETE']:
                return request.user == obj.sender

        return False
