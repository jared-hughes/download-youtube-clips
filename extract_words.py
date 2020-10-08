#!/usr/bin/env python3
import re
import youtube_dl
import time
import os
from downloader import download_intervals

CACHED_NO_SUBTITLES_FILE = "cached_no_subtitles.txt"

with open(CACHED_NO_SUBTITLES_FILE) as f:
    cached_no_subtitles = set(f.read().splitlines())

class Interval:
    def __init__(self, start_time, end_time, start_index, end_index, match_string):
        """
        start_time and end_time should be strings hh:mm:ss[.xxx]
        start_index and end_index refer to that # word
        match_string is the string that the Interval matches
        """
        self.start_time = start_time
        self.end_time = end_time
        self.start_index = start_index
        self.end_index = end_index
        self.match_string = match_string

    def __repr__(self):
        return f"Interval({self.start_index}, {self.end_index}, \"{self.match_string}\")"

TIMESTAMP_REGEX = r'\d+:\d{2}:\d{2}\.\d{3}'
TIME_WORD_1_REGEX = rf"(?P<time1>{TIMESTAMP_REGEX}) --> .*\n.*\n(?P<word1>[^<\n]+)(?=<)"
TIME_WORD_2_REGEX = rf"<(?P<time2>{TIMESTAMP_REGEX})><c> (?P<word2>[^<]+)</c>"
TIME_WORD_REGEX = re.compile(rf"{TIME_WORD_1_REGEX}|{TIME_WORD_2_REGEX}")
FINAL_TIME_REGEX = re.compile(rf"--> (?P<time>{TIMESTAMP_REGEX})")
def get_time_intervals(subtitle, regex=r"\S+"):
    """
    Get the time intervals of all words in the space-separated words of `subtitle`.

    Returns a generator of `Interval`s times in the format hh:mm:ss.000

    Only tested to work for subtitles in VTT format from YouTube's autogeneration.
    """
    # module webvtt only gets the line-captions, not individual words, so it's time for some regex!
    # The time corresponding to a word is when that word *starts*
    # words = (match.group("word") for match in WORD_REGEX.finditer(subtitle))
    time_words = [
        (m.group("time1") or m.group("time2"), m.group("word1") or m.group("word2"))
        for m in TIME_WORD_REGEX.finditer(subtitle)
    ]
    # Incorrect format, which would lead to trouble zipping
    if len(time_words) == 0:
        return []
    times, words = zip(*time_words)
    # Quickly search lines starting from the end
    final_time = next(match.group("time") for line in reversed(subtitle.split("\n")) for match in [re.search(FINAL_TIME_REGEX, line)] if match)
    # timestamps[i] is the time the word starts at if i is the index of the start of a word
    timestamps = {}
    word_indices = {}
    # Build search_str while computing time_stamps by adding one word and one space at a time
    search_str = ''
    words = list(words)
    last_time = 0
    for j, (word, time) in enumerate(zip(words, times)):
        i = len(search_str)
        time = parse_time(time)
        timestamps[i] = time
        if time - last_time > 10:
            search_str += '[ … ] '
        last_time = time
        word_indices[i] = j
        search_str += word + ' '
    i = len(search_str)
    timestamps[i] = final_time
    word_indices[i] = len(words)
    # Trim off the final space
    # Inconsistent capitalization, so just lowercase
    search_str = search_str[:-1].lower()
    for match in re.finditer(regex, search_str):
        start, end = match.span()
        start_index = max(i for i in timestamps if i<=start)
        end_index = min(i for i in timestamps if i>end)
        yield Interval(
            timestamps[start_index],
            timestamps[end_index],
            word_indices[start_index],
            word_indices[end_index],
            match.group(0)
        )

def download_subtitles(video_ids):
    """
    Download all subtitles for the listed video IDs
    This is a generator, so use list(download_subtitles([...])) to download all
    """
    print(f"[downloading subs] {video_ids}")
    ydl_opts = {
        'skip_download': True,
        'writeautomaticsub': True,
        'outtmpl': 'subtitles/%(id)s',
        'subtitleslangs': ['en']
    }
    for video_id in video_ids:
        filename = f"subtitles/{video_id}.en.vtt"
        # Don't download if these subtitles are already downloaded
        # or if we know there are no subtitles on the video
        if video_id in cached_no_subtitles:
            continue
        if not os.path.isfile(filename):
            print(f"[downloading subtitle] {video_id}")
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # assume downloaded subtitle is correct
                ydl.download([video_id])
                # Delay to be nice to the server
                time.sleep(2)
        try:
            with open(filename) as f:
                yield video_id, f.read()
        except IOError:
            with open(CACHED_NO_SUBTITLES_FILE, "a") as f:
                f.write(video_id + '\n')
            cached_no_subtitles.add(video_id)
            yield video_id, None

def parse_time(time):
    h,m,s = [float(t) for t in time.split(":")]
    return 3600*h+60*m+s

def search_in_videos(video_ids, regex):
    i = 1
    for video_id, subtitle in download_subtitles(video_ids):
        print(f"[info] considering video {i}/{len(video_ids)}: {video_id}")
        if subtitle == None:
            print(f"[warning] {video_id} lacks automatic captions")
            continue
        words = list(get_time_intervals(subtitle))
        match_intervals = list(get_time_intervals(subtitle, regex))
        yield video_id, words, match_intervals
