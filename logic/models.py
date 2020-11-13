from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Camera(models.Model):
    name = models.CharField(max_length=20)


class Event(models.Model):
    name = models.CharField(max_length=20)


def _medium_upload_to(medium, filename):
    return '/'.join(['mediums', timezone.now().strftime('%Y/%m/%d'), filename])


class Medium(models.Model):
    SNAPSHOT = 'snapshot'
    VIDEO = 'video'
    BBOX = 'bbox'
    NAMES = (
        ('snapshot', _('Snapshot')),
        ('video', _('Video')),
        ('bbox', _('Bounding Box')),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event = models.ForeignKey(Event, related_name='mediums', null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, choices=NAMES)
    file = models.FileField(upload_to=_medium_upload_to)
