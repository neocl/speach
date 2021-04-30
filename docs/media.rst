.. _tut_media:

Media processing tutorial
==========================

:mod:`Media module <speach.media>` can be used to process audio and video files (converting, merging, cutting, et cetera).
``speach.media`` use ffmpeg underneath.

Installing ffmpeg
-----------------

.. note::
   To be updated

Sample code
-----------
   
.. code:: python

   from speach import media
   print(media.version())
   print(media.locate_ffmpeg())
   media.convert("infile.mp3", "outfile.wav")

Others
------

For in-depth information and a complete API reference, please refer to :mod:`speach.media` API page.
