# -*- coding: utf-8 -*-

'''
Support SQLite storage format
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


import logging

from chirptext import DataObject
from chirptext import ttl
from puchikarui import Schema, with_ctx
from .data import INIT_TTL_SQLITE


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

class Meta(DataObject):
    def __init__(self, key='', value='', **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.value = value

    def __repr__(self):
        data = ("{}={}".format(k, v) for k, v in self.to_dict().items())
        return "Meta({})".format(", ".join(data))

    def __str__(self):
        return str(self.to_dict())


class DocMeta(DataObject):
    def __repr__(self):
        data = ("{}={}".format(k, v) for k, v in self.to_dict().items())
        return "DocMeta({})".format(", ".join(data))

    def __str__(self):
        return str(self.to_dict())


class CorpusMeta(DataObject):
    def __repr__(self):
        data = ("{}={}".format(k, v) for k, v in self.to_dict().items())
        return "CorpusMeta({})".format(", ".join(data))

    def __str__(self):
        return str(self.to_dict())


class Corpus(DataObject):
    pass


class CWLink(DataObject):
    pass


class TTLSQLite(Schema):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_file(INIT_TTL_SQLITE)
        # add tables
        self.add_table('meta', ['key', 'value'], proto=Meta).set_id('key')
        self.add_table('meta_doc', ['name', 'key', 'value'], proto=DocMeta)
        self.add_table('meta_cor', ['name', 'key', 'value'], proto=CorpusMeta)
        self.add_table('corpus', ['ID', 'name', 'title'], proto=Corpus).set_id('ID')
        self.add_table('document', ['ID', 'name', 'title', 'lang', 'corpusID'],
                       proto=ttl.Document, alias='doc').set_id('ID')
        self.add_table('sentence', ['ID', 'ident', 'text', 'docID', 'flag', 'comment'],
                       proto=ttl.Sentence, alias='sent').set_id('ID')
        self.add_table('token', ['ID', 'sid', 'widx', 'text', 'lemma', 'pos', 'cfrom', 'cto', 'comment'],
                       proto=ttl.Token).set_id('ID')
        self.add_table('concept', ['ID', 'sid', 'cidx', 'clemma', 'tag', 'flag', 'comment'],
                       proto=ttl.Concept).set_id('ID')
        self.add_table('tag', ['ID', 'sid', 'wid', 'cfrom', 'cto', 'value', 'source', 'type'], id_cols="ID")
        self.add_table('cwl', ['sid', 'cid', 'wid'], proto=CWLink)

    @with_ctx
    def new_corpus(self, name, title='', ctx=None):
        corpus = Corpus(name=name, title=title)
        newid = ctx.corpus.save(corpus)
        corpus.ID = newid
        return corpus

    @with_ctx
    def new_doc(self, name, corpusID, title='', lang='', ctx=None, **kwargs):
        doc = ttl.Document(name=name, corpusID=corpusID, title=title, lang=lang, **kwargs)
        newid = ctx.doc.save(doc)
        doc.ID = newid
        return doc

    @with_ctx
    def ensure_corpus(self, name, ctx=None, **kwargs):
        corpus = ctx.corpus.select_single('name=?', (name,))
        if corpus is None:
            corpus = self.new_corpus(name, ctx=ctx, **kwargs)
        return corpus

    @with_ctx
    def ensure_doc(self, name, corpus, ctx=None, **kwargs):
        doc = ctx.doc.select_single('name = ?', (name,))
        if doc is None:
            doc = self.new_doc(name=name, corpusID=corpus.ID, ctx=ctx, **kwargs)
        return doc

    def simplify_tag(self, a_tag):
        if a_tag.cfrom == -1:
            a_tag.cfrom = None
        if a_tag.cto == -1:
            a_tag.cto = None
        if not a_tag.source:
            a_tag.source = None
        return a_tag

    @with_ctx
    def save_sent(self, sent_obj, ctx=None):
        # insert sentence
        # save sent obj first
        sent_obj.ID = ctx.sent.save(sent_obj)
        # save sentence's tags
        for tag in sent_obj.tags:
            tag.sid = sent_obj.ID
            tag.wid = None  # ensure that wid is not saved
            self.simplify_tag(tag)
            tag.ID = ctx.tag.save(tag)
        # save tokens
        for idx, token in enumerate(sent_obj):
            token.sid = sent_obj.ID
            token.widx = idx
            token.ID = ctx.token.save(token)
            # save token's tags
            for tag in token:
                tag.sid = sent_obj.ID
                tag.wid = token.ID
                self.simplify_tag(tag)
                tag.ID = ctx.tag.save(tag)
        # save concepts
        for idx, concept in enumerate(sent_obj.concepts):
            concept.sid = sent_obj.ID
            concept.ID = ctx.concept.save(concept)
            # save cwl
            for token in concept.tokens:
                cwl = CWLink(sid=sent_obj.ID, cid=concept.ID, wid=token.ID)
                ctx.cwl.save(cwl)
        return sent_obj

    @with_ctx
    def get_sent(self, sentID, ctx=None):
        sent = ctx.sent.by_id(sentID)
        # select tokens
        tokens = ctx.token.select('sid = ?', (sent.ID,))
        tokenmap = {t.ID: t for t in tokens}
        for tk in tokens:
            sent.tokens.append(tk)
        # select all tags
        tags = ctx.execute('SELECT * FROM TAG where sid = ?', (sent.ID,))
        for tag in tags:
            # TODO: Don't use _append internal
            if tag['wid'] is None:
                sent.tags.new(**tag)
            elif tag['wid'] in tokenmap:
                tokenmap[tag['wid']].tags.new(**tag)
            else:
                getLogger().warning("Orphan tag in sentence #{}: {}".format(sent.ID, tag))
        # select concepts
        concepts = ctx.concept.select('sid = ?', (sent.ID,))
        conceptmap = {c.ID: c for c in concepts}
        for c in concepts:
            sent.concepts._append(c)
        # select cwl
        cwlinks = ctx.cwl.select('sid = ?', (sent.ID,))
        for cwl in cwlinks:
            conceptmap[cwl.cid].tokens += tokenmap[cwl.wid]
        return sent

    @with_ctx
    def lexicon(self, limit=None, ctx=None):
        query = 'SELECT text, COUNT(*) FROM token GROUP BY text ORDER BY COUNT(*) DESC'
        params = []
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        return ctx.execute(query, params)

    # ---- Meta related functions
    @with_ctx
    def get_meta(self, ctx=None):
        return ctx.meta.select()

    @with_ctx
    def get_meta_by_key(self, key, ctx=None):
        return ctx.meta.by_id(key)

    @with_ctx
    def set_meta(self, key, value, ctx=None):
        query = '''INSERT OR REPLACE INTO meta VALUES (?, ?)'''
        params = (key, value)
        return ctx.execute(query, params)

    @with_ctx
    def get_doc_meta(self, name, ctx=None):
        return ctx.meta_doc.select('name = ?', (name,))

    @with_ctx
    def get_doc_meta_by_key(self, name, key, ctx=None):
        return ctx.meta_doc.select_single('name = ? and key = ?', (name, key))

    @with_ctx
    def set_doc_meta(self, name, key, value, ctx=None):
        query = '''INSERT OR REPLACE INTO meta_doc VALUES (?, ?, ?)'''
        params = (name, key, value)
        return ctx.execute(query, params)

    @with_ctx
    def get_cor_meta(self, name, ctx=None):
        return ctx.meta_cor.select('name = ?', (name,))

    @with_ctx
    def get_cor_meta_by_key(self, name, key, ctx=None):
        return ctx.meta_cor.select_single('name = ? and key = ?', (name, key))

    @with_ctx
    def set_cor_meta(self, name, key, value, ctx=None):
        query = '''INSERT OR REPLACE INTO meta_cor VALUES (?, ?, ?)'''
        params = (name, key, value)
        return ctx.execute(query, params)
