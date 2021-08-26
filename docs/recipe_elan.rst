.. _recipe_elan:

ELAN Recipes
============

Common snippets for processing ELAN transcriptions with ``speach``.

For in-depth API reference, see :ref:`api_elan` page.

Open an ELAN file
-----------------

    >>> from speach import elan
    >>> eaf = elan.read_eaf('./data/test.eaf')
    >>> eaf
    <speach.elan.Doc object at 0x7f67790593d0>

Save an ELAN transcription to a file
------------------------------------

After edited an :class:`speach.elan.Doc` object, its content can be saved to an EAF file like this

   >>> eaf.save("test_edited.eaf")

Parse an existing text stream
-----------------------------

If you have an input stream ready, you can parse its content with :meth:`speach.elan.parse_eaf_stream` method.

.. code-block:: python

    >>> from speach import elan
    >>> with open('./data/test.eaf', encoding='utf-8') as eaf_stream:
    >>> ...  eaf = elan.parse_eaf_stream(eaf_stream)
    >>> ...
    >>> eaf
    <speach.elan.Doc object at 0x7f6778f7a9d0>

Accessing tiers & annotations
-----------------------------

You can loop through all tiers in an :class:`speach.elan.Doc` object (i.e. an eaf file)
and all annotations in each tier using Python's ``for ... in ...`` loops.
For example:

.. code-block:: python

    for tier in eaf:
        print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
        for ann in tier:
            print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.text}")

Accessing nested tiers in ELAN
------------------------------

If you want to loop through the root tiers only, you can use the :code:`roots` list of an :class:`speach.elan.Doc`:

.. code-block:: python

    eaf = elan.read_eaf('./data/test_nested.eaf')
    # accessing nested tiers
    for tier in eaf.roots:
        print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
        for child_tier in tier.children:
            print(f"    | {child_tier.ID} | Participant: {child_tier.participant} | Type: {child_tier.type_ref}")
            for ann in child_tier.annotations:
                print(f"    |- {ann.ID.rjust(4, ' ')}. [{ann.from_ts} -- {ann.to_ts}] {ann.text}")

Retrieving a tier by name
-------------------------

All tiers are indexed in :class:`speach.elan.Doc` and can be accessed using Python indexer operator.
For example, the following code loop through all annotations in the tier ``Person1 (Utterance)`` and
print out their text values:

    >>> p1_tier = eaf["Person1 (Utterance)"]
    >>> for ann in p1_tier:
    >>>     print(ann.text)

Cutting annotations to separate audio files
-------------------------------------------

Annotations can be cut and stored into separate audio files using :func:`speach.elan.ELANDoc.cut` method.

.. code-block:: python

   eaf = elan.read_eaf(ELAN_DIR / "test.eaf")
   for idx, ann in enumerate(eaf["Person1 (Utterance)"], start=1):
       eaf.cut(ann, ELAN_DIR / f"test_person1_{idx}.ogg")
                
Converting ELAN files to CSV
----------------------------

``speach`` includes a command line tool to convert an EAF file into CSV.

.. code-block:: bash

   python -m speach eaf2csv path/to/my_transcript.eaf -o path/to/my_transcript.csv

By default, speach generate output using ``utf-8`` and this should be useful for general uses.
However in some situations users may want to customize the output encoding.
For example Microsoft Excel on Windows may require a file to be encoded in ``utf-8-sig`` (UTF-8 file with explicit BOM signature in the beginning of the file) to recognize it as an UTF-8 file.
It is possible to specify output encoding using the keyword ``encoding``, as in the example below:

.. code-block:: bash

    python -m speach eaf2csv my_transcript.eaf -o my_transcript.csv  --encoding=utf-8-sig

