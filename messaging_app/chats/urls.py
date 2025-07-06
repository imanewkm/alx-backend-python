from django.urls import path, include
from rest_framework import routers
from .views import ConversationViewSet, MessageViewSet, UserViewSet, HealthCheckViewSet
from rest_framework_nested.routers import NestedDefaultRouter

router = routers.DefaultRouter()

router.register(r'conversations', ConversationViewSet, basename='conversation')

# Create a nested router for messages under conversations
nested_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
nested_router.register(r'messages', MessageViewSet, basename='conversation-messages')
"""
class HealthCheckViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def health(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
"""
urlpatterns = [
    path('', include(router.urls)),
    path('', include(nested_router.urls)),
    path('register/', UserViewSet.as_view({'post': 'create'}), name='user-register'),
    path('health/', HealthCheckViewSet.as_view({'get': 'health'}), name='health-check'),
]