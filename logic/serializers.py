from rest_framework import serializers
from .models import Camera, Event, Medium


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ('id', 'name')


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'name')


class MediumSerializer(serializers.ModelSerializer):
    event_id = serializers.IntegerField(required=False)

    class Meta:
        model = Medium
        fields = ('id', 'name', 'file', 'event_id')
