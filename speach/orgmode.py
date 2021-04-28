# -*- coding: utf-8 -*-

'''
org-mode support
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


import re
import os
import logging

from chirptext import chio


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


RE_TITLE = re.compile('#\+TITLE: (?P<title>.+)$')
RE_META = re.compile('- (?P<tag>.+) :: (?P<value>.+)$')


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

def _match_title(line):
    m = RE_TITLE.match(line)
    if m:
        return m.group('title')
    else:
        return None


def _match_meta(line):
    m = RE_META.match(line)
    if m:
        return (m.group('tag'), m.group('value'))
    else:
        return None


def _parse_stream(input_stream):
    title = None
    meta = []
    reading_header = True
    lines = []
    for idx, line in enumerate(input_stream):
        if idx == 0:
            m = _match_title(line)
            if m:
                title = m
                continue
        # not title
        if reading_header:
            m = _match_meta(line)
            if m:
                meta.append(m)
                continue
            else:
                # not a meta line
                reading_header = False
                if not line.strip():
                    # ignore the first empty line after meta lines
                    continue
        # add to lines
        lines.append(line)
    return (title, meta, lines)


def read(filepath, **kwargs):
    with chio.open(filepath, mode='r') as infile:
        title, meta, lines = _parse_stream(infile)
        meta.append(('Filename', os.path.basename(filepath)))
        for k, v in kwargs.items():
            meta.append((k, v))
    return (title, meta, lines)


def org_to_ttlig(title, meta, lines, line_processor=None):
    iglines = ['# TTLIG']
    # add title
    if title:
        iglines.append("Title: {}".format(title))
    # add meta
    for k, v in meta:
        iglines.append("{}: {}".format(k, v))
    # add an empty between meta and content
    if meta:
        iglines.append('')

    # add lines
    for line in lines:
        if line_processor:
            line_processor(line, iglines)
        else:
            iglines.append(line)
    return iglines
