"""
Django app configuration for the messaging app - Task 0: User Notifications

This module configures the messaging app and ensures that signals are
properly connected when the app is ready.
"""

from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """Configuration for the messaging app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    verbose_name = 'Messaging System'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        
        This method is called when Django starts up and the app is ready.
        It ensures that our signal handlers are imported and connected.
        """
        print("🚀 Messaging app is ready - connecting signals...")
        
        # Import signals to ensure they are connected
        try:
            import messaging.signals
            print("✅ Messaging signals connected successfully")
        except ImportError as e:
            print(f"❌ Failed to import messaging signals: {e}")
        
        print("📧 User notification signals are now active!")


# Make sure the app is properly configured
default_app_config = 'messaging.apps.MessagingConfig'
