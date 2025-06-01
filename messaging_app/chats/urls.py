from django.urls import path, include
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

# Create a router and register our viewsets
router = routers.DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'users', views.UserViewSet, basename='user')

# Create a nested router for messages under conversations
nested_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
nested_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

# The API URLs are now determined automatically by the router
urlpatterns = router.urls + nested_router.urls
