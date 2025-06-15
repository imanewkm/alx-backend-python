from django.db import models

class UnreadMessagesManager(models.Manager):
    """Custom manager to filter unread messages for a user."""

    def unread_for_user(self, user):
        """Get unread messages for a specific user."""
        # Ensure this method aligns with how conversations and read status are structured.
        # This is a common pattern, adjust field names if your model differs.
        return self.get_queryset().filter(
            conversation__participants=user,  # Assumes conversation has participants
            read=False
        ).exclude(sender=user).select_related('sender', 'conversation')

    def mark_as_read(self, user, conversation=None):
        """Mark messages as read for a user, optionally in a specific conversation."""
        queryset = self.unread_for_user(user)
        if conversation:
            queryset = queryset.filter(conversation=conversation)
        return queryset.update(read=True)