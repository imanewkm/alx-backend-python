from django.db import models

class UnreadMessagesManager(models.Manager):
    """
    Custom manager that filters unread messages for a specific user.
    """
    def filter_unread(self):
        return self.filter(unread=True)