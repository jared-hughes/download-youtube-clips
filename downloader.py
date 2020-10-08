import time
import re
import os
import subprocess

last_downloaded_time = 0
# seconds
INTERVAL = 2
RIGHT_PAD = 0.4
LEFT_PAD = 0.0

def download_clip(video_id, start_time, end_time, name):
    global last_downloaded_time
    t = time.time()
    # Delay between video downloads to respect the server
    dt = t - last_downloaded_time
    if dt < INTERVAL:
        time.sleep(INTERVAL - dt)
    start = start_time - LEFT_PAD
    duration = end_time + RIGHT_PAD - start
    sanitized_name = re.sub('[^a-zA-Z0-9_-]', '_', name)
    # Can be concerned about filename too long (255 bytes)
    filename = f"clips/{sanitized_name}+{video_id}+{start_time}-{end_time}.mp4"
    if not os.path.isfile(filename):
        subprocess.run(['bash', 'download_clip.bash', video_id, str(start), str(duration), filename])
        last_downloaded_time = time.time()

def download_intervals(video_id, intervals):
    for interval in intervals:
        download_clip(
            video_id, interval.start_time,
            interval.end_time, interval.match_string
        )
