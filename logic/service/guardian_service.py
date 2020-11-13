import os
import atexit
import json
import subprocess
from threading import Lock
from django.conf import settings

_guardian_version = ''


def _get_guardian_version():
    global _guardian_version

    if not _guardian_version:
        guardian_dir = os.path.dirname(settings.GUARDIAN_EXECUTABLE)
        version = None
        try:
            with open(os.path.join(guardian_dir, 'VERSION')) as f:
                version = f.read()
        except:  # noqa
            print("guardian version error!")
        # format: 2.6.0-sample-event-1c9a37
        _guardian_version = version.split('-')[0] if version else 'unknown'
    return _guardian_version


class _GuardianDetectorBackend:
    """
    Guardian detector backend.
    """

    def __init__(self):
        self._lock = Lock()
        self._execute_process = None
        atexit.register(self._stop)
        self._version = _get_guardian_version()

    def _compare_version(self):
        v = self._version.split('.')
        if len(v) != 3:
            return False

        return int(v[0]) > 2 or (int(v[0]) == 2 and int(v[1]) >= 6)

    def update_cameras(self, cameras, detect_on=True):
        args = self._build_args(cameras, detect_on=detect_on)
        self._run(args)

    def _run(self, args):
        if not settings.GUARDIAN_EXECUTABLE:
            return False

        if not self._compare_version():
            with self._lock:
                if self._execute_process:
                    self._execute_process.terminate()
                    self._execute_process = None

        self._execute_process = subprocess.Popen(args)

    def _stop(self):
        with self._lock:
            if self._execute_process:
                self._execute_process.terminate()
                self._execute_process = None

    @classmethod
    def _get_base_cmd(cls):
        python = settings.GUARDIAN_PYTHON
        executable = settings.GUARDIAN_EXECUTABLE
        return [python, executable] if python else [executable]

    @classmethod
    def _build_args(cls, cameras, *args, detect_on=True):
        popenargs = cls._get_base_cmd()
        if args:
            popenargs += list(args)
        cameras_args = []
        if detect_on:
            cameras_args = list(cameras)
        popenargs.append('--cameras')
        popenargs.append(json.dumps(cameras_args))
        return popenargs


_detector_backend = None


def get_detector_backend():
    '''
    Used only for celery worker.
    Do not used in web process.
    '''
    global _detector_backend
    if not _detector_backend:
        _detector_backend = _GuardianDetectorBackend()
    return _detector_backend
