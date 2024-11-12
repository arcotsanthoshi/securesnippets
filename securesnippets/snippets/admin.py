# snippets/admin.py
from django.contrib import admin
from .models import Collection, Snippet, AccessControl, AuditLog

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_by', 'created_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'collection', 'created_by', 'version')
    list_filter = ('language', 'collection', 'created_by')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'

@admin.register(AccessControl)
class AccessControlAdmin(admin.ModelAdmin):
    list_display = ('snippet', 'user', 'permission', 'granted_by', 'granted_at')
    list_filter = ('permission', 'granted_at')
    search_fields = ('snippet__title', 'user__username')
    date_hierarchy = 'granted_at'

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'snippet', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_