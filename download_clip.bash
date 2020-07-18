#!/bin/bash
# https://github.com/ytdl-org/youtube-dl/issues/4821
# $1: url or Youtube video id
# $2: starting time, in seconds, or in hh:mm:ss[.xxx] form
# $3: duration, in seconds, or in hh:mm:ss[.xxx] form
# $4: output file
# $5: format, as accepted by youtube-dl (default: best)
# other args are passed directly to youtube-dl; eg, -r 40K
fmt=${5:-best}
url="$(youtube-dl --get-url -f $fmt ${@:5} -- "$1")"
ffmpeg -loglevel warning -hide_banner -ss $2 -i "$url" -c copy -t $3 "$4"
