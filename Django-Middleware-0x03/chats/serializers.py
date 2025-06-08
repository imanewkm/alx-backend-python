from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    user_id = serializers.UUIDField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'email', 'first_name', 'last_name', 'phone_number',
            'full_name', 'is_active', 'date_joined', 'last_login', 
            'password', 'confirm_password'
        ]
        read_only_fields = ['user_id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        """Validate password confirmation."""
        if 'password' in attrs and 'confirm_password' in attrs:
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Update user instance."""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for the Conversation model."""
    
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids',
            'participant_count', 'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at']

    def get_participant_count(self, obj):
        """Return number of participants in conversation."""
        return obj.participants.count()
    
    def validate_participant_ids(self, value):
        """Validate participant IDs."""
        if not value:
            raise serializers.ValidationError("At least one participant is required.")
        
        if len(value) < 2:
            raise serializers.ValidationError("A conversation must have at least 2 participants.")
        
        return value

    def create(self, validated_data):
        """Create conversation with participants."""
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)
        
        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)
        
        return conversation


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the Message model."""
    
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    conversation_id = serializers.UUIDField(write_only=True)
    message_preview = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation_id',
            'message_body', 'message_preview', 'sent_at'
        ]
        read_only_fields = ['message_id', 'sent_at']

    def get_message_preview(self, obj):
        """Return a preview of the message."""
        return obj.message_body[:100] + "..." if len(obj.message_body) > 100 else obj.message_body

    def validate_conversation_id(self, value):
        """Validate conversation exists."""
        try:
            conversation = Conversation.objects.get(conversation_id=value)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversation not found.")
        
        return value

    def create(self, validated_data):
        """Create message with proper relationships."""
        conversation_id = validated_data.pop('conversation_id')
        sender_id = validated_data.pop('sender_id', None)
        
        conversation = Conversation.objects.get(conversation_id=conversation_id)
        sender = None
        
        if sender_id:
            try:
                sender = User.objects.get(user_id=sender_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("Sender not found.")
        
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            **validated_data
        )
        return message