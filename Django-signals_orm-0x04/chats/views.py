from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Prefetch
from django.db import models
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import Conversation, Message, Notification, MessageHistory
from .serializers import (
    ConversationSerializer, 
    ConversationListSerializer,
    MessageSerializer, 
    UserSerializer
)
from .permissions import IsParticipantOfConversation, IsAuthenticatedParticipant, CanCreateMessage
from .filters import MessageFilter, ConversationFilter, UserFilter
from .pagination import MessagePagination, ConversationPagination, UserPagination

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for listing, retrieving, and deleting users."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'user_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ['username']
    pagination_class = UserPagination
    
    @action(detail=True, methods=['delete'])
    def delete_user(self, request, user_id=None):
        """Delete a user account and trigger cleanup signals."""
        try:
            user = self.get_object()
            if user != request.user and not request.user.is_superuser:
                return Response(
                    {'error': 'You can only delete your own account'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            user_email = user.email
            user.delete()  # This will trigger the post_delete signal
            
            return Response(
                {'message': f'User {user_email} deleted successfully'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing conversations."""
    permission_classes = [IsParticipantOfConversation]
    lookup_field = 'conversation_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ConversationFilter
    search_fields = ['participants__username', 'participants__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    pagination_class = ConversationPagination
    
    def get_queryset(self):
        """Return conversations for the current user with optimized queries."""
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender')
                                       .prefetch_related('replies')
                                       .order_by('-sent_at')[:10]
            )
        ).select_related().order_by('-updated_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new conversation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add the current user to participants if not already included
        participant_ids = request.data.get('participant_ids', [])
        if str(request.user.user_id) not in [str(pid) for pid in participant_ids]:
            participant_ids.append(str(request.user.user_id))
        
        # Check if conversation already exists with these participants
        if len(participant_ids) == 2:
            existing_conversation = Conversation.objects.filter(
                participants__user_id__in=participant_ids
            ).annotate(
                participant_count=models.Count('participants')
            ).filter(participant_count=2)
            
            for conv in existing_conversation:
                if set(conv.participants.values_list('user_id', flat=True)) == set(participant_ids):
                    return Response(
                        ConversationSerializer(conv).data,
                        status=status.HTTP_200_OK
                    )
        
        # Create new conversation
        validated_data = serializer.validated_data.copy()
        validated_data['participant_ids'] = participant_ids
        conversation = serializer.create(validated_data)
        
        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, conversation_id=None):
        """Add a participant to the conversation."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(user_id=user_id)
            conversation.participants.add(user)
            return Response(
                {'message': f'User {user.email} added to conversation'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, conversation_id=None):
        """Remove a participant from the conversation."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(user_id=user_id)
            if user == request.user:
                return Response(
                    {'error': 'Cannot remove yourself from conversation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            conversation.participants.remove(user)
            return Response(
                {'message': f'User {user.email} removed from conversation'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing messages."""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticatedParticipant]
    lookup_field = 'message_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MessageFilter
    search_fields = ['message_body', 'sender__username', 'sender__email']
    ordering_fields = ['sent_at', 'message_body']
    ordering = ['-sent_at']
    pagination_class = MessagePagination
    
    def get_queryset(self):
        """Return messages for conversations the user participates in with optimized queries."""
        user_conversations = Conversation.objects.filter(
            participants=self.request.user
        ).only('conversation_id')
        
        return Message.objects.filter(
            conversation__in=user_conversations
        ).select_related('sender', 'conversation', 'parent_message') \
         .prefetch_related(
             Prefetch(
                 'replies',
                 queryset=Message.objects.select_related('sender')
                                       .only('message_id', 'message_body', 'sent_at', 'sender__first_name', 'sender__last_name')
             ),
             'history'
         )
    
    def create(self, request, *args, **kwargs):
        """Create a new message."""
        # Automatically set the sender to the current user
        data = request.data.copy()
        data['sender_id'] = str(request.user.user_id)
        
        # Validate that the user is a participant in the conversation
        conversation_id = data.get('conversation')
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    participants=request.user
                )
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'You are not a participant in this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        
        # Update conversation's updated_at timestamp
        conversation.save()
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
    
    @method_decorator(cache_page(60))  # Cache for 60 seconds
    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        """Get messages for a specific conversation with caching."""
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response(
                {'error': 'conversation_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = Conversation.objects.get(
                conversation_id=conversation_id,
                participants=request.user
            )
            messages = self.get_queryset().filter(conversation=conversation)
            page = self.paginate_queryset(messages)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread messages for the current user using custom manager."""
        conversation_id = request.query_params.get('conversation_id')
        
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    participants=request.user
                )
                unread_messages = Message.unread.for_user(request.user).filter(
                    conversation=conversation
                )
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            unread_messages = Message.unread.for_user(request.user)
        
        page = self.paginate_queryset(unread_messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(unread_messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Mark messages as read for the current user."""
        conversation_id = request.data.get('conversation_id')
        
        try:
            conversation = None
            if conversation_id:
                conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    participants=request.user
                )
            
            # Use custom manager to mark messages as read
            count = Message.unread.mark_as_read(request.user, conversation)
            
            return Response({
                'message': f'Marked {count} messages as read',
                'count': count
            })
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def threaded_replies(self, request, message_id=None):
        """Get threaded replies for a specific message."""
        try:
            parent_message = self.get_object()
            
            # Recursive query to get all replies in threaded format
            def get_replies_recursive(message, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                
                replies = Message.objects.filter(
                    parent_message=message
                ).select_related('sender').prefetch_related('replies')
                
                result = []
                for reply in replies:
                    reply_data = {
                        'message_id': reply.message_id,
                        'message_body': reply.message_body,
                        'sender': {
                            'user_id': reply.sender.user_id,
                            'first_name': reply.sender.first_name,
                            'last_name': reply.sender.last_name,
                        },
                        'sent_at': reply.sent_at,
                        'depth': depth + 1,
                        'replies': get_replies_recursive(reply, depth + 1, max_depth)
                    }
                    result.append(reply_data)
                
                return result
            
            # Check if user is participant in the conversation
            if not parent_message.conversation.participants.filter(
                user_id=request.user.user_id
            ).exists():
                return Response(
                    {'error': 'You are not a participant in this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            threaded_replies = get_replies_recursive(parent_message)
            
            return Response({
                'parent_message': {
                    'message_id': parent_message.message_id,
                    'message_body': parent_message.message_body,
                    'sender': {
                        'user_id': parent_message.sender.user_id,
                        'first_name': parent_message.sender.first_name,
                        'last_name': parent_message.sender.last_name,
                    },
                    'sent_at': parent_message.sent_at,
                },
                'threaded_replies': threaded_replies,
                'total_replies': len(threaded_replies)
            })
            
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def edit_history(self, request, message_id=None):
        """Get edit history for a specific message."""
        try:
            message = self.get_object()
            
            # Check if user is participant in the conversation
            if not message.conversation.participants.filter(
                user_id=request.user.user_id
            ).exists():
                return Response(
                    {'error': 'You are not a participant in this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get message history
            history = MessageHistory.objects.filter(
                message=message
            ).order_by('-edited_at')
            
            history_data = []
            for entry in history:
                history_data.append({
                    'history_id': entry.history_id,
                    'old_content': entry.old_content,
                    'edited_at': entry.edited_at,
                })
            
            return Response({
                'message_id': message.message_id,
                'current_content': message.message_body,
                'edited': message.edited,
                'edit_history': history_data,
                'total_edits': len(history_data)
            })
            
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            return Response(serializer.data)
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'},
                status=status.HTTP_404_NOT_FOUND
            )
