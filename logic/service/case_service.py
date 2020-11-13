import os
import copy
import time
from .ffserver_service import FFServer
from logic.utils.network import get_default_interface, get_ip_address
from logic.utils.util import get_video_duration


case_cameras_dict = {}
global_camera_ids = []
ports = []


class Case:

    def __init__(self, case_dict, video_files):
        self.case_dict = case_dict
        self.video_files = video_files
        self.video_file_names = [os.path.basename(
            video) for video in video_files]
        self.case_id = \
            time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())) \
            + "_{}".format(case_dict.get("case_id"))
        self.max_time = 0
        self.video_ffserver_objs = {}
        self.video_ffserver_pids = []
        self.camera_configs, self.camera_ids = self._parser()
        self.events = case_dict.get("ground_truth", {}).get("events", [])

    def _parser(self):
        case_dict = copy.deepcopy(self.case_dict)
        _check_camera_config_match_id(case_dict.get("datas"), case_dict.get("configs"))
        cameras = {}
        match_old_new = {}
        for data in case_dict.get("datas", []):
            camera = {}
            camera["id"] = data.get("id")
            global global_camera_ids
            old_id = camera["id"]
            if old_id and isinstance(old_id, int):
                if camera["id"] in global_camera_ids:
                    camera["id"] = global_camera_ids[-1] + 1
            else:
                if global_camera_ids:
                    camera["id"] = global_camera_ids[-1] + 1
                else:
                    camera["id"] = 1
            match_old_new[old_id] = camera["id"]
            global_camera_ids.append(camera["id"])
            camera["uri"] = data.get("uri")
            if "rtsp" not in camera["uri"]:
                if not os.path.exists(camera["uri"]) and os.path.basename(camera["uri"] not in self.video_file_names):
                    raise Exception("{} not exists".format(camera["uri"]))
                else:
                    if not os.path.exists(camera["uri"]):
                        camera["uri"] = [video_file for video_file in self.video_files if os.path.basename(
                            camera["uri"]) == os.path.basename(video_file)]
                    duration_time = get_video_duration(camera["uri"])
                    if duration_time > self.max_time:
                        self.max_time = duration_time
                    name = os.path.splitext(os.path.basename(camera["uri"]))[
                        0] + ".mp4"
                    port = _get_port()
                    video_ffserver_obj = FFServer(
                        camera["id"], camera["uri"], port, name)
                    pid = video_ffserver_obj.start_ffserver()
                    ip = get_ip_address(get_default_interface())
                    camera["uri"] = "rtsp://{0}:{1}/{2}".format(
                        ip, port, name)
                    self.video_ffserver_objs[camera["id"]] = video_ffserver_obj
                    self.video_ffserver_pids.append(pid)
            else:
                ip = get_ip_address(get_default_interface())
                rtsp_ip = camera["uri"].split("rtsp://")[-1].split(":")[0]
                rtsp_port = camera["uri"].split("rtsp://")[-1].split(":")[1].split("/")[0]
                if ip == rtsp_ip:
                    global ports
                    if int(rtsp_port) in ports:
                        port = _get_port()
                        camera["uri"] = camera["uri"].replace(rtsp_port, str(port))
                    else:
                        ports.append(int(rtsp_port))
            camera["format"] = data.get("format", "")
            camera["fps"] = data.get("fps", 0)
            cameras[camera["id"]] = camera
        global case_cameras_dict
        case_cameras_dict[self.case_id] = list(camera.keys())
        configs = {}
        for cfg in case_dict.get("configs", []):
            config = {}
            config["id"] = match_old_new.get(cfg.get("camera_id"))
            config["detect_params"] = cfg.get("camera_configs", {})
            config["algos"] = cfg.get("algos", [])
            if config["id"] and config["id"] not in configs.keys():
                configs[config["id"]] = config
        camera_ids = list(cameras.keys())
        config_ids = list(configs.keys())
        camera_ids.sort()
        config_ids.sort()
        camera_configs = {}
        if camera_ids == config_ids:
            for id_num in camera_ids:
                camera_config = {}
                camera_config["id"] = id_num
                camera_config["mode"] = "on"
                camera_config["uri"] = cameras[id_num]["uri"]
                camera_config["detect_params"] = configs[id_num]["detect_params"]
                camera_config["algos"] = configs[id_num]["algos"]
                camera_config["sampling"] = False
                camera_configs[id_num] = camera_config
        return camera_configs, camera_ids


def _check_camera_config_match_id(cameras, configs):
    camera_id = [cam.get("id") for cam in cameras]
    config_id = [con.get("camera_id") for con in configs]
    if len(camera_id) != len(list(set(camera_id)))\
            or len(config_id) != len(list(set(config_id))):
        raise Exception("camera id cannot be repeated.")
    if len(camera_id) != len(config_id):
        raise Exception("Data and config do not match!")
    for id_num in camera_id:
        if id_num not in config_id:
            raise Exception("Data and config do not match!")


def _get_port():
    global ports
    port = 8488
    while True:
        if port not in ports:
            ports.append(port)
            break
        port += 1
    return port
