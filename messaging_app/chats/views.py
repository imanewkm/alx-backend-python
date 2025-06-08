from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation
from .pagination import MessagePagination
from .filters import MessageFilter
from rest_framework.status import HTTP_403_FORBIDDEN

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [filters.SearchFilter]
    search_fields = ['participants__email', 'participants__first_name', 'participants__last_name']

    def create(self, request, *args, **kwargs):
        participants = request.data.get('participants', [])
        if len(participants) < 2:
            return Response({'detail': 'A conversation must have at least two participants.'},
                            status=status.HTTP_400_BAD_REQUEST)
        conversation = Conversation.objects.create()
        conversation.participants.set(participants)
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        if request.user not in conversation.participants.all():
            return Response({'detail': 'You are not a participant of this conversation.'}, status=HTTP_403_FORBIDDEN)
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                sender=request.user,
                conversation=conversation
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        # Only return conversations the user participates in
        return Conversation.objects.filter(participants=self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = MessageFilter
    pagination_class = MessagePagination
    search_fields = ['message_body', 'sender__email', 'conversation__conversation_id']

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def get_queryset(self):
        # Only return messages from conversations the user participates in
        return Message.objects.filter(conversation__participants=self.request.user)
