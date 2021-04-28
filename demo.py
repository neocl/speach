import nltk
from speach import ttl
from speach.sqlite import TTLSQLite


# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def dump_sent(sent):
    ''' Print a sentence to console '''
    print("Raw: {}".format(sent.text))
    print("Tokens: {}".format(sent.tokens))
    print("Concepts: {}".format(sent.concepts))
    for c in sent.concepts:
        print("    > {}".format(c))
    print(sent.to_json())


# ------------------------------------------------------------------------------
# Demo script
# ------------------------------------------------------------------------------

# create a TTL database
db = TTLSQLite('data/demo.db')

# create a sample corpus (if needed)
encor = db.ensure_corpus(name='eng', title='English sentences')
# create a sample document in corpus 'eng' (if needed)
endoc = db.ensure_doc(name='eng1', title='English sample sentences #1', lang='eng', corpus=encor)

# get document by name
doc = db.doc.select_single('name=?', ('eng1',))
# if the document is empty, create a sample sentence inside
if not db.sent.select('docID=?', (doc.ID,)):
    sent = ttl.Sentence("I am a short sentence.")
    # tokenize the sentence with NLTK tokenizer
    tokens = nltk.word_tokenize(sent.text)
    sent.import_tokens(tokens)
    # add concepts
    sent.new_concept('01436003-a', 'short', tokens=[3])
    sent.new_concept('06285090-n', 'sentence', tokens=[4])
    # comment on sentences
    sent.comment = 'This is just an example to demonstrate how to use TTL.'
    # print it out
    dump_sent(sent)
    # save it to document 'eng1'
    sent.docID = doc.ID
    db.save_sent(sent)

    # create a second sentence with MWE
    calico_text = 'I like calico cat.'
    calico_cat_synset = '02123242-n'
    if not db.sent.select('text = ?', (calico_text,)):
        sent = ttl.Sentence(calico_text)
        sent.new_tag('三毛猫が好きです。', tagtype='jpn')
        sent.import_tokens(nltk.word_tokenize(sent.text))
        # create concepts
        sent.new_concept('01777210-v', 'like', tokens=[1])
        sent.new_concept(calico_cat_synset, 'calico cat', tokens=[2, 3])  # MWE -> tokens=[2,3]
        sent[2].new_tag('+', tagtype='MWE')
        sent[3].new_tag('+', tagtype='MWE')
        dump_sent(sent)
        # save it to database
        sent.docID = doc.ID
        db.save_sent(sent)

print("Done!")
