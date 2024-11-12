# backend/securesnippets/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "snippets.apps.SnippetsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "snippets.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "securesnippets.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "securesnippets"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# Static and Media files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# backend/snippets/models.py
from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet


class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Snippet(models.Model):
    LANGUAGE_CHOICES = [
        ("python", "Python"),
        ("javascript", "JavaScript"),
        ("java", "Java"),
        ("cpp", "C++"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    encrypted_content = models.BinaryField(null=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.JSONField(default=list)
    version = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        if self.content:
            key = Fernet.generate_key()
            f = Fernet(key)
            self.encrypted_content = f.encrypt(self.content.encode())
            self.content = ""
        super().save(*args, **kwargs)

    def get_decrypted_content(self):
        if self.encrypted_content:
            f = Fernet(self.encryption_key)
            return f.decrypt(self.encrypted_content).decode()
        return ""


class AccessControl(models.Model):
    PERMISSION_CHOICES = [
        ("read", "Read"),
        ("write", "Write"),
        ("admin", "Admin"),
    ]

    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES)
    granted_by = models.ForeignKey(
        User, related_name="granted_permissions", on_delete=models.CASCADE
    )
    granted_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    details = models.JSONField(default=dict)


# backend/snippets/serializers.py
from rest_framework import serializers
from .models import Snippet, Collection, AccessControl


class SnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = [
            "id",
            "title",
            "content",
            "language",
            "collection",
            "created_by",
            "created_at",
            "updated_at",
            "tags",
            "version",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at", "version"]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "name", "description", "created_by", "created_at", "updated_at"]
        read_only_fields = ["created_by", "created_at", "updated_at"]


# backend/snippets/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Snippet, Collection, AccessControl
from .serializers import SnippetSerializer, CollectionSerializer


class SnippetViewSet(viewsets.ModelViewSet):
    serializer_class = SnippetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Snippet.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        snippet = self.get_object()
        user_id = request.data.get("user_id")
        permission = request.data.get("permission", "read")

        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        target_user = get_object_or_404(User, id=user_id)

        AccessControl.objects.create(
            snippet=snippet,
            user=target_user,
            permission=permission,
            granted_by=request.user,
        )

        return Response({"status": "shared successfully"})
