# -*- coding: utf-8 -*-

"""
Media processor module for cutting, converting media contents (audio, video, etc.)
"""

# This source code utilise ideas and sample processing codes from Victoria Chua
#     Github profile: https://github.com/vicchuayh
# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2021 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


import os
import sys
import logging
import platform
import subprocess
from pathlib import Path

# ------------------------------------------------------------
# Determine ffmpeg binary location
# ------------------------------------------------------------

WIN_EXE_POTENTIAL_PATHS = [
    "C:\\ffmpeg.exe",
    "C:\\ffmpeg\\ffmpeg.exe",
    "C:\\ffmpeg\\bin\\ffmpeg.exe",
    "C:\\Program Files\\ffmpeg\\ffmpeg.exe",
    "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
    os.path.expanduser("~ffmpeg.exe"),
    os.path.expanduser("~\\ffmpeg\\ffmpeg.exe"),
    os.path.expanduser("~\\ffmpeg\\bin\\ffmpeg.exe"),
    os.path.expanduser("~\\local\\ffmpeg\\ffmpeg.exe"),
    os.path.expanduser("~\\local\\ffmpeg\\bin\\ffmpeg.exe"),
]


if platform.system() == "Windows":
    _FFMPEG_PATH = None
    for _potential_path in WIN_EXE_POTENTIAL_PATHS:
        if Path(_potential_path).is_file():
            _FFMPEG_PATH = _potential_path
    if not _FFMPEG_PATH:
        # use any inkscape.exe in PATH as backup solution
        _FFMPEG_PATH = "ffmpeg.exe"
else:
    _FFMPEG_PATH = "/usr/bin/ffmpeg"


# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def _ffmpeg(*args, ffmpeg_path=None, capture_output=False, text=None, check=False):
    """ [Internal] Low level function call to ffmpeg

    This function should not be called by normal users.
    """
    if ffmpeg_path is None:
        ffmpeg_path = _FFMPEG_PATH
    logging.getLogger(__name__).debug("Executing {[ffmpeg_path]}")
    if sys.version_info.major == 3 and sys.version_info.minor >= 7:
        return subprocess.run([ffmpeg_path, *(str(x) for x in args)],
                              capture_output=capture_output,
                              text=text, check=check)
    else:
        if capture_output:
            output = subprocess.run([ffmpeg_path, *(str(x) for x in args)],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, check=check)
        else:
            output = subprocess.run([ffmpeg_path, *(str(x) for x in args)], check=check)
        return output.decoding(encoding='utf-8') if text else output


# ------------------------------------------------------------------------------
# media APIs
# ------------------------------------------------------------------------------

def version(ffmpeg_path=None):
    """ Determine using ffmpeg version 

    >>> from speach import media
    >>> media.version()
    '4.2.4-1ubuntu0.1'
    """
    output = _ffmpeg("-version", capture_output=True, text=True, ffmpeg_path=ffmpeg_path)
    version_line = output.stdout.splitlines()[0] if output and output.stdout else ''
    parts = version_line.split()
    if parts and len(parts) > 3 and parts[0] == 'ffmpeg' and parts[1] == 'version':
        return parts[2]
    else:
        return None


def locate_ffmpeg():
    """ locate the binary file of ffmpeg program (i.e. ffmpeg.exe) 

    >>> from speach import media
    >>> media.locate_ffmpeg()
    '/usr/bin/ffmpeg'
    """
    return _FFMPEG_PATH


def concat(*args, **kwargs):
    raise NotImplementedError()


def cut(*args, **kwargs):
    raise NotImplementedError()


def convert(infile, outfile, *args, ffmpeg_path=None):
    """ Convert an audio/video file into another format """
    if not infile:
        raise ValueError("Input file was not specified")
    elif not outfile:
        raise ValueError("Output file was not specified")
    elif not Path(infile).exists():
        raise FileNotFoundError(f"Input file {infile} does not exist")
    elif Path(outfile).exists():
        raise FileNotFoundError(f"Output file {infile} exists")
    else:
        args = ["-i", str(infile), str(outfile)]
        _ffmpeg(*args, ffmpeg_path=ffmpeg_path)
