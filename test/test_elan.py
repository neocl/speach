#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test ELAN support
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import unittest
from pathlib import Path

from chirptext import chio

from speach import elan

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = Path(os.path.abspath(os.path.realpath(__file__))).parent
TEST_DATA = TEST_DIR / 'data'
TEST_EAF = TEST_DATA / 'test.eaf'


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

def read_eaf():
    return elan.open_eaf(TEST_EAF)


class TestELAN(unittest.TestCase):

    def test_read_elan(self):
        eaf = read_eaf()
        expected_tiernames = ['Person1 (Utterance)', 'marker', 'Person1 (Chunk)', 'Person1 (ChunkLanguage)', 'Person1 (Language)']
        actual_tiernames = [tier.ID for tier in eaf]
        self.assertEqual(expected_tiernames, actual_tiernames)
        annotations = []
        expected = [('How do you read this?', 1040, 2330),
                    ('このリンゴ、おいしいね！', 3200, 5050),
                    ('What does it mean?', 5510, 6350),
                    ('It means "This apple is delicious".', 7070, 9390),
                    ('"この" means this', 9670, 11340),
                    ('"リンゴ" means "apple"', 11780, 13110),
                    ('and "おいしい" means delicious.', 13490, 16090),
                    ('Oh thanks', 16615, 17485)]
        # find all annotations in utterance tier
        for ann in eaf['Person1 (Utterance)']:
            annotations.append((ann.text, ann.from_ts.value, ann.to_ts.value))
        self.assertEqual(annotations, expected)

    def test_elan_info(self):
        eaf = read_eaf()
        # test controlled vocab
        lang_vocab = eaf.get_vocab('Languages')
        actual = [repr(ve) for ve in lang_vocab]
        expected = ["ELANCVEntry(ID='cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc5', lang_ref='eng', value='en')",
                    "ELANCVEntry(ID='cveid_2fef57d6-45fc-4763-95d8-2dca63b043d7', lang_ref='eng', value='jp')"]
        self.assertEqual(expected, actual)
        # non-existence vocab
        boo_vocab = eaf.get_vocab('boo')
        self.assertIsNone(boo_vocab)
        # test participant map (participant code >> tier)
        pmap = {p: [t.ID for t in tiers] for p, tiers in eaf.get_participant_map().items()}
        expected = {'P001': ['Person1 (Utterance)',
                             'Person1 (Chunk)',
                             'Person1 (ChunkLanguage)',
                             'Person1 (Language)'],
                    '': ['marker']}
        self.assertEqual(pmap, expected)

    def test_eaf_to_csv(self):
        eaf = read_eaf()
        actual = eaf.to_csv_rows()
        expected = [tuple(row) for row in chio.read_tsv("./test/data/test.eaf.csv")]
        self.assertEqual(expected, actual)

    def test_write_elan(self):
        eaf = read_eaf()
        self.assertTrue(eaf.to_xml_bin())

    def test_ref_ann(self):
        eaf = read_eaf()
        ann = eaf['Person1 (Language)'][0]
        self.assertIsNotNone(ann.ref)
        self.assertEqual(ann.from_ts, 1040)
        self.assertEqual(ann.to_ts, 2330)
        self.assertEqual(ann.from_ts.sec, 1.04)
        self.assertEqual(ann.to_ts.sec, 2.33)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
