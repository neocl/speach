.. speach documentation master file, created by
   sphinx-quickstart on Mon Mar 22 10:49:52 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to speach's documentation!
======================================

Speach (formerly `texttaglib <https://github.com/letuananh/texttaglib>`_) is a Python 3 library for managing, annotating, and converting natural language corpuses using popular formats (CoNLL, ELAN, Praat, CSV, JSON, SQLite, VTT, Audacity, TTL, TIG, ISF, etc.)

Main functions are:

- Text corpus management library
- Manipuling `ELAN <https://archive.mpi.nl/tla/elan/download>`_ transcription files directly in ELAN Annotation Format (eaf)
- TTLIG - A human-friendly intelinear gloss format for linguistic documentation
- Multiple storage formats (text files, JSON files, SQLite databases)

Installation
------------

Speach is availble on `PyPI <https://pypi.org/project/speach/>`_.

.. code:: bash

   pip install speach

ELAN support
------------

Speach can be used to extract annotations as well as metadata from ELAN transcripts, for example:

.. code:: python

    from speach import elan

    # Test ELAN reader function in speach
    eaf = elan.open_eaf('./test/data/test.eaf')

    # accessing tiers & annotations
    for tier in eaf:
        print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
        for ann in tier:
            print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts} :: {ann.to_ts}] {ann.text}")

Speach also provides command line tools for processing EAF files.

.. code:: bash

   # this command converts an eaf file into csv
   python -m speach eaf2csv input_elan_file.eaf -o output_file_name.csv

More information:

.. toctree::
   :maxdepth: 1

   tutorials
   recipes
   api
           
Useful Links
------------

- Speach documentation: https://speach.readthedocs.io/
- Speach on PyPI: https://pypi.org/project/speach/
- Soure code: https://github.com/neocl/speach/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
