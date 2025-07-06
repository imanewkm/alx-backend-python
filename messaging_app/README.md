# SERIALIZERS
serializers are fundamental to the DRF, they are used to convert complex data types,
like django model instances, into native python data types that can then be easily
rendered into JSON, XML or other content types.
>>> pip install djangorestframework
```python
# settings.py
INSTALLED_APPS = [
    ...
    'rest_framework',
    ...
]
```
if you have a model named BlogPost, you can create a serializer for it by creating a new file - `serializers.py`
```python
from rest_framework import serializers
from .models import BlogPost

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = '__all__'
        # fields = ['title', 'content', 'created_at']
```
compared to fastapi, serializers are similar to pydantic models(schema).

## Using the Serializers in Views
You can use the serializer in your views to handle incoming data and provide appropriate responses. Here's an example using Django REST Framework's class-based views.

### Views Definition
```python
# views.py
from rest_framework import generics
from .models import BlogPost
from .serializers import BlogPostSerializer

class BlogPostListCreate(generics.ListCreateAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer

class BlogPostDetail(generics.RetrieveUpdateDestroyerAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
```
- The statement `queryset = BlogPost.objects.all()` means we're creating a queryset that contains all instances of the `BlogPost` model from the database.
- You can use `values` or `value_list` to filter the specific columns you want.

### Settings Up URLs
Add the URLs for the views in the urls.py
```python
# urls.py
from django.urls import path
from .views import BlogPostListCreate, BlogPostDetail

urlpatterns = [
    path('api/blogposts/', BlogPostListCreate.as_view(), name='blogpost-list-create'),
    path('api/blogposts/<int:pk>/', BlogPostDetail.as_view(), name='blogpost-detail'),
]
```
__Test the api__
>>> python manage.py runserver

__create a new blog post__
>>> curl -X POST -d "title=New Post&content=This is a new post." http://127.0.0.1:8000/api/blogposts

## Serializers and Relationships

Serializers are also used to define and manage relationships between models. This is done by using special fields in serializers, such as `PrimaryKeyRelatedField`, `StringRelatedField`, `HyperlinkedRelatedField`, and `SlugRelatedField`. These fields help you represent and handle relationships between different models in your APIs.

__MANY TO MANY RELATIONSHIP__
models `Author and Book` - An author can write multiple books, and a book can have multiple authors.

`models`
```python
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, related_name='books')
    published_date = models.DateField()

    def __str__(self):
        return self.title
```
### Serializer Definitions
Serializers for the models above, including many-to-many relationship.

```python
# serializers.py

from rest_framework import serializers
from .models import Author, Book

class AuthorSerializer(serializers.modelSerializer):
    books = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'name', 'email', 'books']

class BookSerializer(serializers.modelSerializer):
    authors = serializers.PrimaryKeyRelatedField(many=True, queryset=Author.objects.all())

    class Meta:
        model = Book
        fields = ['id', 'title', 'authors', 'published_date']
```
`Discussion`
The `authors` in `BookSerializer` has a queryset since its not readonly and the author will have to be validated unlike the `books` in the `AuthorSerializer` which is readonly. 
The `books` queryset ensures that only Valid `Author` instances are associated with a `Book`, enabling proper Validation and lookup during create or update operatins.
- The `AuthorSerializer` includes a `books` field that references the related books. This field uses `PrimaryKeyRelatedField` with `many=True` to indicate a `many-to-many` relationship.
- The `BookSerializer` includes an `authors` field that references the related authors. This field also uses
`PrmaryKeyRelatedField` with `many=True` and allows for querying related authors.

- 

- `next is to create the views to serialize and desirialize as well as the urls`


***
***
`StringRelatedField`:
- Used for the participants in ConversationSerializer and sender in MessageSerializer. This ensures that the string representation of the related model is displayed instead of its primary key.

`PrimaryKeyRelatedField`:
- Used for conversation in MessageSerializer to display only the ID of the related conversation.

`Nested Serializer`:
- In ConversationSerializer, the MessageSerializer is nested to include all messages belonging to a conversation.
***
***

***
***
`StringRelatedField`:
- Used for the participants in ConversationSerializer and sender in MessageSerializer. This ensures that the string representation of the related model is displayed instead of its primary key.

`PrimaryKeyRelatedField`:
- Used for conversation in MessageSerializer to display only the ID of the related conversation.

`Nested Serializer`:
- In ConversationSerializer, the MessageSerializer is nested to include all messages belonging to a conversation.
***
***