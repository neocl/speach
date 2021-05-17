# -*- coding: utf-8 -*-

"""
speach - a Python library for managing, annotating, and converting natural language corpuses
using popular formats (CoNLL, ELAN, Praat, CSV, JSON, SQLite, VTT, Audacity, TTL, TIG, ISF)
"""

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


from .__version__ import __author__, __email__, __copyright__, __maintainer__
from .__version__ import __credits__, __license__, __description__, __url__
from .__version__ import __version_major__, __version_long__, __version__, __status__

from chirptext import ttl
from . import ttlig as tig  # expose ttlig as tig
from .sqlite import TTLSQLite


__all__ = ['ttl', 'TTLSQLite', 'tig',
           "__version__", "__author__", "__description__", "__copyright__"]
