from django.contrib import admin
from django.urls import path
from rest_framework.routers import DefaultRouter
from logic.viewsets import CameraViewSet, EventViewSet, MediumViewSet
from logic.views import upload, result


routers = DefaultRouter(trailing_slash=False)
routers.register(r'api/v1/camera/cameras', CameraViewSet, 'camera')
routers.register(r'api/v1/event/events', EventViewSet, 'event')
routers.register(r'api/v1/medium/mediums', MediumViewSet, 'medium')

urlpatterns = routers.urls

urlpatterns += [
    path('admin/', admin.site.urls),
    path('upload/', upload),
    path('result/', result),
]
