"""
URL configuration for the messaging app - Task 1: Message Edit History

This module defines URL patterns for viewing message edit history.
"""

from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Message edit history views
    path('message/<uuid:message_id>/history/', 
         views.message_edit_history, 
         name='message_edit_history'),
    
    path('message/<uuid:message_id>/history/json/', 
         views.message_edit_history_json, 
         name='message_edit_history_json'),
    
    path('message/<uuid:message_id>/edit-preview/', 
         views.message_edit_preview, 
         name='message_edit_preview'),
    
    # Conversation views with edit history
    path('conversation/<uuid:conversation_id>/', 
         views.conversation_with_edit_history, 
         name='conversation_with_history'),
    
    # Dashboard for recent edits
    path('dashboard/recent-edits/', 
         views.recent_edits_dashboard, 
         name='recent_edits_dashboard'),
    
    # Task 2: User deletion and account management URLs
    path('account/settings/', 
         views.account_settings, 
         name='account_settings'),
    
    path('account/delete/', 
         views.delete_user_account, 
         name='delete_user_account'),
    
    path('account/delete/preview/', 
         views.user_deletion_preview, 
         name='user_deletion_preview'),
    
    path('account/export-data/', 
         views.export_user_data, 
         name='export_user_data'),
]
