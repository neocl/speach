.. _recipe_media:

Media processing recipes
========================

:mod:`Media module <speach.media>` can be used to process audio and video files (converting, merging, cutting, et cetera).
``speach.media`` use ffmpeg underneath.

:mod:`Media module <speach.media>` requires ``ffmpeg``, for installation guide please refer to :ref:`install_ffmpeg`.

Sample code
-----------

Just import media module from speach library to start using it

>>> from speach import media

converting the wave file ``test.wav`` in Documents folder into OGG format ``test.ogg``

>>> media.convert("~/Documents/test.wav", "~/Documents/test.ogg")
       
cutting ``test.wav`` from the beginning to 00:00:10 and write output to ``test_before10.ogg``

>>> media.cut("test.wav", "test_before10.ogg", to_ts="00:00:10")

cutting ``test.wav`` from 00:00:15 to the end of the file and write output to ``test_after15.ogg``
   
>>> media.cut("test.wav", ELAN_DIR / "test_after15.ogg", from_ts="00:00:15")

cutting ``test.wav`` from 00:00:15 to 00:00:15 and write output to ``test_10-15.ogg``

>>> media.cut(ELAN_DIR / "test.wav", ELAN_DIR / "test_10-15.ogg", from_ts="00:00:10", to_ts="00:00:15")

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
