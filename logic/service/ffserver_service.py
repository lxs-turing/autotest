import subprocess
import os
import re
import atexit
from django.conf import settings


class FFServer:

    def __init__(self, camera_id, video_path, port, name):
        self.camera_id = camera_id
        self.video_path = video_path
        self.port = port
        self.path = os.path.dirname(video_path)
        self.name = name
        self.cmd = self._get_ffserver_cmd()
        atexit.register(self.stop_ffserver)

    def start_ffserver(self):
        p = subprocess.Popen(self.cmd, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return p.pid

    def stop_ffserver(self):
        cmd_str = " ".join(self.cmd[:-1])
        pids = _find_process_id(cmd_str)
        _kill_process_by_ids(pids)

    def _get_ffserver_cmd(self):
        cfg_file_path = self._write_ffserver_cfg()
        execute_ffserver_path = settings.FFSERVER_EXECUTABLE
        cmd = [execute_ffserver_path, "-f", cfg_file_path]
        return cmd

    def _write_ffserver_cfg(self):
        cfg_save_name = "{}_ffserver.cfg".format(self.camera_id)
        cfg_file_path = os.path.join(self.path, cfg_save_name)
        with open(cfg_file_path, 'w+') as f:
            f.write("RTSPPort {}\n".format(self.port))
            f.write("BindAddress 0.0.0.0\n")
            f.write("RTSPBindAddress 0.0.0.0\n")
            f.write("MaxHTTPConnections 3000\n")
            f.write("MaxClients 500\n")
            f.write("MaxBandwidth 50000\n")
            f.write("CustomLog -\n")
            f.write("NoDaemon\n")
            f.write("<Stream {}>\n".format(self.name))
            f.write("File {}\n".format(self.video_path))
            f.write("Format rtp\n")
            f.write("</Stream>\n")
        return cfg_file_path


def _kill_process_by_id(pid):
    cmd_obj = os.popen("kill -9 {}".format(pid))
    cmd_obj.close()


def _kill_process_by_ids(pids):
    if pids:
        for pid in pids:
            _kill_process_by_id(pid)


def _find_process_id(cmd_str):
    ps_obj = os.popen("ps x | grep ffserver")
    ps_strs = ps_obj.read()
    ps_obj.close()
    ps_str_list = ps_strs.split("\n")
    ps_str_list = [x.strip() for x in ps_str_list]
    pids = []
    for ps_str in ps_str_list:
        if cmd_str in ps_str:
            pid = re.findall(r'(\d+) .*', ps_str)[0]
            pids.append(pid)
    return pids
