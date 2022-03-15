.. _updates:

Speach Changelog
================

Speach 0.1a15
-------------

- 2022-03-15

  - Use ``chirptext`` >= 0.2a6 for Python 3.10 and Python 3.11 support
  - Fixed missing lemmas bug in ``ttl_to_igrow()``
  - Fixed ``_xml_tostring()`` method for Python < 3.8

Speach 0.1a14
-------------

- 20022-03-09

  - Cross-check with controlled vocabularies when creating annotations if possible

- 2022-03-07

  - Allow to add new annotations to all 5 tier stereotypes

    - None (default root tiers)
    - Included In
    - Time Subdivision
    - Symbolic Subdivision
    - Symbolic Association

   - Support ``lxml`` when available

   - Support ``pretty_print`` in ``elan.Doc.to_xml_str()`` and ``elan.Doc.to_xml_bin()``

- 2022-03-02

  - Add ``speach.elan.create()`` function for creating a new ELAN file from scratch

- 2022-02-28

   - Add ``LOCALE`` support
   - Add Speach logo

Speach 0.1a13
-------------

- 2022-01-14

  - Use ``defusedxml`` automatically when available to parse XML for better security

Speach 0.1a12
-------------

- 2021-11-03

   - Support controlled vocabularies editing
      - Add new controlled vocabulary entries
      - Remove controlled vocabulary entries
      - Edit controlled vocabularies (values, desciptions, languages)
   - Add crc32 helper functions to ``speach.media`` module

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
