#!/usr/bin/env python3
import re
import youtube_dl
import subprocess
import time
import os

# seconds
RIGHT_PAD = 0.4
LEFT_PAD = 0.3

class Interval:
    def __init__(self, start_time, end_time, match_string):
        """
        start_time and end_time should be strings hh:mm:ss[.xxx]
        match_string is the string that the Interval matches
        """
        self.start_time = start_time
        self.end_time = end_time
        self.match_string = match_string

    def __repr__(self):
        return f"Interval({self.start_time}, {self.end_time}, {self.match_string})"

TIMESTAMP_REGEX = r'\d+:\d{2}:\d{2}\.\d{3}'
TIME_WORD_1_REGEX = rf"(?P<time1>{TIMESTAMP_REGEX}) --> .*\n.*\n(?P<word1>[^<\n]+)(?=<)"
TIME_WORD_2_REGEX = rf"<(?P<time2>{TIMESTAMP_REGEX})><c> (?P<word2>[^<]+)</c>"
TIME_WORD_REGEX = re.compile(rf"{TIME_WORD_1_REGEX}|{TIME_WORD_2_REGEX}")
FINAL_TIME_REGEX = re.compile(rf"--> (?P<time>{TIMESTAMP_REGEX})")
def get_time_intervals(regex, subtitle):
    """
    Get the time intervals of all phrases that match `regex` in the space-separated words of `subtitle`.

    Returns a iterator of `Interval`s times in the format hh:mm:ss.000

    Only tested to work for autogenerated subtitles in VTT format from YouTube's autogeneration.
    """
    # module webvtt only gets the line-captions, not individual words, so it's time for some regex!
    # The time corresponding to a word is when that word *starts*
    # words = (match.group("word") for match in WORD_REGEX.finditer(subtitle))
    time_words = [
        (m.group("time1") or m.group("time2"), m.group("word1") or m.group("word2"))
        for m in TIME_WORD_REGEX.finditer(subtitle)
    ]
    times, words = zip(*time_words)
    # Quickly search lines starting from the end
    final_time = next(match.group("time") for line in reversed(subtitle.split("\n")) for match in [re.search(FINAL_TIME_REGEX, line)] if match)
    # timestamps[i] is the time the word starts at if i is the index of the start of a word
    timestamps = {}
    # Build search_str while computing time_stamps by adding one word and one space at a time
    search_str = ''
    times = [times[i] for i in range(len(times)) if i==len(times)-1 or parse_time(times[i+1])-parse_time(times[i]) > 0.011]
    words = list(words)
    assert len(times) == len(words), (len(times), len(words), list(zip(times, words)))
    for word, time in zip(words, times):
        timestamps[len(search_str)] = time
        search_str += word + ' '
    timestamps[len(search_str)] = final_time
    # Trim off the final space
    # Inconsistent capitalization, so just lowercase
    search_str = search_str[:-1].lower()
    for match in re.finditer(regex, search_str):
        start, end = match.span()
        yield Interval(
            timestamps[max(i for i in timestamps if i<=start)],
            timestamps[min(i for i in timestamps if i>end)],
            match.group(0)
        )

def subtitle_filename(video_id):
    return f"subtitles/{video_id}.en.vtt"

def download_subtitles(video_ids):
    ydl_opts = {
        'skip_download': True,
        'writeautomaticsub': True,
        'outtmpl': 'subtitles/%(id)s',
        'subtitleslangs': ['en']
    }
    undownloaded = [video_id for video_id in video_ids if not os.path.isfile(subtitle_filename(video_id))]
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        if undownloaded:
            # assume downloaded subtitle is correct
            ydl.download(undownloaded)
    for video_id in video_ids:
        with open(subtitle_filename(video_id)) as f:
            yield video_id, f.read()

def parse_time(time):
    h,m,s = [float(t) for t in time.split(":")]
    return 3600*h+60*m+s

def download_intervals(video_id, intervals):
    for i in intervals:
        start = parse_time(i.start_time)
        end = parse_time(i.end_time)
        start = start - LEFT_PAD
        duration = end - start + RIGHT_PAD
        sanitized_match_string = re.sub('[^a-zA-Z0-9_-]', '_', i.match_string)
        filename = f"clips/{video_id}+{sanitized_match_string}+{i.start_time}.mp4"
        if not os.path.isfile(filename):
            subprocess.run(['bash', 'download_clip.bash', video_id, str(start), str(duration), filename])

def download_clips(regex, video_ids, dry=False):
    video_ids = [video_id[:11] for video_id in video_ids]
    for video_id, subtitle in download_subtitles(video_ids):
        print("[info] considering video", video_id)
        intervals = list(get_time_intervals(regex, subtitle))
        if dry:
            print("[intervals]", intervals)
        else:
            download_intervals(video_id, intervals)
        # Delay between video downloads to respect the server
        time.sleep(2)

download_clips(r"(as always)? have a nice day", ["5pGepIfFxzQ", "bIC0x8OSNzg", "d-hBDjYtE1U"])#, "Pa6VWW7zYJw", "qYbNxE_SEIk", "81gXBVKF19o", "nOqDkdekaVE", "qvacFG9GyOM", "8b9y8QvxenU", "H6MuZhzqKGA", "avwt39uHDOQ", "oFktnCdbavA", "pTys_WYBOLE", "1lLiDnFTsOk", "D1ejvQ0UUNY", "vn0xMtHhgSQ", "JDNoMbjxBMI", "94z0OJ_-4Lo", "vMulHvAznwM", "D0foSHWP7rc", "EdD5oS5yaqg", "o6lteqXZdrA", "26OYMHIhK2U", "aY36o7JY4bo", "DvkSYh2dkN8", "WqE3leevbdg", "lF0uiRS8asc", "pLUGPqw0oks", "ZpX2b2t00Lg", "soyWGLnzeeI", "Gl7gt0SeBi8", "uPqwp7TPGzQ", "-d760fMfiNc", "mG9RHjC9rTM", "uukkzSy3Aw8", "EA5wr3qTVOc", "YzncNl6N18s", "c2DcfJLquOk", "J5Kxm8I1BXU", "mjArO09tGaI", "_iEP_uKOdrQ", "ZW3s1iks0No", "8WkNoA_ki9c", "njU3r3aWm3k", "ixPFDFp8Cfo", "nk6KrBsDwDE", "-aOh4D2GKaw", "TTcrdX7dIZ8", "v_IPY3MM3Yc", "lkfBKQuLkRc", "Cw0EPb3S8v4", "APvmp-rp_D0", "Csa01fsnCQE", "K2KNc4g-0yI", "bLIawIQp3pk", "jHTpW7euAns", "M7q0Qbpa34U", "DuZWhRaLzhk", "lqUapRX9EsY", "isQPh9Gx0q4", "n0cUqNwYcoI", "Joed0P3hhbc", "RR31o8x1OvU", "rco9WLJ82u0", "3N84iZ68cXQ", "OvzMEwVnB2w", "VAIONzHzlXk", "ogELZ78OfyM", "KHvfwpnPwwU", "pRdT07TSSs0", "BO_XEpdw2jA", "ZCKw0nWkpfs", "XXW27KKHtc8", "onHJuyDjbsM", "Tfm-W_DSdXw", "EpDMsPgnh_M", "dTObKtHzroM", "7L8XvasJzdQ", "EXHjirjUJUk", "KcZPIfIbG5o", "0SEHUqkbIjU", "a_oAkbzSKxo", "WAtxEpMDeNk", "oZLNQl0bk1c", "_rGvb2yYh1M", "nz6NxH3wy94", "ToQT_i4I6vI", "ANsipsS7IK8", "T5YsZLJ5FjY", "uUVye2mdwew", "QgOpSFyin8M", "mgWEIiIfGsQ", "z4lVylO7y5U", "TU3nNaIkQLQ", "9_wvQGdCF94", "u2HUXZ61EY8", "78GFp2zTPoo", "6DA92d93FRI", "ke418cAUcPs", "ympVA0GW1jE", "6RSXQsYYso4", "D5Y7R7-4FnA", "wOedgb2zC5s", "slwqiGh0Fak", "nHJWcFe27S0", "EIQkBlo1L8k", "uK3BbETDYis", "_C7bJiFTfFs", "q8AP5XYs8jg", "Zhz9g6A_fuI", "Chu4mvEUc5I", "U__RaOy39Sg", "i7g-TvczpSw", "rbf_NX0-Uj0", "mAyTv64YkTI", "va7PBIQ4CJ8", "Um2Me3Iuv5Q", "nmL-fwtjVUA", "GD0JbDyGOsA", "MK83CkvLbcQ", "i_xZSTF_Uq0", "kSZuVW_1yi8", "cNHY90uQ2eY", "iqsAjzm-qtA", "oPiCgf4U6oE", "hnj8gGf2e7E", "NQjH3-6Qm7c", "o5BRy93769U", "1D_vCWzX_Rw", "5kWBZz7dFxw", "SUfOQ5XeS5Q", "nDgC8JOQhiM"])
