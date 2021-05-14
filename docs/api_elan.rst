.. _api_elan:

ELAN module
===========

``speach`` supports reading and manipulating multi-tier transcriptions from ELAN directly.

For common code samples to processing ELAN, see :ref:`recipe_elan` page.

.. contents:: Table of Contents
    :depth: 3

ELAN module functions
---------------------

.. automodule:: speach.elan
   :members: read_eaf, parse_eaf_stream, parse_string
   :member-order: bysource

ELAN Document model
-------------------

.. autoclass:: Doc
   :members:
   :member-order: groupwise
   :exclude-members: read_eaf, parse_eaf_stream

ELAN Tier model
---------------

.. autoclass:: Tier
   :members:
   :member-order: groupwise

ELAN Annotation model
---------------------

There are two different annotation types in ELAN: :class:`TimeAnnotation` and :class:`RefAnnotation`.
TimeAnnotation objects are time-alignable annotations and contain timestamp pairs ``from_ts, to_ts``
to refer back to specific chunks in the source media.
On the other hand, RefAnnotation objects are annotations that link to something else, such as another annotation
or an annotation sequence in the case of symbolic subdivision tiers.

.. autoclass:: TimeAnnotation
   :members:
   :member-order: groupwise

.. autoclass:: RefAnnotation
   :members:
   :member-order: groupwise

.. autoclass:: Annotation
   :members:
   :member-order: groupwise

.. autoclass:: TimeSlot
   :members:
   :member-order: groupwise