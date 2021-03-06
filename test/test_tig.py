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

        rubytext = ttlig.parse_furigana('{???/???}??????')
        self.assertEqual(str(rubytext), '?????????')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>???</rb><rt>???</rt></ruby>??????')

        rubytext = ttlig.parse_furigana('{???/??????}{???/??????}???')
        self.assertEqual(str(rubytext), '?????????')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>???</rb><rt>??????</rt></ruby><ruby><rb>???</rb><rt>??????</rt></ruby>???')

        rubytext = ttlig.parse_furigana('{??????/?????????}')
        self.assertEqual(str(rubytext), '??????')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>??????</rb><rt>?????????</rt></ruby>')

        rubytext = ttlig.parse_furigana('???{???/??????}{???/???}')
        self.assertEqual(str(rubytext), '?????????')
        self.assertEqual(rubytext.to_html(), '???<ruby><rb>???</rb><rt>??????</rt></ruby><ruby><rb>???</rb><rt>???</rt></ruby>')
        # weird cases
        rubytext = ttlig.parse_furigana('{{??????/?????????}}')
        self.assertEqual(str(rubytext), '{??????}')
        self.assertEqual(rubytext.to_html(), '{<ruby><rb>??????</rb><rt>?????????</rt></ruby>}')
        # %
        rubytext = ttlig.parse_furigana('{???/???????????????}')
        self.assertEqual(str(rubytext), '???')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>???</rb><rt>???????????????</rt></ruby>')

        rubytext = ttlig.parse_furigana('???{???/??????{???/???}')
        self.assertEqual(str(rubytext), '???{???/?????????')  # first one won't be matched
        self.assertEqual(rubytext.to_html(), '???{???/??????<ruby><rb>???</rb><rt>???</rt></ruby>')

    def test_TTL_tokenizer(self):
        parser = TTLTokensParser()
        tokens = parser.parse_ruby('{???/??????} ??? {???/???}??? ?????? ???')
        token_text = [t.text() for t in tokens]
        self.assertEqual(token_text, ['???', '???', '??????', '??????', '???'])
        actual = parser.delimiter.join(r.to_html() for r in tokens)
        expected = '<ruby><rb>???</rb><rt>??????</rt></ruby> ??? <ruby><rb>???</rb><rt>???</rt></ruby>??? ?????? ???'
        self.assertEqual(expected, actual)
        # test parse_ruby
        actual = ttlig.make_ruby_html('????????? ??? {???/???}?????? ???')
        expected = '????????? ??? <ruby><rb>???</rb><rt>???</rt></ruby>?????? ???'
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
        s1_json = {'text': '?????????????????????', 'transliteration': 'neko ga suki desu .', 'transcription': '', 'morphtrans': '', 'morphgloss': 'cat SUBM likeable COP .', 'wordgloss': '', 'translation': 'I like cats.', 'ident': '01a_01', 'tokens': '{???/??????} ??? {???/???}??? ?????? ???'}
        s2_json = {'text': '???????????????', 'transliteration': '', 'transcription': '', 'morphtrans': '', 'morphgloss': '', 'wordgloss': '', 'translation': 'It rains.', 'ident': '01a_02', 'tokens': '{???/??????} ??? {???/???}??? ???'}
        self.assertEqual(s1.to_dict(), s1_json)
        self.assertEqual(s2.to_dict(), s2_json)
        # test furigana
        s1_furi = '<ruby><rb>???</rb><rt>??????</rt></ruby> ??? <ruby><rb>???</rb><rt>???</rt></ruby>??? ?????? ???'
        s2_furi = '<ruby><rb>???</rb><rt>??????</rt></ruby> ??? <ruby><rb>???</rb><rt>???</rt></ruby>??? ???'
        self.assertEqual(ttlig.make_ruby_html(s1.tokens), s1_furi)
        self.assertEqual(ttlig.make_ruby_html(s2.tokens), s2_furi)

    def test_ttlig_auto(self):
        inpath = JP_IMPLICIT
        sents = ttlig.read(inpath)
        s = sents[0]
        self.assertEqual(s.text, '?????????????????????')
        self.assertEqual(s.tokens, '{???/??????} ??? {???/???}??? ?????? ???')
        self.assertEqual(s.morphgloss, 'cat SUBM likeable COP .')
        self.assertEqual(s.translation, 'I like cats.')

    def test_ttlig_manual(self):
        inpath = JP_MANUAL
        s1, s2 = ttlig.read(inpath)
        s1_dict = {'text': '?????????????????????', 'transliteration': 'neko ga suki desu .', 'transcription': '', 'morphtrans': '', 'morphgloss': 'cat SUBM likeable COP .', 'wordgloss': '', 'translation': 'I like cats.', 'ident': '01a_01', 'tokens': '{???/??????} ??? {???/???}??? ?????? ???'}
        s2_dict = {'text': '???????????????', 'transliteration': '', 'transcription': '', 'morphtrans': '', 'morphgloss': '', 'wordgloss': '', 'translation': 'It rains.', 'ident': '01a_02', 'tokens': '{???/??????} ??? {???/???}??? ???'}
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
        s = deko.parse('??????')
        # f = ttlig.mctoken_to_furi(s[0])
        f = ttlig.RubyToken.from_furi(s[0].text, s[0].reading_hira)
        self.assertEqual(f.to_code(), '{??????/????????????}')
        # half-width char
        s = deko.parse('0')
        f = ttlig.RubyToken.from_furi(s[0].text, s[0].reading_hira)
        self.assertEqual(f.to_code(), '0')

    @unittest.skipIf(not _CAN_PARSE_JP, "Deko is not available, test_tig_parsing is skipped.")
    def test_tig_parsing(self):
        igrow = ttlig.text_to_igrow('???????????????????????????')
        self.assertEqual(igrow.text, '???????????????????????????')
        self.assertEqual(igrow.tokens, '{??????/????????????} ??? {???/??????}???{???/???}??? ??? ???')
        expected = '<ruby><rb>??????</rb><rt>????????????</rt></ruby> ??? <ruby><rb>???</rb><rt>??????</rt></ruby>???<ruby><rb>???</rb><rt>???</rt></ruby>??? ??? ???'
        actual = ttlig.make_ruby_html(igrow.tokens)
        self.assertEqual(expected, actual)
        # test
        igrow = ttlig.text_to_igrow('???????????????')
        self.assertEqual(igrow.text, '???????????????')
        self.assertEqual(igrow.tokens, '{???/???}???{???/???}??????')
        # test more
        igrow = ttlig.text_to_igrow('???????????????')
        self.assertEqual(igrow.text, '???????????????')
        self.assertEqual(igrow.tokens, '{???/???}??? ?????????')
        # half-width char
        igrow = ttlig.text_to_igrow('0?????????')
        self.assertEqual(igrow.text, '0?????????')
        self.assertEqual(igrow.tokens, '0 {???/???} ??? ???')
        # test export to ttl
        ttl_sent = igrow.to_ttl()
        actual = ttl_sent.to_dict()
        expected = {'tags': [{'type': 'pos', 'value': '??????-??? ??????-??????-????????? ????????? ??????-??????'}],
                    'text': '0?????????',
                    'tokens': [{'cfrom': 0, 'cto': 1, 'pos': '??????-???', 'text': '0'},
                               {'cfrom': 1,
                                'cto': 2,
                                'pos': '??????-??????-?????????',
                                'tags': [{'type': 'furi', 'value': '{???/???}'}],
                                'text': '???'},
                               {'cfrom': 2, 'cto': 3, 'pos': '?????????', 'text': '???'},
                               {'cfrom': 3, 'cto': 4, 'pos': '??????-??????', 'text': '???'}]}
        self.assertEqual(expected, actual)

    def test_parsing_aligned_text(self):
        print("Testing TTLIG with multiple spaces")


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
