# speach

[![ReadTheDocs Badge](https://readthedocs.org/projects/speach/badge/?version=latest&style=plastic)](https://speach.readthedocs.io/)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/neocl/speach.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/neocl/speach/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/neocl/speach.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/neocl/speach/context:python)

Speach (formerly [texttaglib](https://github.com/letuananh/texttaglib/)), is a Python 3 library for managing, annotating, and converting natural language corpuses using popular formats (CoNLL, ELAN, Praat, CSV, JSON, SQLite, VTT, Audacity, TTL, TIG, ISF, etc.)

Main functions are:

- Text corpus management
- Manipuling [ELAN](https://archive.mpi.nl/tla/elan/download>) transcription files directly in ELAN Annotation Format (eaf)
- TIG - A human-friendly intelinear gloss format for linguistic documentation
- Multiple storage formats (text, CSV, JSON, SQLite databases)

## Useful Links

- Speach documentation: https://speach.readthedocs.io/
- Soure code: https://github.com/neocl/speach/

## Installation

Speach is availble on [PyPI](https://pypi.org/project/speach/).

```bash
pip install speach
```

## ELAN support

Speach can be used to extract annotations as well as metadata from ELAN transcripts, for example:

``` python
from speach import elan

# Test ELAN reader function in speach
eaf = elan.open_eaf('./test/data/test.eaf')

# accessing tiers & annotations
for tier in eaf:
    print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
    for ann in tier:
        print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts} :: {ann.to_ts}] {ann.text}")
```

Speach also provides command line tools for processing EAF files.

```bash
# this command converts an eaf file into csv
python -m speach eaf2csv input_elan_file.eaf -o output_file_name.csv
```

Read [Speach documentation](https://speach.readthedocs.io/) for more information.
