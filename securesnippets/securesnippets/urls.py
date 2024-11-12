# securesnippets/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('snippets.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# snippets/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'collections', views.CollectionViewSet, basename='collection')
router.register(r'snippets', views.SnippetViewSet, basename='snippet')
router.register(r'access', views.AccessControlViewSet, basename='access')
router.register(r'audit', views.AuditLogViewSet, basename='audit')

urlpatterns = [
    path('', include(router.urls)),
]