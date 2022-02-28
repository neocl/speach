.. speach documentation master file, created by
   sphinx-quickstart on Mon Mar 22 10:49:52 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

|SpeachLogo|_ SPeach - Documenting Natural languages
====================================================

.. |SpeachLogo| image:: _static/images/speach_logo.png
                       :width: 48px
.. _SpeachLogo: https://github.com/neocl/speach

Welcome to Speach's documentation!
Speach, formerly `texttaglib <https://github.com/letuananh/texttaglib>`_, is a Python 3 library for managing, annotating, and converting natural language corpuses using popular formats (CoNLL, ELAN, Praat, CSV, JSON, SQLite, VTT, Audacity, TTL, TIG, ISF, etc.)

Main functions:

- Text corpus management
- Manipulating `ELAN <https://archive.mpi.nl/tla/elan/download>`_ transcription files directly in ELAN Annotation Format (eaf)
- TIG - A human-friendly intelinear gloss format for linguistic documentation
- Multiple storage formats (text files, JSON files, SQLite databases)

:ref:`Contributors <contributors>` are welcome!
If you want to help developing ``speach``, please visit :ref:`contributing` page.
  
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
    eaf = elan.read_eaf('./test/data/test.eaf')

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
   contributing
   conduct
   updates
           
Useful Links
------------

- Soure code: https://github.com/neocl/speach/
- Speach on PyPI: https://pypi.org/project/speach/
- Speach documentation: https://speach.readthedocs.io/

Release Notes
-------------

Release notes is available :ref:`here <updates>`.

.. _contributors:

Contributors
------------

- `Le Tuan Anh <https://github.com/letuananh>`__ (Maintainer)
- `Victoria Chua <https://github.com/vicchuayh>`__

Graphic materials
~~~~~~~~~~~~~~~~~

The SPeach logo (|SpeachLogo|_) was created by using
the `snake emoji <https://openmoji.org/library/#author=Selina%20Bauder&emoji=1F40D>`__
(created by Selina Bauder)
and the `peach emoji <https://openmoji.org/library/#author=Marius%20Schnabel&emoji=1F351>`__
(created by Marius Schnabel)
from `Openmoji project <https://openmoji.org/about/>`__. License: `CC BY-SA 4.0 <https://github.com/dakside/openmoji/blob/master/LICENSE.txt>`__
 
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
