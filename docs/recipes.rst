Common Recipes
==============

Here are code snippets for common usecases of speach

Open an ELAN file
-----------------

    >>> from speach import elan
    >>> eaf = elan.open_eaf('./data/test.eaf')
    >>> eaf
    <speach.elan.ELANDoc object at 0x7f67790593d0>

Parse an existing text stream
-----------------------------

.. code-block:: python

    >>> from speach import elan
    >>> with open('./data/test.eaf') as eaf_stream:
    >>> ...  eaf = elan.parse_eaf_stream(eaf_stream)
    >>> ...
    >>> eaf
    <speach.elan.ELANDoc object at 0x7f6778f7a9d0>

Accessing tiers & annotations
-----------------------------

.. code-block:: python

    for tier in eaf.tiers():
        print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
        for ann in tier.annotations:
            print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")

Accessing nested tiers in ELAN
------------------------------

.. code-block:: python

    eaf = elan.open_eaf('./data/test_nested.eaf')
    # accessing nested tiers
    for tier in eaf.roots:
        print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
        for child_tier in tier.children:
            print(f"    | {child_tier.ID} | Participant: {child_tier.participant} | Type: {child_tier.type_ref}")
            for ann in child_tier.annotations:
                print(f"    |- {ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")
         
Converting ELAN files to CSV
----------------------------

speach includes a command line tool to convert an EAF file into CSV.

.. code-block:: bash

   python -m speach eaf2csv my_transcript.eaf -o my_transcript.csv
