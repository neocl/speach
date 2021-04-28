/**
 * Copyright 2018, Le Tuan Anh (tuananh.ke@gmail.com)
 * This file is adapted from the Integrated Semantic Framework
 * https://github.com/letuananh/intsem.fx
 **/

-----------------------------------------------------------
-- Meta tables
-- collections' meta
CREATE TABLE meta (
  'key' TEXT PRIMARY KEY NOT NULL, 
  'value' TEXT
);
-- documents' meta
CREATE TABLE meta_doc (
  'name' TEXT NOT NULL,
  'key' TEXT NOT NULL, 
  'value' TEXT,
  FOREIGN KEY('name') REFERENCES document('name') ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE ('name', 'key')
);
-- corpuses' meta
CREATE TABLE meta_cor (
  'name' TEXT NOT NULL,
  'key' TEXT NOT NULL, 
  'value' TEXT,
  FOREIGN KEY('name') REFERENCES corpus('name') ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE ('name', 'key')
);
CREATE INDEX IF NOT EXISTS 'meta_|_key' ON 'meta' ('key');
CREATE INDEX IF NOT EXISTS 'meta_doc_|_name' ON 'meta_doc' ('name');
CREATE INDEX IF NOT EXISTS 'meta_doc_|_key' ON 'meta_doc' ('key');
CREATE INDEX IF NOT EXISTS 'meta_cor_|_name' ON 'meta_cor' ('name');
CREATE INDEX IF NOT EXISTS 'meta_cor_|_key' ON 'meta_cor' ('key');

CREATE TABLE IF NOT EXISTS "corpus" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT
    , "name" text NOT NULL UNIQUE
    , "title" TEXT
);

CREATE TABLE IF NOT EXISTS "document" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT
    , "name" TEXT NOT NULL UNIQUE
    , "title" TEXT
    , "lang" TEXT
    , "corpusID" INTEGER NOT NULL
    , FOREIGN KEY(corpusID) REFERENCES corpus(ID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS "sentence" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT
    , "ident" VARCHAR
    , "text" TEXT
    , "docID" INTEGER
    , "flag" INTEGER
    , "comment" TEXT
    , FOREIGN KEY(docID) REFERENCES document(ID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS "token" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT
    ,"sid" INTEGER
    ,"widx" INTEGER
    ,"cfrom" INTEGER
    ,"cto" INTEGER
    ,"text" TEXT
    ,"lemma" TEXT
    ,"pos" TEXT
    ,"comment" TEXT
    ,FOREIGN KEY(sid) REFERENCES sentence(ID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS "concept" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT
    ,"sid" INTEGER NOT NULL
    ,"cidx" INTEGER
    ,"clemma" TEXT
    ,"tag" TEXT
    ,"flag" TEXT
    ,"comment" TEXT
    ,FOREIGN KEY(sid) REFERENCES sentence(ID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Sentence level tag will have a wid IS NULL
CREATE TABLE IF NOT EXISTS "tag" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT
    ,"sid" INTEGER NOT NULL
    ,"wid" INTEGER
    ,"cfrom" INTEGER
    ,"cto" INTEGER
    ,"label" TEXT
    ,"source" TEXT
    ,"tagtype" TEXT
    ,FOREIGN KEY(sid) REFERENCES sentence(ID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS "cwl" (
    "sid" INTEGER NOT NULL
    ,"cid" INTEGER NOT NULL
    ,"wid" INTEGER NOT NULL
    ,FOREIGN KEY(sid) REFERENCES sentence(ID) ON DELETE CASCADE ON UPDATE CASCADE
    ,FOREIGN KEY(cid) REFERENCES concept(ID) ON DELETE CASCADE ON UPDATE CASCADE
    ,FOREIGN KEY(wid) REFERENCES word(ID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Indices
------------------------------------------
CREATE INDEX IF NOT EXISTS "corpus_|_name" ON "corpus" ("name");
-- document
CREATE INDEX IF NOT EXISTS "document_|_name" ON "document" ("name");
CREATE INDEX IF NOT EXISTS "document_|_lang" ON "document" ("lang");
CREATE INDEX IF NOT EXISTS "document_|_corpusID" ON "document" ("corpusID");
-- sentence
CREATE INDEX IF NOT EXISTS "sentence_|_text" ON "sentence" ("text");
CREATE INDEX IF NOT EXISTS "sentence_|_ident" ON "sentence" ("ident");
CREATE INDEX IF NOT EXISTS "sentence_|_docID" ON "sentence" ("docID");
CREATE INDEX IF NOT EXISTS "sentence_|_flag" ON "sentence" ("flag");
-- token
CREATE INDEX IF NOT EXISTS "token_|_sid" ON "token" ("sid");
CREATE INDEX IF NOT EXISTS "token_|_text" ON "token" ("text");
CREATE INDEX IF NOT EXISTS "token_|_lemma" ON "token" ("lemma");
CREATE INDEX IF NOT EXISTS "token_|_pos" ON "token" ("pos");
-- concept
CREATE INDEX IF NOT EXISTS "concept_|_sid" ON "concept" ("sid");
CREATE INDEX IF NOT EXISTS "concept_|_clemma" ON "concept" ("clemma");
CREATE INDEX IF NOT EXISTS "concept_|_tag" ON "concept" ("tag");
CREATE INDEX IF NOT EXISTS "concept_|_flag" ON "concept" ("flag");
-- tag
CREATE INDEX IF NOT EXISTS "tag_|_sid" ON "tag" ("sid");
CREATE INDEX IF NOT EXISTS "tag_|_wid" ON "tag" ("wid");
CREATE INDEX IF NOT EXISTS "tag_|_label" ON "tag" ("label");
CREATE INDEX IF NOT EXISTS "tag_|_source" ON "tag" ("source");
CREATE INDEX IF NOT EXISTS "tag_|_tagtype" ON "tag" ("tagtype");
-- cwl
CREATE UNIQUE INDEX IF NOT EXISTS "cwl_|_unique" ON "cwl" ("sid", "cid", "wid");
CREATE INDEX IF NOT EXISTS "cwl_|_sid" ON "cwl" ("sid");
CREATE INDEX IF NOT EXISTS "cwl_|_cid" ON "cwl" ("cid");
CREATE INDEX IF NOT EXISTS "cwl_|_wid" ON "cwl" ("wid");
