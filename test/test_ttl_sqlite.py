#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test basic TTL SQLite
'''

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
from pathlib import Path
import unittest
import logging

from speach import ttl
from speach.sqlite import TTLSQLite


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEST_DATA = TEST_DIR / 'data'


def getLogger():
    return logging.getLogger(__name__)


def get_db(use_ram=True, auto_clear=True):
    if use_ram:
        return TTLSQLite(':memory:')
    else:
        db_loc = os.path.join(TEST_DIR, 'data', 'test.db')
        if auto_clear:
            if os.path.isfile(db_loc):
                os.unlink(db_loc)
        return TTLSQLite(db_loc)


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

class TestTTLSQLite(unittest.TestCase):

    def test_extra_fields(self):
        doc = ttl.Document(corpusID=2)
        self.assertEqual(doc.corpusID, 2)

    def test_write_json(self):
        from chirptext import deko
        doc = deko.parse_doc('三毛猫が好きです。雨が降る。女の子はケーキを食べる。', splitlines=False)
        ttl.write_json(TEST_DATA / 'testx.json', doc)

    def test_read_json(self):
        docjson = os.path.join(TEST_DIR, 'data', 'test.json')
        doc = ttl.read_json(docjson)
        getLogger().debug(doc[0].to_json())
        self.assertTrue(len(doc))

    def test_ident(self):
        db = get_db(True)
        with db.ctx() as ctx:
            corpus = db.new_corpus('eng', ctx=ctx)
            doc = db.new_doc(name='eng1', title='eng1', lang='en', corpusID=corpus.ID, ctx=ctx)
            author = db.get_doc_meta_by_key(doc.name, 'author', ctx=ctx)
            # there must be no meta as of now
            self.assertIsNone(author)
            db.set_doc_meta(doc.name, 'author', 'Le Tuan Anh', ctx=ctx)
            # select it out
            doc1 = db.doc.by_id(1, ctx=ctx)
            author = db.get_doc_meta_by_key(doc1.name, 'author', ctx=ctx)
            self.assertEqual(author.value, 'Le Tuan Anh')
            # make a sentence with ident
            sent = doc1.sents.new('It rains.', ident='10000')
            sent.ID = None
            db.save_sent(sent, ctx=ctx)
            # select sentence by ident
            sid = ctx.sent.select('ident = ?', ('10000',))[0].ID
            sent = db.get_sent(sid, ctx=ctx)
            self.assertEqual(sent.text, 'It rains.')

    def test_store_objects(self):
        db = get_db(True)
        with db.ctx() as ctx:
            getLogger().info("The database should be empty right now")
            self.assertFalse(ctx.tag.select())
            # create a sample corpus
            corpus = db.new_corpus('jpn', ctx=ctx)
            title = 'Japanese Corpus 1'
            corpus.title = title
            ctx.corpus.save(corpus)
            self.assertEqual(ctx.corpus.by_id(1).title, corpus.title)
            corpus = db.corpus.select_single('ID=?', (1,), ctx=ctx)
            self.assertEqual(corpus.title, title)
            # create a document
            doc = db.new_doc(name='jpn1', title='日本語', lang='jp', corpusID=corpus.ID, ctx=ctx)
            doc1 = db.doc.by_id(1, ctx=ctx)
            self.assertEqual(doc1.name, 'jpn1')
            self.assertEqual(doc1.ID, 1)
            # add sentences from JSON
            testdoc_path = os.path.join(TEST_DIR, 'data', 'test.json')
            docjson = ttl.read_json(testdoc_path)
            docjson[0].comment = 'mikeneko ga suki desu.'
            docjson[0].tag.eng = 'I like calico cats.'
            docjson[0][0].tag.romaji = 'mi'
            docjson[1].comment = 'It rains.'
            docjson[1].tag.eng = 'It rains.'
            docjson[1][0].tag.romaji = 'ame'
            docjson[2].comment = 'The girl eats the cake.'
            docjson[2].tag.eng = 'The girl eats the cake.'
            docjson[2][0].tag.romaji = 'onna no ko'
            for sent in docjson:
                sent.ID = None
                sent.docID = doc.ID
                db.save_sent(sent, ctx=ctx)
            # test retrieve data back
            self.assertEqual(len(ctx.sent.select()), 3)
            sent = db.get_sent(1, ctx=ctx)
            self.assertTrue(sent)
            self.assertTrue(sent.tags)
            self.assertTrue(sent.tokens)
            self.assertEqual(sent.tag.eng.value, 'I like calico cats.')
            self.assertEqual(sent.comment, 'mikeneko ga suki desu.')
            getLogger().debug(sent.tags)
            getLogger().debug(sent.tokens)
            getLogger().debug(sent.concepts)
            # test lexicon
            lex = list(db.lexicon(ctx=ctx))
            self.assertEqual(len(lex), 14)
            # use limit
            lex = [(t, c) for t, c in db.lexicon(limit=2, ctx=ctx)]
            self.assertEqual(lex, [('。', 3), ('が', 2)])


class TestTTLSQLiteMeta(unittest.TestCase):

    def test_collection_meta(self):
        db = get_db(True)
        with db.ctx() as ctx:
            metas = db.get_meta(ctx=ctx)
            self.assertFalse(len(metas))
            # insert metas
            db.set_meta(key='name', value='foo', ctx=ctx)
            db.set_meta(key='search', value='bing', ctx=ctx)
            metas = db.get_meta(ctx=ctx)
            actual = set((x.key, x.value) for x in metas)
            expected = {('search', 'bing'), ('name', 'foo')}
            self.assertEqual(expected, actual)
            name = db.get_meta_by_key('name', ctx=ctx)
            self.assertEqual(name.value, 'foo')
            # set meta with existing key -> update
            db.set_meta('search', 'yahoo', ctx=ctx)
            search = db.get_meta_by_key('search', ctx=ctx)
            self.assertEqual(search.value, 'yahoo')

    def test_doc_meta(self):
        db = get_db(True)
        with db.ctx() as ctx:
            metas = db.get_doc_meta('eng1', ctx=ctx)
            self.assertFalse(len(metas))
            # insert metas
            db.set_doc_meta(name='eng1', key='name', value='foo', ctx=ctx)
            db.set_doc_meta(name='eng1', key='search', value='bing', ctx=ctx)
            db.set_doc_meta(name='vie1', key='search', value='yahoo', ctx=ctx)
            metas = db.get_doc_meta(name='eng1', ctx=ctx)
            actual = set((x.name, x.key, x.value) for x in metas)
            expected = {('eng1', 'search', 'bing'), ('eng1', 'name', 'foo')}
            metas = db.get_doc_meta(name='vie1', ctx=ctx)
            actual = set((x.name, x.key, x.value) for x in metas)
            expected = {('vie1', 'search', 'yahoo')}
            self.assertEqual(expected, actual)
            name = db.get_doc_meta_by_key('eng1', 'name', ctx=ctx)
            self.assertEqual(name.value, 'foo')
            # set meta with existing key -> update
            db.set_doc_meta('eng1', 'search', 'yahoo', ctx=ctx)
            search = db.get_doc_meta_by_key('eng1', 'search', ctx=ctx)
            self.assertEqual(search.value, 'yahoo')
            db.set_doc_meta('vie1', 'search', 'wolfram-alpha', ctx=ctx)
            search = db.get_doc_meta_by_key('vie1', 'search', ctx=ctx)
            self.assertEqual(search.value, 'wolfram-alpha')

    def test_cor_meta(self):
        db = get_db(True)
        with db.ctx() as ctx:
            metas = db.get_cor_meta('eng', ctx=ctx)
            self.assertFalse(len(metas))
            # insert metas
            db.set_cor_meta(name='eng', key='name', value='foo', ctx=ctx)
            db.set_cor_meta(name='eng', key='search', value='bing', ctx=ctx)
            db.set_cor_meta(name='vie', key='search', value='yahoo', ctx=ctx)
            metas = db.get_cor_meta(name='eng', ctx=ctx)
            actual = set((x.name, x.key, x.value) for x in metas)
            expected = {('eng', 'search', 'bing'), ('eng', 'name', 'foo')}
            metas = db.get_cor_meta(name='vie', ctx=ctx)
            actual = set((x.name, x.key, x.value) for x in metas)
            expected = {('vie', 'search', 'yahoo')}
            self.assertEqual(expected, actual)
            name = db.get_cor_meta_by_key('eng', 'name', ctx=ctx)
            self.assertEqual(name.value, 'foo')
            # set meta with existing key -> update
            db.set_cor_meta('eng', 'search', 'yahoo', ctx=ctx)
            search = db.get_cor_meta_by_key('eng', 'search', ctx=ctx)
            self.assertEqual(search.value, 'yahoo')
            db.set_cor_meta('vie', 'search', 'wolfram-alpha', ctx=ctx)
            search = db.get_cor_meta_by_key('vie', 'search', ctx=ctx)
            self.assertEqual(search.value, 'wolfram-alpha')
            # select all meta
            metas = ctx.meta_cor.select()
            expected = [{'name': 'eng', 'key': 'name', 'value': 'foo'}, {'name': 'eng', 'key': 'search', 'value': 'yahoo'}, {'name': 'vie', 'key': 'search', 'value': 'wolfram-alpha'}]
            actual = [m.to_dict() for m in metas]
            self.assertEqual(expected, actual)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
