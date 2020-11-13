import os
import json
from django.conf import settings


def generate_upload_file(files, ip):
    path = os.path.join(settings.MEDIA_ROOT, ip)
    if not os.path.exists(path):
        os.mkdir(path)
    file_dict = {}
    for key, value in files.items():
        file_path = os.path.join(path, value.name)
        with open(file_path, 'wb+') as des:
            if value.multiple_chunks():
                for chunk in value.chunks():
                    des.write(chunk)
            else:
                des.write(value.read())
        file_dict[key] = file_path
    return file_dict


def trans_file_to_dict(file_path):
    case_dict = {}
    if os.path.exists(file_path):
        try:
            case_dict = json.load(open(file_path, 'r'))
        except Exception:
            raise Exception("文件内容不是json格式")
    return case_dict
