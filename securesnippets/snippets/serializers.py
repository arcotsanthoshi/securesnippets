# snippets/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Collection, Snippet, AccessControl, AuditLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CollectionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Collection
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class SnippetSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = Snippet
        fields = ['id', 'title', 'content', 'language', 'collection', 
                 'created_by', 'created_at', 'updated_at', 'tags', 'version']
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'version']

    def get_content(self, obj):
        return obj.get_decrypted_content()

class AccessControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessControl
        fields = ['id', 'snippet', 'user', 'permission', 'granted_by', 'granted_at']
        read_only_fields = ['granted_by', 'granted_at']

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'snippet', 'timestamp', 'ip_address', 'details']
        read_only_fields = ['timestamp']