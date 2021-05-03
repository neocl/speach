.. _recipe_media:

Media processing recipes
========================

:mod:`Media module <speach.media>` can be used to process audio and video files (converting, merging, cutting, et cetera).
``speach.media`` use ffmpeg underneath.

:mod:`Media module <speach.media>` requires ``ffmpeg``, for installation guide please refer to :ref:`install_ffmpeg`.

Basic
-----

Just import media module from speach library to start using it

>>> from speach import media

Convert media files
-------------------

converting the wave file ``test.wav`` in Documents folder into OGG format ``test.ogg``

>>> media.convert("~/Documents/test.wav", "~/Documents/test.ogg")

Cutting media files
-------------------

cutting ``test.wav`` from the beginning to 00:00:10 and write output to ``test_before10.ogg``

>>> media.cut("test.wav", "test_before10.ogg", to_ts="00:00:10")

cutting ``test.wav`` from 00:00:15 to the end of the file and write output to ``test_after15.ogg``
   
>>> media.cut("test.wav", ELAN_DIR / "test_after15.ogg", from_ts="00:00:15")

cutting ``test.wav`` from 00:00:15 to 00:00:15 and write output to ``test_10-15.ogg``

>>> media.cut(ELAN_DIR / "test.wav", ELAN_DIR / "test_10-15.ogg", from_ts="00:00:10", to_ts="00:00:15")

Using extra arguments
---------------------

When you process audio files using ffmpeg, sometimes you may want to use extra arguments,
such as codec information or filters, you may add the extra arguments **after** the standard arguments
of :mod:`speach.media` function calls. For example:

Setting async flag and audio codec

>>> media.convert("recording.wav", "recording.ogg", "-async", 1, "-c:a", "pcm_s16le")

Or in using ffmpeg demuxer commands

>>> concat_str = "file './recording.wav'\ninpoint 00:07:03\noutpoint 00:15:23.124"
>>> media.concat(concat_str, "outfile.ogg", "-segment_time_metadata",  1, "-af" , "asetnsamples=32,aselect=concatdec_select")

Querying ffmpeg information
---------------------------

>>> from speach import media
>>> media.version()
'4.2.4-1ubuntu0.1'
>>> media.locate_ffmpeg()
'/usr/bin/ffmpeg'

Others
------

For in-depth information and a complete API reference, please refer to :mod:`speach.media` API page.
