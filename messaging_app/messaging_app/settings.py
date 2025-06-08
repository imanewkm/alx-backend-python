# Authentication Configuration
LOGIN_URL = '/api/auth/login/'
LOGIN_REDIRECT_URL = '/api/chats/'
LOGOUT_REDIRECT_URL = '/api/auth/login/'

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True

# Token Authentication Configuration (for DRF)
REST_AUTH_SERIALIZERS = {
    'LOGIN_SERIALIZER': 'rest_framework.serializers.Serializer',
}

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS Configuration (if using frontend)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
