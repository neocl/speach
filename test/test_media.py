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
from pathlib import Path

from speach import media


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = Path(os.path.abspath(__file__)).parent
TEST_OGG = TEST_DIR.parent / "./test_data/fables_01_03_aesop_64kb.ogg"
TEST_WAV = TEST_DIR.parent / "./test_data/fables_01_03_aesop_64kb.wav"


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

@unittest.skipIf(not media.version(), "ffmpeg is not available. TestMedia will be skipped! For more information see: https://ffmpeg.org")
class TestMedia(unittest.TestCase):

    def test_ffmpeg_version(self):
        ffmpeg_version = media.version()
        self.assertTrue(ffmpeg_version)
        print(f"Testing media with ffmpeg version {ffmpeg_version}")

    def test_locate_ffmpeg(self):
        ffmpeg_loc = media.locate_ffmpeg()
        self.assertTrue(ffmpeg_loc)
        self.assertIn('ffmpeg', ffmpeg_loc)

    def test_read_metadata(self):
        meta = media.metadata(TEST_OGG)
        expected = {'title': 'The Cat and the Mice',
                    'artist': 'Aesop',
                    'album': "Aesop's Fables Volume 1",
                    'Duration': '00:01:41.46',
                    'start': '0.025057',
                    'bitrate': '64 kb/s'}

    def test_convert(self):
        if TEST_WAV.is_file():
            TEST_WAV.unlink()
        media.convert(TEST_OGG, TEST_WAV, "-loglevel", "error")
        self.assertTrue(TEST_WAV.is_file())


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
