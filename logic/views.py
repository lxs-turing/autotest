import json
import time
import copy
import os
from django.shortcuts import render
from django.http import HttpResponse
from .service.file_service import generate_upload_file, trans_file_to_dict
from .service.case_service import Case, ports
from .service.guardian_service import get_detector_backend
from django.conf import settings


ip_cases_dict = {}
camera_configs = {}


def upload(request):
    if request.method == "GET":
        return render(request, "upload.html")
    elif request.method == 'POST':
        request_ip = _get_request_ip(request.META)
        files = request.FILES
        file_dict = generate_upload_file(files, request_ip)
        text = request.POST.get("mytext")
        case_file = file_dict.get("myfile")
        video_files = [value for key, value in file_dict.items(
        ) if key != "myfile" and os.path.exists(value)]
        video_files = list(set(video_files))
        try:
            if text:
                case_dict = json.loads(text)
            else:
                if case_file:
                    case_dict = trans_file_to_dict(case_file)
                else:
                    raise Exception(
                        "Text or file must be uploaded in JSON format.")
        except Exception as e:
            return HttpResponse("Case only supports JSON format!, error: {}".format(str(e)))
        try:
            case = Case(case_dict, video_files)
        except Exception as e:
            return HttpResponse(str(e))
        global camera_configs
        camera_configs.update(case.camera_configs)
        get_detector_backend().update_cameras(
            copy.deepcopy(camera_configs).values())
        case.start_time = int(time.time())
        global ip_cases_dict
        if request_ip in ip_cases_dict.keys():
            ip_cases_dict.get(request_ip).append(case)
        else:
            ip_cases_dict[request_ip] = [case]
        wait_time = _get_wait_time(ip_cases_dict.get(request_ip))
        if case.max_time == 0:
            strs = "This case uses rtsp, waiting time unknown, \
            Current IP needs to wait {}".format(wait_time)
        else:
            strs = "This case needs to wait {0}, \
                Current IP needs to wait {1}".format(case.max_time, wait_time)
        strs += "<br />result api: http://server_ip:server_port/result/"
        return HttpResponse(strs)


def result(request):
    global ip_cases_dict
    request_ip = _get_request_ip(request.META)
    cases = ip_cases_dict.get(request_ip, [])
    result = {}
    for case in cases:
        events = _generate_result(case.camera_ids)
        case_result = {}
        case_result["check_result"] = events
        case_result["ground_truth"] = case.events
        case_result["analyse_result"] = _match_expect_real_result(
            case.events, events)
        case_result["remain_time"] = _get_remain_time(case)
        if case_result["remain_time"] == 0:
            _release_port(case)
        result[case.case_id] = case_result
    result_strs = _format_show_result(result)
    return HttpResponse(result_strs)


def _format_show_result(result):
    strs = ""
    for key, value in result.items():
        strs += str(key) + "<br />"
        strs += json.dumps(value, ensure_ascii=False)
        strs += "<br /><br />"
    return strs


def _generate_result(camera_ids):
    events = []
    event_types = []
    for camera_id in camera_ids:
        path = os.path.join(settings.MEDIA_ROOT, str(camera_id))
        if not os.path.exists(path):
            continue
        for f in os.listdir(path):
            data_dict = json.load(open(os.path.join(path, f), 'r'))
            types = data_dict.get("types")
            if types not in event_types:
                events.append({
                    "event_type": types,
                    "event_count": 1
                })
                event_types.append(types)
            else:
                for event in events:
                    if event.get("event_type") == types:
                        event["event_count"] += 1
                        break
    return events


def _get_request_ip(meta_data):
    x_forwarded_for = meta_data.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = meta_data.get('REMOTE_ADDR')
    return ip


def _get_remain_time(case):
    remain_time = 0
    current_time = int(time.time())
    if case.max_time > current_time - case.start_time:
        remain_time = case.max_time - (current_time - case.start_time)
    return remain_time


def _release_port(case):
    for ffserver_obj in case.video_ffserver_objs.values():
        ffserver_obj.stop_ffserver()
        if ffserver_obj.port in ports:
            ports.remove(ffserver_obj.port)


def _get_wait_time(cases):
    current_time = int(time.time())
    wait_time = 0
    for case in cases:
        if case.max_time > current_time - case.start_time:
            remain_time = case.max_time - (current_time - case.start_time)
            wait_time = max(wait_time, remain_time)
    return wait_time


def _match_expect_real_result(expect_events, real_events):
    expect_event_types = [event.get("event_type") for event in expect_events]
    real_event_types = [event.get("event_type") for event in real_events]
    expect_event_types.sort()
    real_event_types.sort()
    if expect_event_types == real_event_types:
        for event_type in expect_event_types:
            expect_event = [event for event in expect_events if event.get(
                "event_type") == event_type][0]
            real_event = [event for event in real_events if event.get(
                "event_type") == event_type][0]
            expect_count_strs = expect_event.get("event_count").split(" ")
            expect_count = int(expect_count_strs[-1])
            if "gt" in expect_count_strs:
                if real_event.get("event_count") <= expect_count:
                    return False
            elif "lt" in expect_count_strs:
                if real_event.get("event_count") >= expect_count:
                    return False
            else:
                if real_event.get("event_count") != expect_count:
                    return False
        return True
    else:
        return False
