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

speach library contains a command line tool for converting EAF files into CSV.

```bash
python -m speach eaf2csv input_elan_file.eaf -o output_file_name.csv
```

For more complex analyses, speach Python scripts can be used to extract metadata and annotations from ELAN transcripts, for example:

``` python
from speach import elan

# Test ELAN reader function in speach
eaf = elan.open_eaf('./test/data/test.eaf')

# accessing metadata
print(f"Author: {eaf.author} | Date: {eaf.date} | Format: {eaf.fileformat} | Version: {eaf.version}")
print(f"Media file: {eaf.media_file}")
print(f"Time units: {eaf.time_units}")
print(f"Media URL: {eaf.media_url} | MIME type: {eaf.mime_type}")
print(f"Media relative URL: {eaf.relative_media_url}")

# accessing tiers & annotations
for tier in eaf.tiers():
    print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
    for ann in tier.annotations:
        print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")
```

## Text corpus

```python
>>> from speach import ttl
>>> doc = ttl.Document('mydoc')
>>> sent = doc.new_sent("I am a sentence.")
>>> sent
#1: I am a sentence.
>>> sent.ID
1
>>> sent.text
'I am a sentence.'
>>> sent.import_tokens(["I", "am", "a", "sentence", "."])
>>> >>> sent.tokens
[`I`<0:1>, `am`<2:4>, `a`<5:6>, `sentence`<7:15>, `.`<15:16>]
>>> doc.write_ttl()
```

The script above will generate this corpus

```
-rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_concepts.txt
-rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_links.txt
-rw-rw-r--.  1 tuananh tuananh      20  3月 29 13:10 mydoc_sents.txt
-rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_tags.txt
-rw-rw-r--.  1 tuananh tuananh      58  3月 29 13:10 mydoc_tokens.txt
```
