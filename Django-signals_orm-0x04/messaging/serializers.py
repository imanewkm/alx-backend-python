from rest_framework import serializers
from .models import Message, Notification, MessageHistory
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    User model serializer
    Only exposes necessary fields for API readability
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['username', 'email']

class RecursiveMessageSerializer(serializers.Serializer):
    """
    Serializer for recursize display of message threads.
    This helps in nesting replies within replies.
    """
    def to_representation(self, value):
        # Lazily import MessageSerializer to avoid circular import issues
        serializer = MessageSerializer(value, context=self.context)
        return serializer.data

class MessageSerializer(serializers.ModelSerializer):
    """
    Message model serializer
    Uses SlugRelatedField for sender and receiver for cleaner represntation
    in the brwosable API (shows username instead of ID).
    """
    sender = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    receiver = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    parent_message = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        allow_null=True,
        required=False,
        label="Reply To Message ID"
    )

    # Using SerializerMethodField to display the nested replies (children)
    # This will only be populated when explicitly fetched (e.g., in  the 'thread' action)
    message_thread = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'parent_message', 'content',
                  'timestamp', 'edited', 'edited_at', 'unread','message_thread']
        read_only_fields = ['timestamp', 'edited', 'edited_at', 'unread']

    def get_message_thread(self, obj):
        """
        Retrieves and serialises the direct replies to this message.
        This method is called when 'message_thread' is accessed in the serializer.
        """
        # Ensure we only fetch direct children and apply relevant ordering
        # For deeper recursion, limits of a different action should be condidered for performance.
        # This will be specifically populated by the custom 'thread' action in the view.
        replies = obj.message_thread.all().order_by('timestamp')
        return RecursiveMessageSerializer(replies, many=True, context=self.context).data


class NotificationSerializer(serializers.ModelSerializer):
    """
    Notification model serializer
    Links User and Message models
    """
    user = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    message = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Notification
        fields = ['id', 'detail', 'user', 'message', 'created_at', 'is_read']
        read_only_fields = ['created_at']

class MessageHistorySerializer(serializers.ModelSerializer):
    """
    MessageHistory model serializer
    Is read-only as history records shouldn't be modified
    """
    message = serializers.PrimaryKeyRelatedField(read_only=True)
    edited_by = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = MessageHistory
        fields = ['id', 'message', 'edited_by', 'old_content', 'created_at']
        read_only_fields = ['message', 'edited_by', 'old_content', 'created_at']