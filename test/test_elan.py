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
TEST_TSV = TEST_DATA / 'test.eaf.tsv'
TEST_EAF2 = TEST_DIR / '../test_data/fables_01_03_aesop_64kb.eaf'


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

def read_eaf():
    return elan.read_eaf(TEST_EAF)


class TestELAN(unittest.TestCase):

    def test_read_elan(self):
        eaf = read_eaf()
        expected_tiernames = ['Person1 (Utterance)', 'marker', 'Person1 (Chunk)', 'Person1 (ChunkLanguage)',
                              'Person1 (Language)']
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
        expected = ["CVEntry(ID='cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc5', lang_ref='eng', value='en')",
                    "CVEntry(ID='cveid_2fef57d6-45fc-4763-95d8-2dca63b043d7', lang_ref='eng', value='jp')"]
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
        expected = [tuple(row) for row in chio.read_tsv(TEST_TSV)]
        self.assertEqual(expected, actual)

    def test_write_elan(self):
        eaf = read_eaf()
        xml_content = eaf.to_xml_str()
        self.assertTrue(xml_content)
        # parse the XML content back to EAF
        eaf2 = elan.parse_string(xml_content)
        self.assertEqual(eaf.to_csv_rows(), eaf2.to_csv_rows())

    def test_ref_ann(self):
        eaf = read_eaf()
        ann = eaf['Person1 (Language)'][0]
        self.assertIsNotNone(ann.ref)
        self.assertEqual(ann.from_ts, 1040)
        self.assertEqual(ann.to_ts, 2330)
        self.assertEqual(ann.from_ts.sec, 1.04)
        self.assertEqual(ann.to_ts.sec, 2.33)

    def test_elan_sample2(self):
        eaf = elan.read_eaf(TEST_EAF2)
        # test languages
        self.assertTrue(eaf.languages)
        self.assertEqual(eaf.languages[0].lang_def, "http://cdb.iso.org/lg/CDB-00130975-001")
        # test licenses
        self.assertTrue(eaf.licenses)
        self.assertEqual(eaf.licenses[0].url, "https://creativecommons.org/licenses/by/4.0/")
        # test external resource
        self.assertTrue(eaf.external_refs)
        self.assertEqual(eaf.external_refs[0].value, "file:/home/tuananh/Documents/ELAN/fables_cv.ecv")


class TestEditElan(unittest.TestCase):

    def test_edit_elan(self):
        eaf = read_eaf()
        actual_pre = [(t.ID, t.participant, t.parent.ID if t.parent else None) for t in eaf]
        expected_pre = [('Person1 (Utterance)', 'P001', None),
                        ('marker', '', None),
                        ('Person1 (Chunk)', 'P001', 'Person1 (Utterance)'),
                        ('Person1 (ChunkLanguage)', 'P001', 'Person1 (Chunk)'),
                        ('Person1 (Language)', 'P001', 'Person1 (Utterance)')]
        self.assertEqual(expected_pre, actual_pre)
        marker_annotations_pre = [(ann.value, ann.from_ts.value, ann.to_ts.value) for ann in eaf["marker"]]
        expected_annotations_pre = [('convo start', 830, 5200),
                                    ('convo body', 6890, 16260),
                                    ('convo end', 16523, 17570)]
        self.assertEqual(marker_annotations_pre, expected_annotations_pre)
        # edit tier name
        eaf["Person1 (Utterance)"].name = "Person1-Utterance"
        # edit participant
        for tier in eaf:
            if tier.participant == "P001":
                tier.participant = "P999"
        eaf["marker"].participant = "leta"
        # edit annotation value
        for ann in eaf["marker"]:
            if ann.text.startswith("convo "):
                ann.text = ann.text.replace("convo ", ":convo:")
        # serialize
        eaf2 = elan.parse_string(eaf.to_xml_str())
        actual = [(t.ID, t.participant, t.parent.ID if t.parent else None) for t in eaf2]
        expected = [('Person1-Utterance', 'P999', None),
                    ('marker', 'leta', None),
                    ('Person1 (Chunk)', 'P999', 'Person1-Utterance'),
                    ('Person1 (ChunkLanguage)', 'P999', 'Person1 (Chunk)'),
                    ('Person1 (Language)', 'P999', 'Person1-Utterance')]
        self.assertEqual(expected, actual)
        marker_annotations = [(ann.value, ann.from_ts.value, ann.to_ts.value) for ann in eaf2["marker"]]
        expected_annotations = [(':convo:start', 830, 5200), (':convo:body', 6890, 16260), (':convo:end', 16523, 17570)]
        self.assertEqual(marker_annotations, expected_annotations)
        self.assertEqual(eaf.to_csv_rows(), eaf2.to_csv_rows())

    def test_updating_media_url(self):
        eaf = read_eaf()
        self.assertEqual(eaf.media_file, '')
        self.assertEqual(eaf.media_url, 'file:///home/tuananh/Documents/ELAN/test.wav')
        self.assertEqual(eaf.relative_media_url, './test.wav')
        self.assertEqual(eaf.media_path(), '/home/tuananh/Documents/ELAN/test.wav')
        eaf.media_file = 'test2.wav'
        eaf.media_url = 'file:///home/user/Documents/ELAN/test2.wav'
        eaf.relative_media_url = './test2.wav'
        eaf2 = elan.parse_string(eaf.to_xml_str())
        self.assertEqual(eaf2.media_file, 'test2.wav')
        self.assertEqual(eaf2.media_url, 'file:///home/user/Documents/ELAN/test2.wav')
        self.assertEqual(eaf2.relative_media_url, './test2.wav')
        self.assertEqual(eaf2.media_path(), '/home/user/Documents/ELAN/test2.wav')


    def test_edit_elan_participant_code(self):
        eaf = elan.read_eaf(TEST_DATA / "test2.eaf")
        participants = [(t.participant, t.name) for t in eaf]
        expected = [('P001', 'Person1 (Utterance)'),
                    ('', 'marker'),
                    ('P001', 'Person1 (Chunk)'),
                    ('P001', 'Person1 (ChunkLanguage)'),
                    ('P001', 'Person1 (Language)'),
                    ('R004001', 'R004 (Utterance)')]
        self.assertEqual(expected, participants)
        # edit the participant list
        for tier in eaf:
            if not tier.participant:
                tier.participant = "nobody"
            elif "001" in tier.participant:
                orig_participant = tier.participant
                tier.participant = tier.participant.replace("001", "x")
        eaf.save(TEST_DATA / 'test2_edited.eaf')
        # read it back
        eaf2 = elan.read_eaf(TEST_DATA / 'test2_edited.eaf')
        participants2 = [(t.participant, t.name) for t in eaf2]
        expected2 = [('Px', 'Person1 (Utterance)'),
                     ('nobody', 'marker'),
                     ('Px', 'Person1 (Chunk)'),
                     ('Px', 'Person1 (ChunkLanguage)'),
                     ('Px', 'Person1 (Language)'),
                     ('R004x', 'R004 (Utterance)')]
        self.assertEqual(expected2, participants2)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
