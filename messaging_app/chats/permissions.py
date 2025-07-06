from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrParticipant(BasePermission):
    """
    Custom permission to ensure users can access only their own messages and conversations.
    """

    def has_permission(self, request, view):
        # ensure the user is authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'participants'):  # For Conversations
            return request.user in obj.participants.all()
        elif hasattr(obj, 'sender'):  # For Messages
            return obj.sender == request.user or request.user in obj.conversation.participants.all()
        return False

class IsParticipantOfConversation(BasePermission):
    """
    Custom permission to ensure only participants of a conversation can send, view, update, and delete messages.
    """

    def has_permission(self, request, view):
        # Ensure the user is authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the object is a Conversation or a Message
        if hasattr(obj, 'participants'):  # For Conversation
            return request.user in obj.participants.all()
        elif hasattr(obj, 'sender'):  # For Message
            return (
                request.user in obj.conversation.participants.all()
                or obj.sender == request.user
            )
        return False