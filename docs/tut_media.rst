.. _tut_media:

Media processing tutorial
=========================

:mod:`Media module <speach.media>` can be used to process audio and video files (converting, merging, cutting, et cetera).
``speach.media`` use ffmpeg underneath.

.. _install_ffmpeg:

Installing ffmpeg
-----------------

Linux
~~~~~

It is very likely that your Linux distribution comes with a default ``ffmpeg`` package under ``/usr/bin/ffmpeg``.

Windows
~~~~~~~

.. note::
   To be updated (download and install to ``C:\\Users\\<account_name>\\local\\ffmpeg\\ffmpeg.exe``)

Mac OS
~~~~~~

You can download ffmpeg binary file from https://ffmpeg.org and copy it to one of these folders

- /Users/<account_name>/ffmpeg
- /Users/<account_name>/bin/ffmpeg
- /Users/<account_name>/local/ffmpeg
- /Users/<account_name>/local/ffmpeg/ffmpeg

and ``speach`` will find it automatically.
