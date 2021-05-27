#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test TTL Interlinear Gloss (TIG)
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import io
import unittest
import logging
from collections import OrderedDict

from chirptext import chio
from chirptext import deko

from speach import ttl
from speach import ttlig
from speach.ttlig import IGStreamReader, TTLTokensParser


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
JP_IMPLICIT = os.path.join(TEST_DIR, 'data', 'testig_jp_implicit.txt')
JP_EXPLICIT = os.path.join(TEST_DIR, 'data', 'testig_jp_explicit.txt')
JP_MANUAL = os.path.join(TEST_DIR, 'data', 'testig_jp_manual.txt')
VN_EXPLICIT = os.path.join(TEST_DIR, 'data', 'testig_vi_explicit.txt')
TRANSCRIPT_FILE = os.path.join(TEST_DIR, 'data', 'test_transcript.tab')
TRANSCRIPT_EXPECTED_FILE = os.path.join(TEST_DIR, 'data', 'test_transcript.human.tab')

_CAN_PARSE_JP = None
try:
    engines = deko.engines()
    _CAN_PARSE_JP = len(engines)
except Exception:
    pass


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

class TestTokenizer(unittest.TestCase):

    def test_tokenizer(self):
        print("test multiple spaces for tokenizing")
        sent = ttl.Sentence('It works.')
        token_string = 'It       works   .    '
        gloss_string = 'SUBJ     work    PUNC '
        tokens = ttlig.tokenize(token_string)
        glosses = ttlig.tokenize(gloss_string)
        sent.tokens = tokens
        for tk, gl in zip(sent.tokens, glosses):
            tk.tag.gloss = gl
        # verify imported information
        actual = [(t.text, t.tag.gloss.value) for t in sent]
        expected = [('It', 'SUBJ'), ('works', 'work'), ('.', 'PUNC')]
        self.assertEqual(expected, actual)

    def test_tokenizing_special_chars(self):
        ''' Only 2 characters - escapechar and delimiter '''
        tokens = ttlig.tokenize('some\\ thing is a word .')
        expected = ['some thing', 'is', 'a', 'word', '.']
        self.assertEqual(tokens, expected)
        # last char is special
        with self.assertLogs("speach", "WARNING") as cm:
            tokens = ttlig.tokenize('some\\ thing is a word \\.')
            expected = ['some thing', 'is', 'a', 'word', '.']
            self.assertEqual(tokens, expected)
            _found_warning = False
            for log in cm.output:
                if "should not be used for normal character" in log:
                    _found_warning = True
                    break
            self.assertTrue(_found_warning)
        # last char is delimiter
        self.assertRaises(Exception, lambda: ttlig.tokenize('this is wrong\\'))


class TestFurigana(unittest.TestCase):

    def test_parse_furigana(self):
        rubytext = ttlig.parse_furigana('')
        self.assertEqual(str(rubytext), '')
        self.assertEqual(rubytext.to_html(), '')

        self.assertRaises(ValueError, lambda: ttlig.parse_furigana(None))

        rubytext = ttlig.parse_furigana('{食/た}べる')
        self.assertEqual(str(rubytext), '食べる')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>食</rb><rt>た</rt></ruby>べる')

        rubytext = ttlig.parse_furigana('{面/おも}{白/しろ}い')
        self.assertEqual(str(rubytext), '面白い')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>面</rb><rt>おも</rt></ruby><ruby><rb>白</rb><rt>しろ</rt></ruby>い')

        rubytext = ttlig.parse_furigana('{漢字/かんじ}')
        self.assertEqual(str(rubytext), '漢字')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>漢字</rb><rt>かんじ</rt></ruby>')

        rubytext = ttlig.parse_furigana('お{天/てん}{気/き}')
        self.assertEqual(str(rubytext), 'お天気')
        self.assertEqual(rubytext.to_html(), 'お<ruby><rb>天</rb><rt>てん</rt></ruby><ruby><rb>気</rb><rt>き</rt></ruby>')
        # weird cases
        rubytext = ttlig.parse_furigana('{{漢字/かんじ}}')
        self.assertEqual(str(rubytext), '{漢字}')
        self.assertEqual(rubytext.to_html(), '{<ruby><rb>漢字</rb><rt>かんじ</rt></ruby>}')
        # %
        rubytext = ttlig.parse_furigana('{％/パーセント}')
        self.assertEqual(str(rubytext), '％')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>％</rb><rt>パーセント</rt></ruby>')

        rubytext = ttlig.parse_furigana('お{天/てん{気/き}')
        self.assertEqual(str(rubytext), 'お{天/てん気')  # first one won't be matched
        self.assertEqual(rubytext.to_html(), 'お{天/てん<ruby><rb>気</rb><rt>き</rt></ruby>')

    def test_TTL_tokenizer(self):
        parser = TTLTokensParser()
        tokens = parser.parse_ruby('{猫/ねこ} が {好/す}き です 。')
        token_text = [t.text() for t in tokens]
        self.assertEqual(token_text, ['猫', 'が', '好き', 'です', '。'])
        actual = parser.delimiter.join(r.to_html() for r in tokens)
        expected = '<ruby><rb>猫</rb><rt>ねこ</rt></ruby> が <ruby><rb>好</rb><rt>す</rt></ruby>き です 。'
        self.assertEqual(expected, actual)
        # test parse_ruby
        actual = ttlig.make_ruby_html('ケーキ を {食/た}べた 。')
        expected = 'ケーキ を <ruby><rb>食</rb><rt>た</rt></ruby>べた 。'
        self.assertEqual(expected, actual)


class TestTTLIG(unittest.TestCase):

    def test_iter_stream(self):
        raw = io.StringIO('''# TTLIG
# This is a comment
I drink green tea.
I drink green_tea.

I have two cats.
I have two cat-s.
''')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = [['I drink green tea.', 'I drink green_tea.'], ['I have two cats.', 'I have two cat-s.']]
        self.assertEqual(groups, expected)

        # nothing
        raw = io.StringIO('''# TTLIG''')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = []
        self.assertEqual(groups, expected)
        raw = io.StringIO('')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = []
        self.assertEqual(groups, expected)
        raw = io.StringIO('a\n\nb')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = [['a'], ['b']]
        self.assertEqual(groups, expected)
        raw = io.StringIO('a\n#comment\nb')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = [['a', 'b']]
        self.assertEqual(groups, expected)

    def test_read_header(self):
        inpath = VN_EXPLICIT
        with chio.open(inpath) as infile:
            meta = ttlig.IGStreamReader._read_header(infile)
        expected = OrderedDict([('Language', 'Vietnamese'), ('Language code', 'vie'), ('Lines', 'orth translit gloss translat'), ('Author', 'Le Tuan Anh'), ('Date', 'May 25 2018')])
        self.assertEqual(meta, expected)

    def test_read_file(self):
        inpath = JP_MANUAL
        s1, s2 = ttlig.read(inpath)
        s1_json = {'text': '猫が好きです。', 'transliteration': 'neko ga suki desu .', 'transcription': '', 'morphtrans': '', 'morphgloss': 'cat SUBM likeable COP .', 'wordgloss': '', 'translation': 'I like cats.', 'ident': '01a_01', 'tokens': '{猫/ねこ} が {好/す}き です 。'}
        s2_json = {'text': '雨が降る。', 'transliteration': '', 'transcription': '', 'morphtrans': '', 'morphgloss': '', 'wordgloss': '', 'translation': 'It rains.', 'ident': '01a_02', 'tokens': '{雨/あめ} が {降/ふ}る 。'}
        self.assertEqual(s1.to_dict(), s1_json)
        self.assertEqual(s2.to_dict(), s2_json)
        # test furigana
        s1_furi = '<ruby><rb>猫</rb><rt>ねこ</rt></ruby> が <ruby><rb>好</rb><rt>す</rt></ruby>き です 。'
        s2_furi = '<ruby><rb>雨</rb><rt>あめ</rt></ruby> が <ruby><rb>降</rb><rt>ふ</rt></ruby>る 。'
        self.assertEqual(ttlig.make_ruby_html(s1.tokens), s1_furi)
        self.assertEqual(ttlig.make_ruby_html(s2.tokens), s2_furi)

    def test_ttlig_auto(self):
        inpath = JP_IMPLICIT
        sents = ttlig.read(inpath)
        s = sents[0]
        self.assertEqual(s.text, '猫が好きです。')
        self.assertEqual(s.tokens, '{猫/ねこ} が {好/す}き です 。')
        self.assertEqual(s.morphgloss, 'cat SUBM likeable COP .')
        self.assertEqual(s.translation, 'I like cats.')

    def test_ttlig_manual(self):
        inpath = JP_MANUAL
        s1, s2 = ttlig.read(inpath)
        s1_dict = {'text': '猫が好きです。', 'transliteration': 'neko ga suki desu .', 'transcription': '', 'morphtrans': '', 'morphgloss': 'cat SUBM likeable COP .', 'wordgloss': '', 'translation': 'I like cats.', 'ident': '01a_01', 'tokens': '{猫/ねこ} が {好/す}き です 。'}
        s2_dict = {'text': '雨が降る。', 'transliteration': '', 'transcription': '', 'morphtrans': '', 'morphgloss': '', 'wordgloss': '', 'translation': 'It rains.', 'ident': '01a_02', 'tokens': '{雨/あめ} が {降/ふ}る 。'}
        self.assertEqual(s1.to_dict(), s1_dict)
        self.assertEqual(s2.to_dict(), s2_dict)

    def test_read_empty_file(self):
        instream = io.StringIO('# TTLIG')
        sents = ttlig.read_stream(instream)
        self.assertEqual(sents, [])

    def test_read_invalid_ttlig(self):
        instream = io.StringIO('')
        self.assertRaises(Exception, lambda: ttlig.read_stream(instream))
        invalid_file = os.path.join(TEST_DIR, 'data', 'testig_invalid.txt')
        self.assertRaises(Exception, lambda: ttlig.read(invalid_file))

    @unittest.skipIf(not _CAN_PARSE_JP, "Deko is not available, test_make_furi_token is skipped.")
    def test_make_furi_token(self):
        s = deko.parse('友達')
        # f = ttlig.mctoken_to_furi(s[0])
        f = ttlig.RubyToken.from_furi(s[0].text, s[0].reading_hira)
        self.assertEqual(f.to_code(), '{友達/ともだち}')
        # half-width char
        s = deko.parse('0')
        f = ttlig.RubyToken.from_furi(s[0].text, s[0].reading_hira)
        self.assertEqual(f.to_code(), '0')

    @unittest.skipIf(not _CAN_PARSE_JP, "Deko is not available, test_tig_parsing is skipped.")
    def test_tig_parsing(self):
        igrow = ttlig.text_to_igrow('友達と巡り会った。')
        self.assertEqual(igrow.text, '友達と巡り会った。')
        self.assertEqual(igrow.tokens, '{友達/ともだち} と {巡/めぐ}り{会/あ}っ た 。')
        expected = '<ruby><rb>友達</rb><rt>ともだち</rt></ruby> と <ruby><rb>巡</rb><rt>めぐ</rt></ruby>り<ruby><rb>会</rb><rt>あ</rt></ruby>っ た 。'
        actual = ttlig.make_ruby_html(igrow.tokens)
        self.assertEqual(expected, actual)
        # test
        igrow = ttlig.text_to_igrow('言い尽くす')
        self.assertEqual(igrow.text, '言い尽くす')
        self.assertEqual(igrow.tokens, '{言/い}い{尽/つ}くす')
        # test more
        igrow = ttlig.text_to_igrow('言いなさい')
        self.assertEqual(igrow.text, '言いなさい')
        self.assertEqual(igrow.tokens, '{言/い}い なさい')
        # half-width char
        igrow = ttlig.text_to_igrow('0時だ。')
        self.assertEqual(igrow.text, '0時だ。')
        self.assertEqual(igrow.tokens, '0 {時/じ} だ 。')
        # test export to ttl
        ttl_sent = igrow.to_ttl()
        expected = {'tags': [{'type': 'pos', 'value': '名詞-数 名詞-接尾-助数詞 助動詞 記号-句点'}],
                    'text': '0時だ。',
                    'tokens': [{'cfrom': 0, 'cto': 1, 'pos': '名詞-数', 'text': '0'},
                               {'cfrom': 1,
                                'cto': 2,
                                'pos': '名詞-接尾-助数詞',
                                'tags': [{'type': 'furi', 'value': '{時/じ}'}],
                                'text': '時'},
                               {'cfrom': 2, 'cto': 3, 'pos': '助動詞', 'text': 'だ'},
                               {'cfrom': 3, 'cto': 4, 'pos': '記号-句点', 'text': '。'}]}
        self.assertEqual(expected, ttl_sent.to_dict())

    def test_parsing_aligned_text(self):
        print("Testing TTLIG with multiple spaces")


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
