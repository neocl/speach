# -*- coding: utf-8 -*-

"""
TTL Interlinear Gloss (TIG) format support

More information: https://en.wikipedia.org/wiki/Interlinear_gloss
An interlinear text will commonly consist of some or all of the following, usually in this order, from top to bottom:
    The original orthography (typically in italic or bold italic),
    a conventional transliteration into the Latin alphabet,
    a phonetic transcription,
    a morphophonemic transliteration,
    a word-by-word or morpheme-by-morpheme gloss, where morphemes within a word are separated by hyphens or other punctuation,
    a free translation, which may be placed in a separate paragraph or on the facing page if the structures of the languages are too different for it to follow the text line by line.
"""
# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


import re
import logging
from difflib import ndiff
from collections import OrderedDict
import warnings

from chirptext import DataObject, piter
from chirptext import chio
from chirptext import deko
from chirptext import ttl


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

# Source: https://en.wikipedia.org/wiki/Interlinear_gloss
# An interlinear text will commonly consist of some or all of the following, usually in this order, from top to bottom:
#     The original orthography (typically in italic or bold italic),
#     a conventional transliteration into the Latin alphabet,
#     a phonetic transcription,
#     a morphophonemic transliteration,
#     a word-by-word or morpheme-by-morpheme gloss, where morphemes within
#     a word are separated by hyphens or other punctuation,
#     a free translation, which may be placed in a separate paragraph or on the facing page
#     if the structures of the languages are too different for it to follow the text line by line.
class IGRow(DataObject):
    def __init__(self, text='', transliteration='', transcription='', morphtrans='', morphgloss='', wordgloss='', translation='', **kwargs):
        """
        """
        super().__init__()
        self.text = text
        self.transliteration = transliteration
        self.transcription = transcription
        self.morphtrans = morphtrans
        self.morphgloss = morphgloss
        self.wordgloss = wordgloss
        self.translation = translation
        self.update(kwargs)

    def to_ttl(self):
        ttl_sent = ttl.Sentence(text=self.text)
        data = self.to_dict()
        for l in TTLIG.KNOWN_LABELS:
            if l not in ['text', 'orth', 'tokens'] and l in data and data[l]:
                ttl_sent.tags.new(data[l], type=l)
        if self.tokens:
            _tokens = parse_ruby(self.tokens)
            ttl_sent.tokens = (t.text() for t in _tokens)
            for ttl_token, furi_token in zip(ttl_sent, _tokens):
                if furi_token.surface != furi_token.text():
                    ttl_token.tags.new(furi_token.surface, type='furi')
            if self.morphtrans:
                _morphtokens = tokenize(self.morphtrans)
                if len(_morphtokens) != len(ttl_sent):
                    logging.getLogger(__name__).warning("Morphophonemic transliteration line and tokens line are mismatched for sentence: {}".format(self.ident or self.ID or self.Id or self.id or self.text))
                else:
                    for t, m in zip(ttl_sent, _morphtokens):
                        t.tags.new(m, type='mtrans')
            if self.pos:
                _postokens = tokenize(self.pos)
                if len(_postokens) != len(ttl_sent):
                    logging.getLogger(__name__).warning("Part-of-speech line and tokens line are mismatched for sentence: {}".format(self.ident or self.ID or self.Id or self.id or self.text))
                else:
                    for t, m in zip(ttl_sent, _postokens):
                        t.pos = m
            if self.lemma:
                _lemmas = tokenize(self.lemma)
                if len(_lemmas) != len(ttl_sent):
                    logging.getLogger(__name__).warning("Lemma line and tokens line are mismatched for sentence: {}".format(self.ident or self.ID or self.Id or self.id or self.text))
                else:
                    for t, m in zip(ttl_sent, _lemmas):
                        t.lemma = m
            if self.morphgloss:
                _glosstokens = tokenize(self.morphgloss)
                if len(_glosstokens) != len(ttl_sent):
                    logging.getLogger(__name__).warning("morpheme-by-morpheme gloss and tokens lines are mismatched for sentence {}".format(self.ident or self.ID or self.Id or self.id or self.text))
                else:
                    for t, m in zip(ttl_sent, _glosstokens):
                        t.tags.new(m, type='mgloss')
            if self.wordgloss:
                _glosstokens = tokenize(self.wordgloss)
                if len(_glosstokens) != len(ttl_sent):
                    logging.getLogger(__name__).warning("word-by-word gloss and tokens lines are mismatched for sentence {}".format(self.ident or self.ID or self.Id or self.id or self.text))
                else:
                    for t, m in zip(ttl_sent, _glosstokens):
                        t.tags.new(m, type='wgloss')
        return ttl_sent

    def to_expex(self, default_ident=''):
        lines = []
        sent_ident = self.ident if self.ident else default_ident
        lines.append('\\ex \\label{{{}}}'.format(sent_ident))
        lines.append('\\begingl[aboveglftskip=0pt]')
        tags = ['gla', 'glb', 'glc']
        # process tokens and gloss
        glosses = []
        lengths = []
        if self.tokens:
            lengths.append(make_expex_gloss(self.tokens, glosses, tags.pop(0)))
        if self.morphtrans:
            lengths.append(make_expex_gloss(self.morphtrans, glosses, tags.pop(0)))
        if self.morphgloss:
            lengths.append(make_expex_gloss(self.morphgloss, glosses, tags.pop(0)))
        if self.concept:
            if tags:
                lengths.append(make_expex_gloss(self.concept, glosses, tags.pop(0)))
            else:
                logging.getLogger(__name__).warning("There are too many gloss lines in sentence {}. {}".format(sent_ident, self.text))
        # ensure that number of tokens are the same
        if len(lengths) > 1:
            for line_len in lengths[1:]:
                if line_len != lengths[0]:
                    logging.getLogger(__name__).warning("Inconsistent tokens and morphgloss for sentence {}. {} ({} v.s {})".format(sent_ident, self.text, line_len, lengths[0]))
                    break
        lines.extend(glosses)
        lines.append('\\glft \lit{{{}}}//'.format(escape_latex(self.text)))
        lines.append('\\endgl')
        lines.append('\\xe')
        return '\n'.join(lines)

    # Matrix alias
    @property
    def orth(self):
        return self.text

    @orth.setter
    def orth(self, value):
        self.text = value

    @property
    def translit(self):
        return self.transliteration

    @translit.setter
    def translit(self, value):
        self.transliteration = value

    @property
    def translat(self):
        return self.translation

    @translat.setter
    def translat(self, value):
        self.translation = value

    @property
    def gloss(self):
        return self.morphgloss

    @gloss.setter
    def gloss(self, value):
        self.morphgloss = value

    @property
    def tsduration(self):
        if self.tsfrom is None or self.tsto is None:
            return None
        else:
            return self.tsto - self.tsfrom

    def overlap(self, other):
        ''' Calculate overlap score between this utterance and another
        Score = 0 means adjacent, score > 0 means overlapped, score < 0 means no overlap (the distance between the two)
        '''
        return min(self.tsto, other.tsto) - max(self.tsfrom, other.tsfrom)



LATEX_SPECIAL_CHARS = P = re.compile('([%${_#&}])')


def escape_latex(text):
    text = LATEX_SPECIAL_CHARS.sub(r"\\\g<1>", text.replace('\\', '\\textbackslash '))
    text = text.replace('<', '\\textless ').replace('>', '\\textgreater ')
    return text if text.strip() else '{}'


def make_expex_gloss(raw, lines, gloss_tag):
    _tokens = tokenize(raw)
    lines.append('\\{} {} //'.format(gloss_tag, ' '.join((escape_latex(t) for t in _tokens))))
    return len(_tokens)


class TTLIG(object):

    # default lines
    AUTO_LINES = ['tokens', 'morphtrans', 'gloss']
    MANUAL_TAG = '__manual__'
    AUTO_TAG = '__auto__'
    ROBUST_TAG = '__robust__'
    SPECIAL_LABELS = [AUTO_TAG, MANUAL_TAG, ROBUST_TAG]
    KNOWN_META = ['language', 'language code', 'lines', 'author', 'date']
    ANNOTATIONS = ['flag', 'font', 'font-global']
    SPECIAL_FEATURES = ['furigana', 'furi']
    CORPUS_MANAGEMENT = ['comment', 'source', 'vetted', 'judgement', 'phenomena', 'url', 'type']
    SYNTAX = ['tree', 'dtree']
    SEMANTICS = ['concept', 'mrs', 'dmrs', 'predicates', 'preds']
    DISCOURSE = ['tsfrom', 'tsto', 'speaker']
    INTERLINEAR_GLOSS = ['ident', 'orth', 'morphgloss', 'wordgloss', 'translation', 'text', 'translit', 'translat', 'tokens', 'lemma', 'pos']
    KNOWN_LABELS = AUTO_LINES + KNOWN_META + ANNOTATIONS + SPECIAL_FEATURES + CORPUS_MANAGEMENT + SYNTAX + SEMANTICS + INTERLINEAR_GLOSS + DISCOURSE
    # [TODO] Add examples & description for each of these labels

    def __init__(self, meta):
        self.meta = meta

    def row_format(self):
        if 'Lines' in self.meta:
            lines = self.meta['Lines'].strip()
            if lines:
                return self.meta['Lines'].strip().split()
        return []

    def _parse_row(self, line_list, line_tags):
        if not line_list:
            raise ValueError("Lines cannot be empty")
        if not line_tags or line_tags == [TTLIG.AUTO_TAG]:
            # auto
            # first line = text, last line = translation, transli
            if len(line_list) == 1:
                return IGRow(text=line_list[0])
            elif len(line_list) == 2:
                return IGRow(text=line_list[0], translation=line_list[-1])
            else:
                others = {k: v for k, v in zip(TTLIG.AUTO_LINES, line_list[1:-1])}
                return IGRow(text=line_list[0], translation=line_list[-1], **others)
        elif line_tags == [TTLIG.MANUAL_TAG]:
            line_dict = {}
            for line in line_list:
                tag_idx = line.find(':')
                if tag_idx == -1:
                    raise ValueError("Invalid line (no tag found) -> {}".format(line))
                _tag = line[:tag_idx].strip()
                _val = line[tag_idx + 1:].lstrip().rstrip('\r\n')
                if _tag.lower() not in TTLIG.KNOWN_LABELS:
                    logging.getLogger(__name__).warning("Unknown tag was used ({}): {}".format(_tag, _val))
                line_dict[_tag] = _val
            return IGRow(**line_dict)
        else:
            # explicit, just zip them
            if len(line_tags) != len(line_list):
                raise ValueError("Mismatch number of lines for {} - {}".format(line_tags, line_list))
            return IGRow(**{k: v for k, v in zip(line_tags, line_list)})

    def read_iter(self, stream):
        line_tags = self.row_format()
        for tag in line_tags:
            if tag.lower() not in TTLIG.KNOWN_LABELS + TTLIG.SPECIAL_LABELS:
                logging.getLogger(__name__).warning("Unknown label in header: {}".format(tag))
        for row in IGStreamReader._iter_stream(stream):
            yield self._parse_row(row, line_tags)


class IGStreamReader(object):

    META_LINE = re.compile(r'(?P<key>[\w\s]+):\s*(?P<value>.*)')

    @staticmethod
    def _read_header(ig_stream):
        ''' Read the TTLIG header from a stream '''
        lines = piter(ig_stream)
        first = next(lines)
        if first.strip() != '# TTLIG':
            raise Exception("Invalid TTLIG header. TTLIG files must start with # TTLIG")
        meta = OrderedDict()
        for line in lines:
            if line.startswith("#"):
                continue
            m = IGStreamReader.META_LINE.match(line)
            if m:
                key = m.group('key').strip()
                value = m.group('value')
                if key in meta:
                    logging.getLogger(__name__).warning("Key {} is duplicated in the header".format(key))
                meta[key] = value
            else:
                # this line is weird
                break
            if not lines.peep() or not lines.peep().value.strip():
                # if next line is empty, break
                break
        return meta

    @staticmethod
    def _iter_stream(ig_stream):
        lines = piter(ig_stream)
        current = []
        for line_raw in lines:
            line = line_raw.rstrip('\r\n')
            if not line.startswith('#') and line:
                # not a comment or an empty line
                current.append(line)
            if not line or not lines.peep() or not lines.peep().value:
                if current:
                    yield current
                    current = []


def read_stream_iter(ttlig_stream):
    meta = IGStreamReader._read_header(ttlig_stream)
    ig_obj = TTLIG(meta)
    return ig_obj.read_iter(ttlig_stream)


def read_stream(ttlig_stream):
    ''' read TTLIG stream '''
    return [s for s in read_stream_iter(ttlig_stream)]


def read(ttlig_filepath):
    ''' Read TTLIG file '''
    with chio.open(ttlig_filepath, mode='rt') as infile:
        return read_stream(infile)


FURIMAP = re.compile(r'\{(?P<text>[\w%％]+?)/(?P<furi>[\w%％]+?)\}')


class RubyToken(DataObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'groups' not in kwargs:
            self.groups = []

    def append(self, group):
        self.groups.append(group)

    def text(self):
        return ''.join(str(x) for x in self.groups)

    def to_html(self):
        frags = []
        for g in self.groups:
            if isinstance(g, RubyFrag):
                frags.append(g.to_html())
            else:
                frags.append(str(g))
        return ''.join(frags)

    def to_code(self):
        frags = []
        for g in self.groups:
            if isinstance(g, RubyFrag):
                frags.append('{{{text}/{furi}}}'.format(text=g.text, furi=g.furi))
            else:
                frags.append(str(g))
        return ''.join(frags)

    def to_anki(self):
        ''' Export token to Anki fugigana format '''
        frags = []
        for g in self.groups:
            if isinstance(g, RubyFrag):
                frags.append('{text}[{furi}]'.format(text=g.text, furi=g.furi))
            else:
                frags.append(str(g))
        return ''.join(frags)

    def __str__(self):
        return self.text()

    @staticmethod
    def from_furi(surface, kana):
        ruby = RubyToken(surface=surface)
        if deko.is_kana(surface):
            ruby.append(surface)
            return ruby
        edit_seq = ndiff(surface, kana)
        kanji = ''
        text = ''
        furi = ''
        before = ''
        expected = ''
        for item in edit_seq:
            if item.startswith('- '):
                # flush text if needed
                if expected and kanji and furi:
                    ruby.append(RubyFrag(text=kanji, furi=furi))
                    kanji = ''
                    furi = ''
                if text:
                    ruby.append(text)
                    text = ''
                kanji += item[2:]
            elif item.startswith('+ '):
                if expected and item[2:] == expected:
                    if expected and kanji and furi:
                        ruby.append(RubyFrag(text=kanji, furi=furi))
                        kanji = ''
                        furi = ''
                    ruby.append(item[2:])
                    expected = ''
                else:
                    furi += item[2:]
            elif item.startswith('  '):
                if before == '-' and not furi:
                    # shifting happened
                    expected = item[2:]
                    furi += item[2:]
                else:
                    text += item[2:]
                    # flush if possible
                    if kanji and furi:
                        ruby.append(RubyFrag(text=kanji, furi=furi))
                        kanji = ''
                        furi = ''
                    else:
                        # possible error?
                        pass
            before = item[0]  # end for
        # flush final parts
        if kanji:
            if furi:
                ruby.append(RubyFrag(text=kanji, furi=furi))
            else:
                ruby.append(kanji)
        elif text:
            ruby.append(text)
        return ruby


class RubyFrag(DataObject):
    def __init__(self, text, furi, **kwargs):
        super().__init__(text=text, furi=furi, **kwargs)

    def __repr__(self):
        return "Ruby(text={}, furi={})".format(repr(self.text), repr(self.furi))

    def to_html(self):
        return "<ruby><rb>{}</rb><rt>{}</rt></ruby>".format(self.text, self.furi)

    def __str__(self):
        return self.text if self.text else ''


def parse_furigana(text):
    ''' Parse TTLRuby token (returns a RubyToken)'''
    if text is None:
        raise ValueError
    start = 0
    ruby = RubyToken(surface=text)
    ms = [(m.groupdict(), m.span()) for m in FURIMAP.finditer(text)]
    # frag: ruby fragment
    for frag, (cfrom, cto) in ms:
        if start < cfrom:
            ruby.append(text[start:cfrom])
        ruby.append(RubyFrag(text=frag['text'], furi=frag['furi']))
        start = cto
    if start < len(text):
        ruby.append(text[start:len(text)])
    return ruby


class TTLTokensParser(object):
    ''' TTL Tokens parser '''
    def __init__(self, escapechar='\\', delimiter=' '):
        self.escapechar = escapechar
        self.delimiter = delimiter

    def parse(self, text):
        tokens = []
        current = []
        chars = piter(text)
        is_escaping = False
        for c in chars:
            if is_escaping:
                current.append(c)
                is_escaping = False
            elif c == self.escapechar:
                # add the next character to current token
                if not chars.peep():
                    raise ValueError("Escape char ({}) cannot be the last character".format(self.escapechar))
                elif chars.peep() and chars.peep().value not in (self.escapechar, self.delimiter):
                    logging.getLogger(__name__).warning("Escape char ({}) should not be used for normal character ({}). This can be a potential bug in the data.".format(self.escapechar, chars.peep().value))
                is_escaping = True
            elif c == self.delimiter:
                # flush
                if current:
                    tokens.append(''.join(current))
                    current = []
                # else -> ignore
            else:
                current.append(c)
            # flush if current is the last character
            if chars.peep() is None and current:
                tokens.append(''.join(current))
                current = []
        return tokens

    def parse_ruby(self, text):
        ''' Return a list of RubyToken '''
        return [parse_furigana(t) for t in self.parse(text)]


DEFAULT_TTL_TOKEN_PARSER = TTLTokensParser()


def tokenize(text):
    return DEFAULT_TTL_TOKEN_PARSER.parse(text)


def parse_ruby(text):
    return DEFAULT_TTL_TOKEN_PARSER.parse_ruby(text)


def make_ruby_html(text):
    tokens = parse_ruby(text)
    return DEFAULT_TTL_TOKEN_PARSER.delimiter.join(r.to_html() for r in tokens)


def mctoken_to_furi(token):
    ''' Convert mecab token to TTLIG format '''
    warnings.warn("mctoken_to_furi() is deprecated and will be removed in near future. Use RubyToken.from_furi() instead", DeprecationWarning, stacklevel=2)
    return RubyToken.from_furi(token.surface, token.reading_hira())


def ttl_to_igrow(msent):
    ''' Convert TTL to TTLIG format '''
    tokens = []
    pos = []
    lemmas = []
    for token in msent:
        pos.append(token.pos3 if token.pos3 else token.pos)
        if token.reading_hira:
            r = RubyToken.from_furi(token.text, token.reading_hira)
            tokens.append(r.to_code())
        else:
            tokens.append(token.text)
            lemmas.append(token.lemma if token.lemma else '')
    igrow = IGRow(text=msent.text, tokens=' '.join(tokens), pos=' '.join(pos), lemma=' '.join(lemmas))
    return igrow


def text_to_igrow(txt):
    ''' Parse text to TTLIG format '''
    sent = deko.parse(txt)
    return ttl_to_igrow(sent)
