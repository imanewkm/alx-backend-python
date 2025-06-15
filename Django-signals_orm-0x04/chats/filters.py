import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Message, Conversation, User


class MessageFilter(filters.FilterSet):
    """Filter for messages with various criteria."""
    
    conversation = filters.UUIDFilter(field_name='conversation__conversation_id')
    sender = filters.UUIDFilter(field_name='sender__user_id')
    sender_username = filters.CharFilter(field_name='sender__username', lookup_expr='icontains')
    sender_email = filters.CharFilter(field_name='sender__email', lookup_expr='icontains')
    message_body = filters.CharFilter(field_name='message_body', lookup_expr='icontains')
    sent_at_after = filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte')
    sent_at_before = filters.DateTimeFilter(field_name='sent_at', lookup_expr='lte')
    sent_at_range = filters.DateTimeFromToRangeFilter(field_name='sent_at')
    
    class Meta:
        model = Message
        fields = [
            'conversation',
            'sender',
            'sender_username', 
            'sender_email',
            'message_body',
            'sent_at_after',
            'sent_at_before',
            'sent_at_range'
        ]


class ConversationFilter(filters.FilterSet):
    """Filter for conversations with various criteria."""
    
    participant = filters.UUIDFilter(field_name='participants__user_id')
    participant_username = filters.CharFilter(field_name='participants__username', lookup_expr='icontains')
    participant_email = filters.CharFilter(field_name='participants__email', lookup_expr='icontains')
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_at_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Custom filter for conversations with specific user
    with_user = filters.UUIDFilter(method='filter_with_user')
    
    def filter_with_user(self, queryset, name, value):
        """Filter conversations that include a specific user."""
        return queryset.filter(participants__user_id=value)
    
    class Meta:
        model = Conversation
        fields = [
            'participant',
            'participant_username',
            'participant_email', 
            'created_at_after',
            'created_at_before',
            'updated_at_after',
            'updated_at_before',
            'with_user'
        ]


class UserFilter(filters.FilterSet):
    """Filter for users with various criteria."""
    
    username = filters.CharFilter(field_name='username', lookup_expr='icontains')
    email = filters.CharFilter(field_name='email', lookup_expr='icontains')
    first_name = filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    full_name = filters.CharFilter(method='filter_full_name')
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    def filter_full_name(self, queryset, name, value):
        """Filter by full name (first name + last name)."""
        return queryset.filter(
            Q(first_name__icontains=value) | 
            Q(last_name__icontains=value) |
            Q(first_name__icontains=value.split()[0] if ' ' in value else value) |
            Q(last_name__icontains=value.split()[-1] if ' ' in value else value)
        )
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'created_at_after',
            'created_at_before'
        ]
