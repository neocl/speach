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
        expected = [('Person1 (Utterance)', 'P001', '1.040', '2.330', '1.290', 'How do you read this?'),
                    ('Person1 (Utterance)', 'P001', '3.200', '5.050', '1.850', 'このリンゴ、おいしいね！'),
                    ('Person1 (Utterance)', 'P001', '5.510', '6.350', '0.840', 'What does it mean?'),
                    ('Person1 (Utterance)', 'P001', '7.070', '9.390', '2.320', 'It means "This apple is delicious".'),
                    ('Person1 (Utterance)', 'P001', '9.670', '11.340', '1.670', '"この" means this'),
                    ('Person1 (Utterance)', 'P001', '11.780', '13.110', '1.330', '"リンゴ" means "apple"'),
                    ('Person1 (Utterance)', 'P001', '13.490', '16.090', '2.600', 'and "おいしい" means delicious.'),
                    ('Person1 (Utterance)', 'P001', '16.615', '17.485', '0.870', 'Oh thanks'),
                    ('marker', '', '0.830', '5.200', '4.370', 'convo start'),
                    ('marker', '', '6.890', '16.260', '9.370', 'convo body'),
                    ('marker', '', '16.523', '17.570', '1.047', 'convo end'),
                    ('Person1 (Chunk)', 'P001', '1.040', '2.330', '1.290', 'How do you read this?'),
                    ('Person1 (Chunk)', 'P001', '3.200', '5.050', '1.850', 'このリンゴ、おいしいね！'),
                    ('Person1 (Chunk)', 'P001', '5.510', '6.350', '0.840', 'What does it mean?'),
                    ('Person1 (Chunk)', 'P001', '7.070', '9.390', '2.320', 'It means "This apple is delicious".'),
                    ('Person1 (Chunk)', 'P001', '9.731', '10.281', '0.550', 'この'),
                    ('Person1 (Chunk)', 'P001', '10.554', '11.240', '0.686', 'means "this"'),
                    ('Person1 (Chunk)', 'P001', '11.870', '12.303', '0.433', ' リンゴ'),
                    ('Person1 (Chunk)', 'P001', '12.498', '13.041', '0.543', 'means "apple"'),
                    ('Person1 (Chunk)', 'P001', '13.660', '13.915', '0.255', 'and'),
                    ('Person1 (Chunk)', 'P001', '13.915', '14.711', '0.796', 'おいしい'),
                    ('Person1 (Chunk)', 'P001', '14.882', '15.908', '1.026', 'means "delicious"'),
                    ('Person1 (Chunk)', 'P001', '16.615', '17.485', '0.870', 'oh thanks'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'jp'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'jp'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'jp'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'jp'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (ChunkLanguage)', 'P001', '', '', '', 'en'),
                    ('Person1 (Language)', 'P001', '', '', '', 'en'),
                    ('Person1 (Language)', 'P001', '', '', '', 'jp'),
                    ('Person1 (Language)', 'P001', '', '', '', 'en'),
                    ('Person1 (Language)', 'P001', '', '', '', 'en'),
                    ('Person1 (Language)', 'P001', '', '', '', 'en'),
                    ('Person1 (Language)', 'P001', '', '', '', 'en'),
                    ('Person1 (Language)', 'P001', '', '', '', 'en'),
                    ('Person1 (Language)', 'P001', '', '', '', 'en')]
        self.assertEqual(expected, actual)

    def test_write_elan(self):
        eaf = read_eaf()
        self.assertTrue(eaf.to_xml_bin())


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
