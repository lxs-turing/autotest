import os
import re
import math
from django.conf import settings


def get_video_duration(video_path):
    cmd = "{0} {1} 2>&1".format(settings.FFPROBE_EXECUTABLE, video_path)
    process_obj = os.popen(cmd)
    strs = process_obj.read()
    process_obj.close()
    match_str = re.findall(r'.*Duration: (.*), start.*', strs)[0]
    time_strs = match_str.split(":")
    duration_time = int(time_strs[0]) * 3600 + int(time_strs[1]) * 60 + math.ceil(float(time_strs[2]))
    return duration_time
