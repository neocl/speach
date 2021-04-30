.. _api_elan:

ELAN module
===========

``speach`` supports reading and manipulating multi-tier transcriptions from ELAN directly.

For common code samples to processing ELAN, see :ref:`tut_elan` page.
            
.. automodule:: speach.elan
   :members: read_eaf, parse_eaf_stream

.. autoclass:: ELANDoc
   :members:
   :member-order: groupwise
   :exclude-members: read_eaf, parse_eaf_stream

.. autoclass:: ELANTier
   :members:
   :member-order: groupwise
