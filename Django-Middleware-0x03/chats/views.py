from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from .models import User, Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation
from .pagination import MessagesPagination


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsParticipantOfConversation, IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['created_at']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants').order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        participant_ids = request.data.get('participant_ids', [])
        if str(request.user.user_id) not in [str(pid) for pid in participant_ids]:
            participant_ids.append(request.user.user_id)
        
        conversation = Conversation.objects.create()
        participants = User.objects.filter(user_id__in=participant_ids)
        conversation.participants.set(participants)
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsParticipantOfConversation, IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['conversation__conversation_id', 'sent_at']
    search_fields = ['message_body']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']
    pagination_class = MessagesPagination
    
    def get_queryset(self):
        user_conversations = Conversation.objects.filter(
            participants=self.request.user
        ).values_list('conversation_id', flat=True)
        
        return Message.objects.filter(
            conversation__conversation_id__in=user_conversations
        ).select_related('sender', 'conversation').order_by('-sent_at')
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['sender_id'] = request.user.user_id
        
        conversation_id = data.get('conversation_id')
        try:
            conversation = Conversation.objects.get(conversation_id=conversation_id)
            if not conversation.participants.filter(user_id=request.user.user_id).exists():
                return Response(
                    {'error': 'You are not a participant in this conversation.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)