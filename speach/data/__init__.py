import os

MY_DIR = os.path.dirname(os.path.realpath(__file__))
INIT_TTL_SQLITE = os.path.join(MY_DIR, 'scripts', 'init_corpus.sql')
ELAN_BLANK_FILE = os.path.join(MY_DIR, 'elan', 'blank.eaf')
