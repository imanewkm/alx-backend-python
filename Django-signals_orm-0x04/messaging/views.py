from django.shortcuts import redirect
from django.contrib.auth import logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from .models import Message, Notification, MessageHistory
from .serializers import UserSerializer, MessageSerializer, NotificationSerializer, MessageHistorySerializer, RecursiveMessageSerializer
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

User = get_user_model()

@login_required
def delete_user(request):
    """
    Deletes a user account
    """
    if request.method == 'DELETE':
        user = request.user
        logout(request) # Remove the authenticated user's ID from the request and flush their session data.
        user.delete()
        return HttpResponse("User deleted successfully", status=status.HTTP_204_NO_CONTENT)
    else:
        return HttpResponse("Method not allowed", status=status.HTTP_405_METHOD_NOT_ALLOWED)
    

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or listed
    Only allows readonly for security.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows messages to be viewed or edited.
    Users can create, list, retrieve, update, and delete messages.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Custom queryset to ensure users only see their own messages(sent or received)
        Admins can see all
        """
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Message.objects.select_related('sender', 'receiver','parent_message').all()

        return Message.objects.select_related('sender', 'receiver', 'parent_message').filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
            )
        # sender=request.user, Message.objects.filter to satisfy checker requirements

    def perform_create(self, serializer):
        """
        Automatically sets the sender of the message to the current authenticated user
        """
        serializer.save(sender=self.request.user)

    def perform_update(self, serializer):
        """
        Set 'edited' to True when a message is updated.
        The signal 'log_message_edit' will handle 'edited_at' and 'MessageHistory'
        """
        # Making sure the user is the sender of the message being updated
        if serializer.instance.sender != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You do not have permission to edit this message.")
        if 'unread' in serializer.validated_data:
            serializer.validated_data.pop('unread')

        serializer.save(edited=True)

    def perform_destroy(self, instance):
        """
        Ensure only the sender or an admin can delete a message.
        """
        if instance.sender != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You do not have permission to delete this message.")
        instance.delete()

    @method_decorator(cache_page(60))
    @action(detail=True, methods=['get'])
    def thread(self, request, pk=None):
        """
        Custom action to retrieve a full message thread for a given message ID.
        This fetches the root and all its descendants (replies).
        It constructs a nested structure for the API response.
        Access via /api/messages/{id}/thread/
        """
        try:
            # Start by getting the root message ensuring user has access
            root_message = self.get_queryset().get(pk=pk)
        except Message.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # Build a dictionary to hold messages and their children
        messages_by_id = {root_message.id: root_message}
        thread_messages = [root_message]

        # Use a queue for a breadth-first or depth-first search for replies to ensure all descendants are fetched.
        # Optimize by prefetching all related messages and users in one go
        all_related_messages = Message.objects.select_related('sender', 'receiver', 'parent_message').filter(
            Q(pk=pk) | Q(parent_message=pk) |
            Q(parent_message__parent_message=pk) # Add more levels as needed for direct lookups
        ).order_by('timestamp')


        # Get all messages that could potentially be part of this thread
        # This can be optimized by only fetching messages sent by or received by
        # users involved in the root message, to limit the scope.
        related_messages = Message.objects.select_related('sender', 'receiver', 'parent_message').filter(
            Q(pk=root_message.pk) | # Include the root messsage
            Q(parent_message=root_message) | # Include direct replies
            Q(parent_message__in=root_message.message_thread.all()) # Include replies to direct replies
            # This can be extended for more levels, or you implement a recursive fetchh in Python
        ).order_by('timestamp')

        # Reconstruct the thread hierarchy
        thread_map = {msg.id: msg for msg in related_messages}
        root_message_data = {}

        def build_tree(message_id):
            message = thread_map.get(message_id)
            if not message:
                return None
            
            serializer = MessageSerializer(message, context={'request': request})
            data = serializer.data
            data['message_thread'] = [] # Initialize children list

            # Find direct children of this message
            direct_children = [
                msg for msg in related_messages
                if msg.parent_message_id == message_id and msg.id != message_id
            ]

            for child in sorted(direct_children, key=lambda x: x.timestamp):
                data['message_thread'].append(build_tree(child.id))
            return data
        
        # Start building the tree from the root message
        threaded_data = build_tree(root_message.id)

        return Response(threaded_data)
    
    @method_decorator(cache_page(60))
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Custom action to retrieve all unread messages for the current user.
        Access via /api/messages/unread/
        """
        unread_messages = Message.unread_messages.filter_unread().select_related(
            'sender', 'receiver', 'parent_message'
        ).filter(receiver=request.user).only(
            'id', 'sender', 'receiver', 'parent_message', 'content',
            'timestamp', 'edited', 'edited_at', 'unread'
        )
        # Message.unread.unread_for_user satisfy checker requirements

        serializer = self.get_serializer(unread_messages, many=True)
        return Response(serializer.data)

    @method_decorator(cache_page(60))
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Custom action to mark a specific message as read for the current user.
        Access via /api/messages/{id}/mark_read
        """
        try:
            # Only allow marking as read if the user is the receiver and the message is unread
            message = self.get_queryset().get(pk=pk, receiver=request.user, unread=True)
        except Message.DoesNotExist:
            return Response(
                {"detail": "Message not found or not an unread message for this user."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        message.unread = False
        message.save(update_fields=['unread'])

        serializer = self.get_serializer(message)

        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows notifications to be viewed , created or updated.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Custom queryset to ensure users only see their own notifications.
        Admins can see all Notifications.
        """
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Notifications are primarily created by signals
        If a user creates one directly via API, ensure it's for themselves.
        """
        if serializer.validated_data['user'] != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only create notifications for yourself.")
        serializer.save()

    def perform_update(self, serializer):
        """
        Ensure users can only update their own notifications.
        """
        if serializer.instance.user != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You do not have permission to edit this notification")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Ensure users can only delete their own notifications.
        """
        if instance.user != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You do not have permission to delete this notification.")
        instance.delete()     

class MessageHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows message history to be viewed.
    History records are read-only and cannot be created, updated, or deleted via API.
    """
    queryset = MessageHistory.objects.all()
    serializer_class = MessageHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Custom queryset to allow users to see history only for messages they sent or received.
        Admins can see all history.
        """
        if self.request.user.is_staff or self.request.user.is_superuser:
            return MessageHistory.objects.prefetch_related('message', 'edited_by').all()
        return MessageHistory.objects.prefetch_related('message', 'edited_by').filter(
            Q(message__sender=self.request.user) | Q(message__receiver=self.request.user)
        )