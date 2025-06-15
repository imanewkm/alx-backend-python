"""
Views for the messaging app - Enhanced with User Deletion

This module provides views for:
- Message edit history display
- User account deletion with data cleanup
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_page
from django.urls import reverse
from django.utils import timezone
from .models import Message, MessageHistory, Conversation, Notification
from django.contrib.auth import get_user_model
import json

User = get_user_model()


@login_required
def message_edit_history(request, message_id):
    """
    Display the edit history for a specific message.
    
    This view shows all previous versions of a message, allowing users
    to view how the message content has changed over time.
    """
    message = get_object_or_404(Message, message_id=message_id)
    
    # Check if user has permission to view this message
    if not (message.sender == request.user or 
            message.receiver == request.user or 
            request.user in message.conversation.participants.all()):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get edit history
    edit_history = message.get_edit_history()
    edit_summary = message.get_edit_summary()
    
    context = {
        'message': message,
        'edit_history': edit_history,
        'edit_summary': edit_summary,
        'original_content': message.get_original_content(),
        'edit_count': message.get_edit_count(),
    }
    
    return render(request, 'messaging/message_edit_history.html', context)


@login_required
def message_edit_history_json(request, message_id):
    """
    Return message edit history as JSON for AJAX requests.
    """
    message = get_object_or_404(Message, message_id=message_id)
    
    # Check permissions
    if not (message.sender == request.user or 
            message.receiver == request.user or 
            request.user in message.conversation.participants.all()):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    edit_summary = message.get_edit_summary()
    
    return JsonResponse({
        'message_id': str(message.message_id),
        'current_content': message.content,
        'is_edited': message.edited,
        'edit_count': edit_summary['edit_count'],
        'last_edited': edit_summary['last_edited'].isoformat() if edit_summary['last_edited'] else None,
        'original_content': edit_summary['original_content'],
        'edit_history': [
            {
                'history_id': str(history['history_id']),
                'old_content': history['old_content'],
                'edited_at': history['edited_at'].isoformat(),
            }
            for history in edit_summary['edit_history']
        ]
    })


@login_required
def conversation_with_edit_history(request, conversation_id):
    """
    Display a conversation with edit history indicators for messages.
    """
    conversation = get_object_or_404(Conversation, conversation_id=conversation_id)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get messages with edit information
    messages = conversation.messages.annotate(
        edit_count=Count('history')
    ).select_related('sender', 'receiver').prefetch_related('history')
    
    # Paginate messages
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'conversation': conversation,
        'messages': page_obj,
        'participants': conversation.participants.all(),
    }
    
    return render(request, 'messaging/conversation_with_history.html', context)


@login_required
def recent_edits_dashboard(request):
    """
    Dashboard showing recent message edits across all conversations
    where the user is a participant.
    """
    # Get user's conversations
    user_conversations = request.user.messaging_conversations.all()
    
    # Get recent edits in user's conversations
    recent_edits = MessageHistory.get_recent_edits(days=7).filter(
        message__conversation__in=user_conversations
    ).select_related('message', 'message__sender', 'message__conversation')
    
    # Get most edited messages in user's conversations
    most_edited = MessageHistory.get_most_edited_messages(limit=10).filter(
        conversation__in=user_conversations
    )
    
    # Paginate recent edits
    paginator = Paginator(recent_edits, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'recent_edits': page_obj,
        'most_edited_messages': most_edited,
        'total_conversations': user_conversations.count(),
    }
    
    return render(request, 'messaging/recent_edits_dashboard.html', context)


def message_edit_preview(request, message_id):
    """
    AJAX endpoint to get a quick preview of message edit history.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    message = get_object_or_404(Message, message_id=message_id)
    
    # Check permissions
    if not (message.sender == request.user or 
            message.receiver == request.user or 
            request.user in message.conversation.participants.all()):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if not message.edited:
        return JsonResponse({
            'is_edited': False,
            'message': 'This message has not been edited'
        })
    
    latest_history = message.get_edit_history().first()
    
    return JsonResponse({
        'is_edited': True,
        'edit_count': message.get_edit_count(),
        'last_edited': latest_history.edited_at.isoformat() if latest_history else None,
        'latest_old_content': latest_history.get_content_preview(100) if latest_history else None,
        'current_content_preview': message.content[:100] + "..." if len(message.content) > 100 else message.content,
    })


@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def delete_user_account(request):
    """
    View to allow a user to delete their account.
    
    This view handles both GET (show confirmation page) and POST (perform deletion).
    When a user deletes their account, the post_delete signal will automatically
    clean up all related data including messages, notifications, and message histories.
    """
    user = request.user
    
    if request.method == 'GET':
        # Show confirmation page with user's data summary
        context = get_user_deletion_context(user)
        return render(request, 'messaging/delete_account_confirmation.html', context)
    
    elif request.method == 'POST':
        # Verify user confirmation
        confirmation = request.POST.get('confirmation', '').strip().lower()
        expected_confirmation = 'delete my account'
        
        if confirmation != expected_confirmation:
            messages.error(request, 'Please type "delete my account" to confirm deletion.')
            context = get_user_deletion_context(user)
            return render(request, 'messaging/delete_account_confirmation.html', context)
        
        # Store user info for logging before deletion
        user_info = {
            'user_id': str(user.user_id),
            'email': user.email,
            'username': user.username,
            'deletion_timestamp': timezone.now().isoformat()
        }
        
        try:
            # The post_delete signal will handle all the cleanup automatically
            user_email = user.email
            logout(request)  # Log out the user before deletion
            
            # Delete the user - this triggers the post_delete signal
            user.delete()
            
            # Success message for the deletion confirmation page
            return render(request, 'messaging/account_deleted_success.html', {
                'user_email': user_email,
                'deletion_info': user_info
            })
            
        except Exception as e:
            messages.error(request, f'An error occurred while deleting your account: {str(e)}')
            context = get_user_deletion_context(user)
            return render(request, 'messaging/delete_account_confirmation.html', context)


def get_user_deletion_context(user):
    """
    Get context data for user deletion confirmation page.
    
    Args:
        user: The user who wants to delete their account
        
    Returns:
        dict: Context data showing what will be deleted
    """
    # Count user's data that will be deleted
    sent_messages_count = Message.objects.filter(sender=user).count()
    received_messages_count = Message.objects.filter(receiver=user).count()
    conversations_count = user.messaging_conversations.count()
    notifications_count = Notification.objects.filter(user=user).count()
    
    # Get edit history count for messages sent by user
    edit_history_count = MessageHistory.objects.filter(message__sender=user).count()
    
    # Get recent activity
    recent_messages = Message.objects.filter(sender=user).order_by('-timestamp')[:5]
    recent_conversations = user.messaging_conversations.order_by('-updated_at')[:3]
    
    return {
        'user': user,
        'deletion_summary': {
            'sent_messages_count': sent_messages_count,
            'received_messages_count': received_messages_count,
            'conversations_count': conversations_count,
            'notifications_count': notifications_count,
            'edit_history_count': edit_history_count,
            'total_data_points': (
                sent_messages_count + received_messages_count + 
                notifications_count + edit_history_count
            )
        },
        'recent_activity': {
            'recent_messages': recent_messages,
            'recent_conversations': recent_conversations,
        }
    }


@login_required
def user_deletion_preview(request):
    """
    AJAX endpoint to preview what data will be deleted when user deletes account.
    """
    user = request.user
    context = get_user_deletion_context(user)
    
    return JsonResponse({
        'user_id': str(user.user_id),
        'email': user.email,
        'deletion_summary': context['deletion_summary'],
        'message': f"Deleting your account will remove {context['deletion_summary']['total_data_points']} data points."
    })


@login_required
def export_user_data(request):
    """
    Allow user to export their data before deletion.
    
    This provides a JSON export of all user's messages, conversations, and notifications
    for backup purposes before account deletion.
    """
    user = request.user
    
    # Collect all user data
    user_data = {
        'user_info': {
            'user_id': str(user.user_id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
            'export_timestamp': timezone.now().isoformat()
        },
        'sent_messages': [],
        'received_messages': [],
        'conversations': [],
        'notifications': [],
        'message_edit_history': []
    }
    
    # Export sent messages
    for message in Message.objects.filter(sender=user).select_related('receiver', 'conversation'):
        user_data['sent_messages'].append({
            'message_id': str(message.message_id),
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'receiver': message.receiver.email if message.receiver else None,
            'conversation_id': str(message.conversation.conversation_id),
            'edited': message.edited,
            'read': message.read
        })
    
    # Export received messages
    for message in Message.objects.filter(receiver=user).select_related('sender', 'conversation'):
        user_data['received_messages'].append({
            'message_id': str(message.message_id),
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'sender': message.sender.email,
            'conversation_id': str(message.conversation.conversation_id),
            'edited': message.edited,
            'read': message.read
        })
    
    # Export conversations
    for conversation in user.messaging_conversations.all():
        participants = [p.email for p in conversation.participants.all()]
        user_data['conversations'].append({
            'conversation_id': str(conversation.conversation_id),
            'participants': participants,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'message_count': conversation.messages.count()
        })
    
    # Export notifications
    for notification in Notification.objects.filter(user=user).select_related('message'):
        user_data['notifications'].append({
            'notification_id': str(notification.notification_id),
            'notification_type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'message_id': str(notification.message.message_id),
            'message_content': notification.message.content[:100]
        })
    
    # Export message edit history for user's messages
    for history in MessageHistory.objects.filter(message__sender=user).select_related('message'):
        user_data['message_edit_history'].append({
            'history_id': str(history.history_id),
            'message_id': str(history.message.message_id),
            'old_content': history.old_content,
            'edited_at': history.edited_at.isoformat()
        })
    
    # Create HTTP response with JSON data
    response = HttpResponse(
        json.dumps(user_data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="user_data_export_{user.email}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response


@login_required 
def account_settings(request):
    """
    Account settings page with deletion option.
    """
    user = request.user
    context = get_user_deletion_context(user)
    
    return render(request, 'messaging/account_settings.html', context)
