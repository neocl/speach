#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test ORG-mode
"""

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import io
import unittest
import logging

from speach import orgmode


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_ORG = '''#+TITLE: まだらの紐
- author :: アーサー・コナン・ドイル
- genre :: 短編小説

同様に、悲しみそのものを、それが悲しみであるという理由で愛する者や、それゆえ得ようとする者は、どこにもいない。
同様に、悲しみそのものを、それが悲しみであるという理由で愛する者や、それゆえ得ようとする者は、どこにもいない。
同様に、悲しみそのものを、それが悲しみであるという理由で愛する者や、それゆえ得ようとする者は、どこにもいない。
'''


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------


class TestOrgMode(unittest.TestCase):

    def test_title(self):
        title = orgmode._match_title('#+TITLE: まだらの紐\n')
        self.assertEqual(title, 'まだらの紐')

    def test_meta(self):
        k, v = orgmode._match_meta('- genre :: fiction')
        self.assertEqual((k, v), ('genre', 'fiction'))

    def test_parse(self):
        instream = io.StringIO(TEST_ORG)
        t, m, l = orgmode._parse_stream(instream)
        self.assertEqual(t, 'まだらの紐')
        self.assertEqual(m, [('author', 'アーサー・コナン・ドイル'), ('genre', '短編小説')])
        self.assertEqual(len(l), 3)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
