#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test ELAN support
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

from datetime import datetime
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
TEST_ECV2 = TEST_DIR / '../test_data/test_speach.ecv'


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

def read_eaf():
    return elan.read_eaf(TEST_EAF)


class TestELAN(unittest.TestCase):

    def test_safe_mode(self):
        print(f"ELAN safe mode: {elan.SAFE_MODE}")
        print(f"ELAN XML parser: {elan.best_parser.__name__}")

    def test_pretty_print(self):
        x = elan.create().to_xml_bin(pretty_print=True)
        self.assertTrue(x)
        x = elan.create().to_xml_str(pretty_print=True)
        self.assertTrue(x)

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

    def test_elan_locale(self):
        loc = elan.Locale(language_code='vi')
        self.assertEqual(repr(loc), "Locale(language_code='vi')")
        self.assertEqual(str(loc), 'vi')
        eaf = elan.read_eaf(TEST_EAF2)
        self.assertEqual(repr(eaf.locale), "Locale(country_code='GB', language_code='en')")
        self.assertEqual(str(eaf.locale), 'en')

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

    def test_new_elan(self):
        # test creating a new EAF file from scratch
        eaf = elan.create(media_file='test.wav',
                          author='Le Tuan Anh')
        eaf = elan.parse_string(eaf.to_xml_str())
        self.assertEqual(eaf.media_file, 'test.wav')
        self.assertEqual(eaf.media_url, 'test.wav')
        self.assertEqual(eaf.relative_media_url, 'test.wav')
        # set relative_media_url
        eaf = elan.create(media_file='test.wav',
                          relative_media_url='./test.wav',
                          author='Le Tuan Anh')
        eaf = elan.parse_string(eaf.to_xml_str())
        self.assertEqual(eaf.media_file, 'test.wav')
        self.assertEqual(eaf.media_url, 'test.wav')
        self.assertEqual(eaf.relative_media_url, './test.wav')
        # set media_url
        eaf = elan.create(media_file='test.wav',
                          media_url='/home/tuananh/test.wav',
                          author='Le Tuan Anh')
        eaf = elan.parse_string(eaf.to_xml_str())
        self.assertEqual(eaf.media_file, 'test.wav')
        self.assertEqual(eaf.media_url, '/home/tuananh/test.wav')
        self.assertEqual(eaf.relative_media_url, 'test.wav')
        # set datetime
        d = datetime.now()
        eaf = elan.create(media_file='test.wav',
                          media_url='file:///home/tuananh/Documents/ELAN/test.eaf',
                          relative_media_url='./test.wav',
                          author='Le Tuan Anh')
        # update media info after created
        eaf.media_file = 'new_test.wav'
        eaf.media_url = 'file:///home/tuananh/Documents/ELAN/new_test.eaf'
        eaf.relative_media_url = './new_test.wav'
        # test update created time
        eaf.date = d
        eaf2 = elan.parse_string(eaf.to_xml_str())  # save simulation
        # make sure that customized information is saved
        self.assertEqual(eaf2.date, d.astimezone().isoformat())
        self.assertEqual(eaf2.author, "Le Tuan Anh")
        self.assertEqual(eaf2.media_file, 'new_test.wav')
        self.assertEqual(eaf2.media_url, 'file:///home/tuananh/Documents/ELAN/new_test.eaf')
        self.assertEqual(eaf2.relative_media_url, './new_test.wav')


class TestControlledVocab(unittest.TestCase):

    def test_reading_ecv(self):
        ecv = elan.read_ecv(TEST_ECV2)
        self.assertEqual(ecv.author, "Le Tuan Anh")
        self.assertEqual(ecv.date, "2021-10-29T11:39:43+08:00")
        self.assertEqual(ecv.version, "0.2")
        self.assertEqual(ecv.schema_location, "http://www.mpi.nl/tools/elan/EAFv2.8.xsd")
        # test parsing languages
        actual = set()
        for lang in ecv.languages:
            actual.add((lang.label, lang.lang_def))
        expected = {
            ('English (eng)', 'http://cdb.iso.org/lg/CDB-00138502-001'),
            ('Japanese (jpn)', 'http://cdb.iso.org/lg/CDB-00138539-001')
        }
        self.assertEqual(actual, expected)
        # test parsing controlled vocabs
        actual = dict()
        for cv in ecv.vocabs:
            key = f"{cv.ID}/{cv.description}"
            actual[key] = []
            for entry in cv:
                actual[key].append((entry.lang_ref, entry.ID, entry.value, entry.description))
        expected = {
            'Prompt_Words/Word list to prompt speech from infants': [
                ('eng',
                 'cveid_8852638b-ce28-47ea-ba2c-6f450d9e16be',
                 'mama',
                 'Mother'),
                ('eng',
                 'cveid_1469b811-ec54-4a6e-9ae0-57c8d935d42e',
                 'papa',
                 'Father'),
                ('eng',
                 'cveid_2b218228-bf70-45c2-a902-f02e1da66509',
                 'apple',
                 'The common fruit')],
            '喃語/喃語（なんご）とは、乳児が発する意味のない声。言語を獲得する前段階で、声帯の使い方や発声される音を学習している。': [
                ('jpn',
                 'cveid_5be8575f-7f1f-4c16-88e6-b0f177d63b2c',
                 'あっあっ',
                 ''),
                ('jpn',
                 'cveid_5a10927a-8a51-4a4e-8aec-8e1db774f3a3',
                 'えっえっ',
                 ''),
                ('jpn',
                 'cveid_7f88f97b-fa7a-4faf-a7d6-383140073b23',
                 'あうー',
                 ''),
                ('jpn',
                 'cveid_57ee66f2-5a08-4d78-8191-3fca86871b07',
                 'おぉー',
                 '')]}
        self.assertEqual(expected, actual)

    def test_editing_ecv(self):
        eaf = read_eaf()
        expected = [('cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc7', 'vi', 'Vietnamese'),
                    ('cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc8', 'ko', 'Korean'),
                    ('cveid_2fef57d6-45fc-4763-95d8-2dca63b043d7', 'jp', 'Japanese')]
        # remove en
        eaf.vocabs[0].remove(eaf.vocabs[0].by_id('cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc5'))
        jp = eaf.vocabs[0].by_id('cveid_2fef57d6-45fc-4763-95d8-2dca63b043d7')
        # add vi
        vi = eaf.vocabs[0].new_entry('cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc7', 'vi', 'Vietnamese', next_entry=jp)
        # add ko
        eaf.vocabs[0].new_entry('cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc8', 'ko', 'Korean', prev_entry=vi)
        actual = []
        for e in eaf.vocabs[0]:
            actual.append((e.ID, e.value, e.description))
            e.value = e.value.upper()
            e.description = e.description + " Language"
        self.assertEqual(expected, actual)
        eaf2 = elan.parse_string(eaf.to_xml_str())
        expected2 = [('cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc7', 'VI', 'Vietnamese Language'),
                     ('cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc8', 'KO', 'Korean Language'),
                     ('cveid_2fef57d6-45fc-4763-95d8-2dca63b043d7', 'JP', 'Japanese Language')]
        actual2 = []
        for e in eaf2.vocabs[0]:
            actual2.append((e.ID, e.value, e.description))
        self.assertEqual(expected2, actual2)

    def test_ecv_new_annotation(self):
        # internal vocabs
        eaf = read_eaf()
        icv = eaf.get_vocab('Languages')
        self.assertEqual(icv.ID, 'Languages')
        en_id = 'cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc5'
        self.assertEqual(icv.by_id(en_id).value, 'en')
        self.assertEqual(icv['en'].ID, en_id)
        # make sure that controlled vocab has been linked properly
        t = eaf['Person1 (Language)']
        self.assertEqual(t.vocab.ID, 'Languages')
        # external vocabs
        ecv = elan.read_ecv(TEST_ECV2)
        self.assertEqual(ecv.by_id('Prompt_Words').ID, 'Prompt_Words')


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

    def test_create_new_elan_file(self):
        eaf = elan.create()
        # test add new vocab
        vc = eaf.new_vocab('Fruits', 'jpn')
        vc.new_entry(None, 'ringo', 'apple')
        vc.new_entry(None, 'ichigo', 'strawberry')
        # test adding new tier type
        eaf.new_linguistic_type('default-lt2')
        eaf.new_linguistic_type('default-ts', 'Time_Subdivision', vc.ID)
        eaf.new_linguistic_type('default-ss', 'Symbolic_Subdivision')
        eaf.new_linguistic_type('default-sa', 'Symbolic_Association')
        eaf.new_linguistic_type('default-ii', 'Included_In')
        # add new tiers
        eaf.new_tier('tier-lt2', 'default-lt2')
        eaf.new_tier('tier-ts', 'default-ts', 'tier-lt2')
        eaf.new_tier('tier-ss', 'default-ss', 'tier-lt2')
        eaf.new_tier('tier-sa', 'default-sa', 'tier-lt2')
        eaf.new_tier('tier-ii', 'default-ii', 'tier-lt2')
        # save eaf
        eaf = elan.parse_string(eaf.to_xml_str())
        # all stereotypes
        constraints = {c.stereotype for c in eaf.constraints}
        expected = {'Time_Subdivision', 'Symbolic_Subdivision', 'Symbolic_Association', 'Included_In'}
        self.assertEqual(constraints, expected)
        # validate linguistic types
        types = [(t.ID, t.constraints, t.vocab.ID if t.vocab else None) for t in eaf.linguistic_types]
        expected = [('default-lt', None, None), ('default-lt2', None, None),
                    ('default-ts', 'Time_Subdivision', 'Fruits'),
                    ('default-ss', 'Symbolic_Subdivision', None),
                    ('default-sa', 'Symbolic_Association', None),
                    ('default-ii', 'Included_In', None)]
        self.assertEqual(types, expected)
        # validate tiers
        tiers = [(t.ID, t.type_ref.ID, t.parent.ID if t.parent is not None else None) for t in eaf]
        expected = [('default', 'default-lt', None),
                    ('tier-lt2', 'default-lt2', None),
                    ('tier-ts', 'default-ts', 'tier-lt2'),
                    ('tier-ss', 'default-ss', 'tier-lt2'),
                    ('tier-sa', 'default-sa', 'tier-lt2'),
                    ('tier-ii', 'default-ii', 'tier-lt2')]
        self.assertEqual(tiers, expected)
        # validate controlled vocab
        entries = [(e.value, e.description, e.lang_ref) for e in eaf.get_linguistic_type('default-ts').vocab]
        expected = [('ringo', 'apple', 'jpn'), ('ichigo', 'strawberry', 'jpn')]
        self.assertEqual(entries, expected)

    def test_add_annotation(self):
        eaf = elan.create('test.wav')
        eaf.new_linguistic_type('Utterance')
        eaf.new_linguistic_type('Words', 'Time_Subdivision')
        eaf.new_linguistic_type('Tokens', 'Symbolic_Subdivision')
        eaf.new_linguistic_type('Translate', 'Symbolic_Association')
        eaf.new_linguistic_type('Phoneme', 'Included_In')
        eaf.new_tier('Baby (Utterance)', 'Utterance')
        tw = eaf.new_tier('Baby (Words)', 'Words', 'Baby (Utterance)')
        te = eaf.new_tier('Baby (Translate)', 'Translate', 'Baby (Utterance)')
        tp = eaf.new_tier('Baby (Phoneme)', 'Phoneme', 'Baby (Utterance)')
        tt = eaf.new_tier('Baby (Tokens)', 'Tokens', 'Baby (Utterance)')
        tu = eaf['Baby (Utterance)']
        a = tu.new_annotation('ano ringo tabetai',
                              elan.ts2msec("00:00:01.123"),
                              elan.ts2msec("00:00:02.456"))
        tw.new_annotation('ano', values=['ringo', 'tabetai'],
                          timeslots=[1500, 2000],
                          ann_ref_id=a.ID)
        te.new_annotation('(I) want to eat that apple', ann_ref_id=a.ID)
        tp.new_annotation('t', 2100, 2200, ann_ref_id=a.ID)
        tt.new_annotation('ano', values=['ringo', 'tabetai'], ann_ref_id=a.ID)
        self.assertRaises(ValueError, lambda: tp.new_annotation('t', 1600, 2700, ann_ref_id=a.ID))
        # save changes
        eaf = elan.parse_string(eaf.to_xml_str())
        actual = [(t.ID, [(a.ID, a.value, a.from_ts.sec, a.to_ts.sec, a.ref.ID if a.ref else None) for a in t]) for t in eaf]
        expected = [('default', []),
                    ('Baby (Utterance)', [('a1', 'ano ringo tabetai', 1.123, 2.456, None)]),
                    ('Baby (Words)',
                     [('a2', 'ano', 1.123, 1.5, None),
                      ('a3', 'ringo', 1.5, 2.0, None),
                      ('a4', 'tabetai', 2.0, 2.456, None)]),
                    ('Baby (Translate)',
                     [('a5', '(I) want to eat that apple', 1.123, 2.456, 'a1')]),
                    ('Baby (Phoneme)', [('a6', 't', 2.1, 2.2, None)]),
                    ('Baby (Tokens)',
                     [('a7', 'ano', 1.123, 2.456, 'a1'),
                      ('a8', 'ringo', 1.123, 2.456, 'a1'),
                      ('a9', 'tabetai', 1.123, 2.456, 'a1')])]
        self.assertEqual(expected, actual)

    def test_cv_check_add_annotation_ref(self):
        en_id = 'cveid_20c62fa0-8144-44cb-b0d1-ebe9bec51cc5'
        eaf = read_eaf()
        tu = eaf['Person1 (Utterance)']
        tl = eaf['Person1 (Language)']
        u = tu.new_annotation('test', 1000, 2000)
        self.assertRaises(ValueError, lambda: tl.new_annotation('test', ann_ref_id=u.ID))
        tl.new_annotation('en', ann_ref_id=u.ID)
        eaf = elan.parse_string(eaf.to_xml_str())
        tl = eaf['Person1 (Language)']
        self.assertEqual(tl[-1].cve_ref, en_id)
        self.assertEqual(tl[-1].ref.value, 'test')


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
