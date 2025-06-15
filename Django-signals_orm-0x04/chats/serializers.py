from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 
                 'full_name', 'phone_number', 'date_of_birth', 'created_at']
        read_only_fields = ['user_id', 'created_at']
    
    def get_full_name(self, obj):
        """Return the full name of the user."""
        return f"{obj.first_name} {obj.last_name}".strip()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model with sender details."""
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True)
    sender_name = serializers.CharField(read_only=True)
    conversation_title = serializers.CharField(read_only=True)
    
    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'sender_id', 'sender_name', 
                 'conversation', 'conversation_title', 'message_body', 'sent_at']
        read_only_fields = ['message_id', 'sent_at', 'sender_name', 'conversation_title']
    
    def to_representation(self, instance):
        """Add computed fields to the serialized representation."""
        data = super().to_representation(instance)
        if instance.sender:
            data['sender_name'] = f"{instance.sender.first_name} {instance.sender.last_name}"
        if instance.conversation:
            # Create a simple conversation title based on participants
            participants = instance.conversation.participants.all()[:2]
            if participants:
                participant_names = [f"{p.first_name} {p.last_name}" for p in participants]
                data['conversation_title'] = ", ".join(participant_names)
        return data
    
    def create(self, validated_data):
        # Remove sender_id from validated_data and use it to set sender
        sender_id = validated_data.pop('sender_id')
        try:
            sender = User.objects.get(user_id=sender_id)
            validated_data['sender'] = sender
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid sender_id")
        
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model with participants and messages."""
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    messages = MessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    participant_names = serializers.CharField(read_only=True)
    conversation_title = serializers.CharField(read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'participant_ids', 
                 'participant_names', 'conversation_title', 'messages', 
                 'last_message', 'created_at', 'updated_at']
        read_only_fields = ['conversation_id', 'created_at', 'updated_at', 
                           'participant_names', 'conversation_title']
    
    def to_representation(self, instance):
        """Add computed fields to the serialized representation."""
        data = super().to_representation(instance)
        participants = instance.participants.all()
        if participants:
            participant_names = [f"{p.first_name} {p.last_name}" for p in participants]
            data['participant_names'] = ", ".join(participant_names)
            data['conversation_title'] = f"Conversation with {', '.join(participant_names[:2])}"
            if len(participants) > 2:
                data['conversation_title'] += f" and {len(participants) - 2} others"
        return data
    
    def get_last_message(self, obj):
        """Get the most recent message in the conversation."""
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = super().create(validated_data)
        
        # Add participants to the conversation
        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)
        
        return conversation


class ConversationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing conversations."""
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    participant_names = serializers.CharField(read_only=True)
    last_message_preview = serializers.CharField(read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'participant_names',
                 'last_message', 'last_message_preview', 'message_count', 
                 'created_at', 'updated_at']
        read_only_fields = ['participant_names', 'last_message_preview']
    
    def to_representation(self, instance):
        """Add computed fields to the serialized representation."""
        data = super().to_representation(instance)
        participants = instance.participants.all()
        if participants:
            participant_names = [f"{p.first_name} {p.last_name}" for p in participants]
            data['participant_names'] = ", ".join(participant_names)
        
        # Add last message preview
        last_message = instance.messages.last()
        if last_message:
            preview = last_message.message_body[:50]
            if len(last_message.message_body) > 50:
                preview += "..."
            data['last_message_preview'] = preview
        
        return data
    
    def get_last_message(self, obj):
        """Get the most recent message in the conversation."""
        last_message = obj.messages.last()
        if last_message:
            return {
                'message_body': last_message.message_body,
                'sender': last_message.sender.first_name + ' ' + last_message.sender.last_name,
                'sent_at': last_message.sent_at
            }
        return None
    
    def get_message_count(self, obj):
        """Get the total number of messages in the conversation."""
        return obj.messages.count()
