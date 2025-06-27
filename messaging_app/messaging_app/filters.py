# chats/filters.py
from django_filters import rest_framework as filters
from chats.models import Message

class MessageFilter(filters.FilterSet):
    sender = filters.CharFilter(field_name='sender__username', lookup_expr='iexact')
    conversation = filters.UUIDFilter(field_name='conversation__id')
    start_date = filters.IsoDateTimeFilter(field_name='sent_at', lookup_expr='gte')
    end_date = filters.IsoDateTimeFilter(field_name='sent_at', lookup_expr='lte')

    class Meta:
        model = Message
        fields = ['sender', 'conversation', 'start_date', 'end_date']
