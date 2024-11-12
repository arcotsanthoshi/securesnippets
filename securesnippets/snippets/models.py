# snippets/models.py
from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet

class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Snippet(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('other', 'Other'),
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

    class Meta:
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if self.content:
            key = Fernet.generate_key()
            f = Fernet(key)
            self.encrypted_content = f.encrypt(self.content.encode())
            self.content = ''
        super().save(*args, **kwargs)

    def get_decrypted_content(self):
        if self.encrypted_content and hasattr(self, 'encryption_key'):
            f = Fernet(self.encryption_key)
            return f.decrypt(self.encrypted_content).decode()
        return ''

class AccessControl(models.Model):
    PERMISSION_CHOICES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('admin', 'Admin'),
    ]

    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES)
    granted_by = models.ForeignKey(User, related_name='granted_permissions', on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['snippet', 'user']

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']