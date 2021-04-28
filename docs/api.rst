Speach APIs
===============

An overview of ``speach`` modules.

.. module:: speach

ELAN supports
-------------

speach supports reading and manipulating multi-tier transcriptions from ELAN directly.
            
.. automodule:: speach.elan
   :members: open_eaf, parse_eaf_stream

.. autoclass:: ELANDoc
   :members:
   :member-order: groupwise

.. autoclass:: ELANTier
   :members:
   :member-order: groupwise

TTL Interlinear Gloss Format
----------------------------

TTLIG is a human friendly interlinear gloss format that can be edited using any text editor.
            
.. module:: speach.ttlig

TTL SQLite
----------

TTL supports SQLite storage format to manage large scale corpuses.
            
.. module:: speach.sqlite

WebVTT
------

Speach supports manipulating Web Video Text Tracks format (Web VTT).
Read more in :ref:`page_vtt` page.
