# Messaging App API - Postman Collection

This directory contains Postman collection and environment files for testing the Django Messaging App API.

## Files

- `messaging-app-api.postman_collection.json` - Complete API collection with all endpoints
- `messaging-app-environment.postman_environment.json` - Environment variables for the collection

## Setup Instructions

1. **Start the Django Server**
   ```bash
   cd messaging_app
   python manage.py runserver
   ```

2. **Import into Postman**
   - Open Postman
   - Click "Import" 
   - Select both JSON files from this directory
   - The collection and environment will be imported

3. **Select Environment**
   - In Postman, select "Messaging App Environment" from the environment dropdown

## Testing Flow

### 1. Authentication Testing

1. **Register a User** - Creates a new user and automatically sets tokens
2. **Login User** - Login with existing credentials and get tokens
3. **Get User Profile** - Test authenticated endpoint
4. **Refresh Token** - Test token refresh functionality
5. **Logout User** - Test logout functionality

### 2. Basic API Testing

1. **List Users** - Get all users (requires authentication)
2. **Create Conversation** - Create a new conversation
3. **List Conversations** - Get user's conversations
4. **Create Message** - Send a message in a conversation
5. **List Messages** - Get messages with pagination

### 3. Permission Testing

1. **Access Conversations Without Token** - Should return 401 Unauthorized
2. **Access Messages Without Token** - Should return 401 Unauthorized
3. **Try to access other users' conversations** - Should return 403 Forbidden

### 4. Advanced Features Testing

1. **Pagination** - Test different page sizes and page numbers
2. **Filtering** - Filter messages by sender, content, time range
3. **Search** - Search users and conversations
4. **Object-level Permissions** - Only conversation participants can access messages

## API Endpoints Covered

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - Logout user
- `GET /api/auth/profile/` - Get current user profile

### Users
- `GET /api/users/` - List users (with search and pagination)
- `GET /api/users/{user_id}/` - Get specific user

### Conversations
- `GET /api/conversations/` - List user's conversations
- `POST /api/conversations/` - Create new conversation
- `GET /api/conversations/{conversation_id}/` - Get conversation details
- `POST /api/conversations/{conversation_id}/add_participant/` - Add participant

### Messages
- `GET /api/messages/` - List messages (with filtering and pagination)
- `POST /api/messages/` - Create new message
- `GET /api/messages/{message_id}/` - Get specific message
- `PATCH /api/messages/{message_id}/` - Update message
- `DELETE /api/messages/{message_id}/` - Delete message
- `GET /api/messages/by_conversation/` - Get messages by conversation

## Authentication

The API uses JWT (JSON Web Token) authentication. After registering or logging in, the access token is automatically stored in the environment variable and used for subsequent requests.

### Token Lifecycle
- **Access Token**: Valid for 60 minutes
- **Refresh Token**: Valid for 7 days
- **Auto Refresh**: Refresh tokens are rotated on use

## Filtering and Pagination

### Messages Filtering
- `conversation` - Filter by conversation ID
- `sender` - Filter by sender user ID
- `sender_username` - Filter by sender username (contains)
- `message_body` - Filter by message content (contains)
- `sent_at_after` - Messages sent after datetime
- `sent_at_before` - Messages sent before datetime

### Pagination Parameters
- `page` - Page number (default: 1)
- `page_size` - Number of items per page (default: 20, max: 100)

### Example Filtered Request
```
GET /api/messages/?sender={{user_id}}&page=1&page_size=10&message_body=hello
```

## Security Features Tested

1. **JWT Authentication** - All protected endpoints require valid JWT token
2. **Object-level Permissions** - Users can only access their own conversations and messages
3. **Participant Validation** - Only conversation participants can send/view messages
4. **Token Blacklisting** - Logout invalidates refresh tokens
5. **Token Rotation** - Refresh tokens are rotated for security

## Expected Response Codes

- `200 OK` - Successful GET, PATCH requests
- `201 Created` - Successful POST requests
- `204 No Content` - Successful DELETE requests
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found

## Variables Auto-Set

The collection automatically extracts and sets these variables from responses:
- `access_token` - JWT access token
- `refresh_token` - JWT refresh token
- `user_id` - Current user's ID
- `conversation_id` - Created conversation ID
- `message_id` - Created message ID

This allows for seamless testing flow where you can run requests in sequence without manually copying IDs.
