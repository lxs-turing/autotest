import time
import os
import json
from django.conf import settings
from rest_framework.viewsets import ModelViewSet
from .models import Camera, Event, Medium
from .serializers import CameraSerializer, EventSerializer, MediumSerializer
from rest_framework.response import Response
from rest_framework import status


class CameraViewSet(ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer

    def update(self, request, *args, **kwargs):
        print("camera update")
        data = _packing_result_data({})
        return Response(data)


class EventViewSet(ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        print("event create")
        data = request.data
        print(data)
        _write_event(data)
        data = _packing_result_data({})
        return Response(data, status=status.HTTP_201_CREATED)


class MediumViewSet(ModelViewSet):
    queryset = Medium.objects.all()
    serializer_class = MediumSerializer

    def create(self, request, *args, **kwargs):
        print("medium create")
        result = super(MediumViewSet, self).create(request, *args, **kwargs)
        result.data = _packing_result_data(result.data)
        return result


def _packing_result_data(data):
    data = {
        'err': {'ec': 0, 'dm': 'ok'},
        'ret': data,
    }
    return data


def _write_event(data):
    time_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    camera_id = data.get("camera_id")
    path = os.path.join(settings.MEDIA_ROOT, str(camera_id))
    file_name = "{0}_{1}.json".format(camera_id, time_str)
    if not os.path.exists(path):
        os.mkdir(path)
    json.dump(data, open(os.path.join(path, file_name), 'w'))
