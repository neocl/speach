.. _updates:

Speach Changelog
================

Speach 0.1a11
-------------

- 2021-08-26

  - Add ``encoding`` option to ``eaf2csv`` command

Speach 0.1a10
-------------

- 2021-07-27

  - Support editing ELAN media fields

    - media_file
    - time_units
    - media_url
    - mime_type
    - relative_media_url

Speach 0.1a9
------------

- 2021-05-27

  - Use TTLv2 API (chirptext >= 0.2a4.post1)

Speach 0.1a8
------------

- 2021-05-27: Added some basic ELAN editing functions

  - Update participant codes
  - Update tier names
  - Update annotation texts

Speach 0.1a7
------------

- 2021-04-30

  - Added :func:`speach.elan.ELANDoc.cut` function to cut annotations to separate audio files.
  - Expand user home directory automatically when using :func:`speach.elan.read_eaf` function.
  - Module :mod:`speach.media` supports converting media files, cutting them by timestamps, and demuxer concat.
  - Package :ref:`Victoria Chua <contributors>`'s media processing code into ``speach.media`` module.

- 2021-04-28

  -  Initial release on PyPI
