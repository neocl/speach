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
import tempfile
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

OTHER_POTENTIAL_PATHS = [
    "/usr/bin/ffmpeg",
    "/usr/local/bin/ffmpeg",
    "~/local/ffmpeg",
    "~/local/ffmpeg/ffmpeg",
    "~/ffmpeg",
    "~/ffmpeg/ffmpeg",
    "~/bin/ffmpeg"
]


_FFMPEG_PATH = None
if platform.system() == "Windows":
    for _potential_path in WIN_EXE_POTENTIAL_PATHS:
        if Path(_potential_path).is_file():
            _FFMPEG_PATH = _potential_path
    if not _FFMPEG_PATH:
        # use any inkscape.exe in PATH as backup solution
        _FFMPEG_PATH = "ffmpeg.exe"
else:
    for _potential_path in OTHER_POTENTIAL_PATHS:
        if Path(_potential_path).is_file():
            _FFMPEG_PATH = _potential_path
    if not _FFMPEG_PATH:
        _FFMPEG_PATH = "ffmpeg"


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
            procinfo = subprocess.run([ffmpeg_path, *(str(x) for x in args)],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=check)
        else:
            procinfo = subprocess.run([ffmpeg_path, *(str(x) for x in args)], check=check)
        # Python < 3.7 does not support kwarg text
        if text:
            if procinfo.stdout:
                procinfo.stdout = procinfo.stdout.decode(encoding='utf-8')
            if procinfo.stderr:
                procinfo.stderr = procinfo.stderr.decode(encoding='utf-8')
        return procinfo


def _norm_path(p):
    return os.path.expanduser(p) if p.startswith("~") else p


def _validate_outfile(outfile):
    _p = _norm_path(str(outfile))
    if not outfile:
        raise ValueError("Output file was not specified")
    elif os.path.exists(_p):
        raise FileExistsError(f"Output file {outfile} exists")
    return _p


def _validate_infile(infile):
    _p = _norm_path(str(infile))
    if not infile:
        raise ValueError("Input file was not specified")
    elif not os.path.isfile(_p):
        raise FileNotFoundError(f"Input file {infile} does not exist")
    return _p


def _validate_args(infile, outfile):
    return _validate_infile(infile), _validate_outfile(outfile)


# ------------------------------------------------------------------------------
# media APIs
# ------------------------------------------------------------------------------

def version(ffmpeg_path=None):
    """ Determine using ffmpeg version

    >>> from speach import media
    >>> media.version()
    '4.2.4-1ubuntu0.1'
    """
    try:
        output = _ffmpeg("-version", capture_output=True, text=True, ffmpeg_path=ffmpeg_path, check=False)
    except FileNotFoundError:
        return None
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


def concat(text, outfile, dir=None, *args, **kwargs):
    """ Process a ffmpeg demuxer file and write result to outfile

    Read more: https://trac.ffmpeg.org/wiki/Concatenate

    :param text: demuxer content string, which will be written to a temporary file before calling
    :type text: str
    :param outfile: path to an output file
    :param dir: The directory to create the temp demuxer file, leave as None to use Python default temp dir
    """
    outfile = _validate_outfile(outfile)
    with tempfile.TemporaryFile(mode="wt", dir=dir) as concat_file:
        concat_file.write(text)
        return _ffmpeg("-f", "concat",
                       "-segment_time_metadata", 1,
                       "-i", concat_file.name,
                       *args,
                       outfile, **kwargs)


def cut(infile, outfile, from_ts=None, to_ts=None, use_concat=False, *args, **kwargs):
    """ Cut a media file from a timestamp to another timestamp

    To cut myfile.wav from ``00:03:12`` to the end of the file and write output to outfile.ogg

    >>> media.cut("myfile.wav", "outfile.ogg", from_ts="00:03:12")

    To cut myfile.wav from the beginning to ``00:04:27`` and then write output to outfile.ogg

    >>> media.cut("myfile.wav", "outfile.ogg", to_ts="00:04:27")

    When use_concat is set to True, both from_ts and to_ts must be specified

    >>> media.cut("myfile.wav", "outfile.ogg", from_ts="00:03:12", to_ts="00:04:27", use_concat=True)

    :param infile: Path to an existing file (in str or Path-like object)
    :param outfile: Path to output file (must not exist, or else a FileExistsError will be raised)
    :param from_ts: Leave as None to start cutting from the beginning
    :type from_ts: a timestamp string or a TimeSlot object
    :param to_ts: Timestamp to end cutting. Leave as None to cut to the end of the file
    :type to_ts: a timestamp string or a TimeSlot object
    :param use_concat: Set to True to use demuxer to cut audio file. Both from_ts and to_ts must be specified when use. Defaulted to None
    """
    infile, outfile = _validate_args(infile, outfile)
    if from_ts is None and to_ts is None:
        raise ValueError("from_ts and to_ts cannot be both None")
    if use_concat and (from_ts is None or to_ts is None):
        raise ValueError("when use_concat is True, both from_ts and to_ts must be defined")
    if not use_concat:
        # use -ss
        if from_ts is None or str(from_ts) in ["0", "00:00:00", "00:00:00.000"]:
            _ffmpeg("-i", infile, "-to", to_ts, *args, outfile)
        elif to_ts is not None:
            _ffmpeg("-i", infile, "-ss", from_ts, "-to", to_ts, *args, outfile)
        else:
            _ffmpeg("-i", infile, "-ss", from_ts, *args, outfile)
    else:
        concat_text = "\n".join([f"file '{infile}'",
                                 f"inpoint {from_ts}",
                                 f"outpoint {to_ts}"])
        concat(concat_text, outfile)


def convert(infile, outfile, *args, ffmpeg_path=None):
    """ Convert an audio/video file into another format

    To convert the file ``test.wav`` in Music folder under current user's home directory
    into ``output.ogg``

    >>> from speach import media
    >>> media.convert("~/Music/test.wav", "~/Music/output.ogg")
    """
    infile, outfile = _validate_args(infile, outfile)
    _ffmpeg("-i", str(infile), *args, str(outfile), ffmpeg_path=ffmpeg_path)


def metadata(infile, *args, ffmpeg_path=None):
    """ Read metadata of a given media file
    """
    _proc = _ffmpeg("-i", str(infile), capture_output=True, text=True, ffmpeg_path=ffmpeg_path)
    # ffmpeg output metadata to stderr instead of stdout
    lines = _proc.stderr.splitlines()
    meta = {}
    for l in lines:
        if l.startswith("    title"):
            meta["title"] = l.split(":", maxsplit=1)[1].strip()
        elif l.startswith("    artist"):
            meta["artist"] = l.split(":", maxsplit=1)[1].strip()
        elif l.startswith("    album"):
            meta["album"] = l.split(":", maxsplit=1)[1].strip()
        elif l.startswith("  Duration:"):
            parts = l.split(",")
            for p in parts:
                k, v = p.split(":", maxsplit=1)
                meta[k.strip()] = v.strip()
    return meta
