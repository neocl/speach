#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Victoria media module
"""

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import unittest
import logging

from speach import media


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

class TestMedia(unittest.TestCase):

    def test_ffmpeg_version(self):
        ffmpeg_version = media.version()
        self.assertTrue(ffmpeg_version)

    def test_locate_ffmpeg(self):
        ffmpeg_loc = media.locate_ffmpeg()
        self.assertTrue(ffmpeg_loc)
        self.assertIn('ffmpeg', ffmpeg_loc)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
