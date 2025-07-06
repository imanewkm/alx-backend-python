from rest_framework import serializers
from .models import User, Conversation, Message
from django.contrib.auth.hashers import make_password

def validate_email(value):
    if User.objects.filter(email=value).exists():
        raise serializers.ValidationError("Email already exists")
    return value

class UserSerializer(serializers.ModelSerializer):
    email = serializers.CharField(validators=[validate_email])

    class Meta:
        model = User
        fields = ['user_id', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'created_at', 'password']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return User.objects.create(**validated_data)

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    conversation = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'conversation', 'message_body', 'sent_at']

# StringRelatedField returns the string representation of the related field
class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.StringRelatedField(many=True)
    messages = MessageSerializer(many=True, read_only=True) #nested messages

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'participants', 'messages', 'created_at']