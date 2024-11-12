# snippets/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Collection, Snippet, AccessControl, AuditLog
from .serializers import (
    CollectionSerializer, SnippetSerializer, 
    AccessControlSerializer, AuditLogSerializer
)

class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Collection.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class SnippetViewSet(viewsets.ModelViewSet):
    serializer_class = SnippetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Snippet.objects.filter(
            models.Q(created_by=self.request.user) |
            models.Q(accesscontrol__user=self.request.user, 
                    accesscontrol__permission__in=['read', 'write', 'admin'])
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        snippet = self.get_object()
        user_id = request.data.get('user_id')
        permission = request.data.get('permission', 'read')
        
        if not user_id:
            return Response(
                {'error': 'User ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        target_user = get_object_or_404(User, id=user_id)
        
        AccessControl.objects.create(
            snippet=snippet,
            user=target_user,
            permission=permission,
            granted_by=request.user
        )
        
        return Response({'status': 'shared successfully'})

class AccessControlViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccessControlSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AccessControl.objects.filter(
            models.Q(snippet__created_by=self.request.user) |
            models.Q(user=self.request.user)
        )

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AuditLog.objects.filter(snippet__created_by=self.request.user)