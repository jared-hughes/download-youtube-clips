#!/usr/bin/env python3

import json
import extract_words
import argparse
import curses
from textwrap import dedent

parser = argparse.ArgumentParser(
    description=dedent("""\
    Download Youtube subtitles + clips

    Sample usage:
        dlyt.py new-project projects/hello.json
        dlyt.py add-videos projects/hello.json "ab1cd_2efg3" "hij2klmn-o"
        dlyt.py download-clips projects/hello.json "hello|hi"
    """),
    # retain newlines
    formatter_class=argparse.RawTextHelpFormatter
)

default_state = {
    "videos": []
}

def dump_json(state, project_file):
    path = project_file.name
    with open(path, "w") as f:
        json.dump(state, f, indent=True)
    project_file.seek(0)

def new_project(args):
    dump_json(default_state, args.project)

def add_videos(args):
    state = json.load(args.project)
    videos = state["videos"]
    for video in args.videos:
        if video not in videos:
            videos.append(video)
    state["videos"] = list(videos)
    dump_json(state, args.project)

def remove_videos(args):
    state = json.load(args.project)
    args.videos = args.videos or state["videos"]
    videos = state["videos"]
    for video in args.videos:
        videos.remove(video)
    state["videos"] = list(videos)
    dump_json(state, args.project)

def download_subs(args):
    add_videos(args)
    state = json.load(args.project)
    videos = args.videos or state["videos"]
    list(extract_words.download_subtitles(videos))

def word_index(intervals, index, is_start):
    # if is start then reverse order
    for i in range(index, len(intervals)):
        if intervals[i].start_index > index:
            return ind
        if intervals[i].start_index >= index:
            ind = i
            if is_start:
                return ind

def actual_intervals(intervals, start_word, end_word):
    return intervals[word_index(intervals, start_word, True): word_index(intervals, end_word, False)+1]

def words_from_intervals(intervals, start, end):
    return ' '.join(interval.match_string for interval in actual_intervals(intervals, start, end))

def _download_clips(stdscr, args):
    # When the spagetti makes you cry just like a pasta e fasul
    # That's amore
    # hide cursor
    curses.curs_set(False)
    add_videos(args)
    state = json.load(args.project)
    videos = args.videos or state["videos"]
    # height, width, starty, startx
    video_num_win = curses.newwin(1, 36, 0, 0)
    interval_num_win = curses.newwin(1, 26, 1, 0)
    current_string_win = curses.newwin(6, curses.COLS, 3, 0)
    controls_win = curses.newwin(3, 46, 10, 0)
    debug_win = curses.newwin(10, 50, 16, 0)
    import time
    for j, (video_id, word_intervals, match_intervals) in enumerate(extract_words.search_in_videos(videos, args.regex)):
        video_num_win.clear()
        video_num_win.addstr(0, 0, f"Video {j+1}/{len(videos)}: {video_id}")
        video_num_win.refresh()
        for i, match_interval in enumerate(match_intervals):
            interval_num_win.clear()
            interval_num_win.addstr(0, 0, f"Interval {i+1}/{len(match_intervals)}", curses.A_BOLD)
            interval_num_win.refresh()

            selected_indices = [match_interval.start_index, match_interval.end_index]
            max_context_words = 10


            while True:
                # compute relevant words for preview box
                left_context_length = min(max_context_words, selected_indices[0])
                can_left = left_context_length > 0
                right_context_length = min(max_context_words, word_intervals[-1].end_index - selected_indices[1] - 1)
                can_right = right_context_length > 0
                can_shrink = selected_indices[1] - selected_indices[0] > 1
                selected_words = words_from_intervals(word_intervals, selected_indices[0], selected_indices[1]-1)
                left_context_words = words_from_intervals(word_intervals, selected_indices[0]-left_context_length-1, selected_indices[0]-1)
                right_context_words = words_from_intervals(word_intervals, selected_indices[1], selected_indices[1]+right_context_length)
                # update controls with currently relevant ones
                controls_win.clear()
                controls_win.addstr(
                    0, 0,
                    (
                        "`<` extend left" * can_left +
                        " | " * (can_left and can_right )+
                        "`.` extend right" * can_right +
                        "\n" * (can_left or can_right) +
                        "`>` shrink from left | `,` shrink from right\n" * can_shrink +
                        "`s` skip | `Enter` download"
                    ),
                    curses.A_DIM
                )
                controls_win.refresh()

                # debug_win.clear()
                # debug_win.addstr(0, 0, str(word_intervals[1]))
                # debug_win.refresh()
                # wrap doesn't respect word boundaries, but not high priority rn
                current_string_win.clear()
                current_string_win.addstr(0, 0, left_context_words + " ", curses.A_DIM)
                current_string_win.addstr(selected_words + " ", curses.A_BOLD)
                current_string_win.addstr(right_context_words, curses.A_DIM)
                current_string_win.refresh()

                c = current_string_win.getkey(0, 0)

                if c == '<' and can_left:
                    selected_indices[0] -= 1
                elif c == '.' and can_right:
                    selected_indices[1] += 1
                elif c == '>' and can_shrink:
                    selected_indices[0] += 1
                elif c == ',' and can_shrink:
                    selected_indices[1] -= 1
                elif c == 's':
                    break
                elif c == '\n':
                    ints = actual_intervals(word_intervals, selected_indices[0], selected_indices[1]-1)
                    extract_words.download_intervals(video_id, [
                        extract_words.Interval(ints[0].start_time, ints[-1].end_time, None, None, args.regex)
                    ])
                    break
                # break

def download_clips(args):
    curses.wrapper(_download_clips, args)


subparser = parser.add_subparsers()
subcommands = [
    ("new-project", "Initialize a project file", "*", new_project),
    ("add-videos", "Add videos", "+", add_videos),
    ("remove-videos", "Remove videos (defaults to all)", "*", remove_videos),
    ("download-subs", "Download subtitles of ids (defaults to all)", "*", download_subs),
    ("download-clips", "Select and download desired intervals of ids. Automatically downloads subtitles if necessary (defaults to all)", "*", download_clips)
]
parsers = {}
for subcommand, help, nargs, func in subcommands:
    parsers[subcommand] = subparser.add_parser(subcommand, help=help)
    parsers[subcommand].add_argument(
        "project",
        type=argparse.FileType("w" if subcommand=="new-project" else "r+")
    )
    if subcommand != "new-project":
        parsers[subcommand].add_argument(
            "videos",
            help="Video IDs, space-separated; defaults to all",
            nargs=nargs
        )
    parsers[subcommand].set_defaults(func=func)

parsers["download-clips"].add_argument(
    "regex",
    help="Match regex for search"
)

def do_parse(x):
    args = parser.parse_args(x)
    if "func" in args:
        args.func(args)
    else:
        # given no arguments at all
        parser.parse_args(["-h"])

do_parse(None)
