# speach

[![ReadTheDocs Badge](https://readthedocs.org/projects/speach/badge/?version=latest&style=plastic)](https://speach.readthedocs.io/)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/neocl/speach.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/neocl/speach/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/neocl/speach.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/neocl/speach/context:python)

Speach (formerly [texttaglib](https://github.com/letuananh/texttaglib/)), is a Python 3 library for managing, annotating, and converting natural language corpuses using popular formats (CoNLL, ELAN, Praat, CSV, JSON, SQLite, VTT, Audacity, TTL, TTLIG, ISF, etc.)

Main functions are:

- Reading, editing, and writing ELAN transcriptions and related media files directly in [ELAN Annotation Format](https://archive.mpi.nl/tla/elan/download) (eaf)
- Cutting, converting, and merging audio/video files
- TTLIG (or TIG) - A human-friendly linguistic documentation format with intelinear gloss support
- Text corpus management using texttaglib format
- Multiple storage formats (text, CSV, JSON, SQLite databases)

## Useful Links

- Speach documentation: https://speach.readthedocs.io/
- Source code: https://github.com/neocl/speach/

## Installation

`speach` is available on [PyPI](https://pypi.org/project/speach/).

```bash
pip install speach
```

## Sample codes

Speach can extract annotations and metadata from ELAN transcripts directly, for example:

``` python
from speach import elan

# Test ELAN reader function in speach
eaf = elan.read_eaf('./test/data/test.eaf')

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

Processing media files

```python
>>> from speach import media
>>> media.convert("~/Documents/test.wav", "~/Documents/test.ogg")
>>> media.cut("test.wav", "test_10-15.ogg", from_ts="00:00:10", to_ts="00:00:15")
```

Read [Speach documentation](https://speach.readthedocs.io/) for more information.

## Contributors

- [Le Tuan Anh](https://github.com/letuananh) (Maintainer)
- [Victoria Chua](https://github.com/vicchuayh)

Contributors are welcome! If you want to help developing speach, please visit [Contributing](https://speach.readthedocs.io/en/latest/contributing.html) page.