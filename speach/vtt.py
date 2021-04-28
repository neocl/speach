# -*- coding: utf-8 -*-

'''
Web Video Text Tracks format (WebVTT) support

More information:
    WebVTT: The Web Video Text Tracks Format
        https://www.w3.org/2013/07/webvtt.html
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


import re
import math

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

WEBVTT = re.compile(r'(?P<hour>\d{2,}):(?P<min>\d{2}):(?P<sec>\d{2}.\d{3})')


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

def sec2ts(seconds: float) -> str:
    ''' Convert duration in seconds in seconds to VTT format (e.g. 01:53:47.262)

    >>> from speach import vtt
    >>> vtt.sec2ts(25.403)
    '00:00:25.403'
    >>> vtt.sec2ts(14532.768)
    '04:02:12.768'

    :param seconds: Timestamp in seconds
    :type ts: float
    :returns: Web VTT formatted timestamp
    :rtype: str
    :raises: :exc:`ValueError`: when seconds is not a number or cannot be casted into a number
    '''
    try:
        seconds = float(seconds)
        if seconds < 0:
            raise ValueError("Timestamp cannot be smaller than 0")
    except Exception as e:
        raise ValueError("Invalid timestamp ({})".format(seconds)) from e
    min_base = math.floor(seconds / 60)
    ts_hour = math.floor(min_base / 60)
    ts_min = math.floor(min_base % 60)
    ts_sec = math.floor(seconds) % 60
    ts_msec = (seconds - int(seconds)) * 1000
    ts = "{:0>2.0f}:{:0>2.0f}:{:0>2.0f}.{:0>3.0f}".format(ts_hour, ts_min, ts_sec, ts_msec)
    return ts


def ts2sec(ts: str) -> float:
    ''' Convert VTT timestamp to duration (float, in seconds)

    >>> from speach import vtt
    >>> vtt.ts2sec("01:00:41.231")
    3641.231
    >>> print(vtt.ts2sec("00:00:00.000"))
    0.0

    :param ts: Timestamp (hh:mm:ss.nnn)
    :type ts: str
    :returns: timestamp in seconds
    :rtype: float
    :raises: :exc:`ValueError`: if timestamp is not formatted correctly
    '''
    if ts is None:
        raise ValueError("Timestamp cannot be empty")
    m = WEBVTT.match(ts)
    if not m:
        raise ValueError("Invalid VTT timestamp format ({})".format(ts))
    pd = m.groupdict()  # parts' dictionary
    secs = int(pd['hour']) * 3600
    secs += int(pd['min']) * 60
    secs += float(pd['sec'])
    return secs
