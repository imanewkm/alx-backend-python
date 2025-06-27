from django.contrib import admin
from .models import CustomUser, Conversation, Message
from django.contrib.auth.admin import UserAdmin

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Conversation)
admin.site.register(Message)
