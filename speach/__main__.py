# -*- coding: utf-8 -*-

"""
TTL Tools
"""

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import logging
try:
    from lxml import etree
    _LXML_AVAILABLE = True
except Exception:
    _LXML_AVAILABLE = False

from chirptext import TextReport, FileHelper
from chirptext import chio
from chirptext.cli import CLIApp, setup_logging

from speach import ttl, TTLSQLite, ttlig, orgmode
from speach.elan import parse_eaf_stream

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

try:
    setup_logging('logging.json', 'logs')
except Exception:
    pass


def getLogger():
    return logging.getLogger(__name__)


FORMAT_TTL = 'ttl'
FORMAT_EXPEX = 'expex'


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------

def get_doc_length(name, ctx):
    query = 'SELECT COUNT(*) FROM sentence WHERE docID = (SELECT ID FROM document WHERE name=?)'
    return ctx.select_scalar(query, (name,))


def make_db(cli, args):
    """ Convert TTL-TXT to TTL-SQLite """
    print("Reading document ...")
    ttl_doc = ttl.Document.read_ttl(args.ttl)
    print("Sentences: {}".format(len(ttl_doc)))
    db = TTLSQLite(args.db)
    db_corpus = db.ensure_corpus(name=args.corpus)
    db_doc = db.ensure_doc(name=args.doc if args.doc else ttl_doc.name, corpus=db_corpus)
    if get_doc_length(db_doc.name, ctx=db.ctx()):
        print("Document is not empty, program aborted.")
    else:
        # insert sents
        with db.ctx() as ctx:
            ctx.buckmode()
            ctx.execute('BEGIN;')
            for idx, sent in enumerate(ttl_doc):
                if args.topk and args.topk <= idx:
                    break
                print("Processing sent #{}/{}".format(idx + 1, len(ttl_doc)))
                sent.ID = None
                sent.docID = db_doc.ID
                db.save_sent(sent, ctx=ctx)
            ctx.execute('COMMIT;')
    print("Done!")


def process_tig(cli, args):
    ''' Convert TTLIG file to TTL format '''
    if args.format == FORMAT_TTL:
        sc = 0
        ttl_writer = ttl.TxtWriter.from_path(args.output) if args.output else None
        with chio.open(args.ttlig) as infile:
            for sent in ttlig.read_stream_iter(infile):
                sc += 1
                if ttl_writer is not None:
                    ttl_sent = sent.to_ttl()
                    ttl_writer.write_sent(ttl_sent)
        if ttl_writer is not None:
            print("Output file: {}".format(args.output))
        print("Processed {} sentence(s).".format(sc))
    elif args.format == FORMAT_EXPEX:
        sc = 0
        output = TextReport(args.output)
        output.print("\\newcommand{\\lit}[1]{``#1''}     %%% literal meaning")
        output.print()
        output.print()
        output.print()
        with chio.open(args.ttlig) as infile:
            for idx, sent in enumerate(ttlig.read_stream_iter(infile)):
                sc += 1
                output.print(sent.to_expex(default_ident=idx + 1))
                output.print()
                output.print()
                output.print()
    else:
        print("Format {} is not supported".format(args.format))


def jp_line_proc(line, iglines):
    igrow = ttlig.text_to_igrow(line.replace('\u3000', ' ').strip())
    iglines.append(igrow.text)
    iglines.append(igrow.tokens)
    iglines.append("")


def convert_org_to_tig(inpath, outpath):
    title, meta, lines = orgmode.read(inpath)
    meta.append(("Lines", "text tokens"))
    out = orgmode.org_to_ttlig(title, meta, lines, jp_line_proc)
    output = TextReport(outpath)
    for line in out:
        output.print(line)


def org_to_ttlig(cli, args):
    ''' Convert ORG file to TTLIG format '''
    if args.orgfile:
        # single file mode
        convert_org_to_tig(args.orgfile, args.output)
    elif args.orgdir:
        if not args.output:
            print("Output directory is required for batch mode")
            exit()
        # make output directory
        if not os.path.exists(args.output):
            print("Make directory: {}".format(args.output))
            os.makedirs(args.output)
        else:
            print("Output directory: {}".format(args.output))
        filenames = FileHelper.get_child_files(args.orgdir)
        for filename in filenames:
            infile = os.path.join(args.orgdir, filename)
            outfile = os.path.join(args.output, FileHelper.replace_ext(filename, 'tig'))
            if os.path.exists(outfile):
                print("File {} exists. SKIPPED".format(outfile))
            else:
                print("Generating: {} => {}".format(infile, outfile))
                convert_org_to_tig(infile, outfile)
    print("Done")


def make_text(sent, delimiter=' '):
    frags = []
    if sent.tokens:
        for tk in sent:
            furi = tk.find('furi', default=None)
            if furi:
                frags.append(ttlig.make_ruby_html(furi.label))
            else:
                frags.append(tk.text)
    html_text = delimiter.join(frags) if frags else sent.text
    return "<text>{}</text>".format(html_text)


def make_html(cli, args):
    ''' Convert TTL to HTML '''
    if not _LXML_AVAILABLE:
        print("lxml library is required for this function")
        exit()
    print("Reading document ...")
    ttl_doc = ttl.Document.read_ttl(args.ttl)
    output = TextReport(args.output)
    doc_node = etree.Element('doc')
    for sent in ttl_doc:
        sent_node = etree.SubElement(doc_node, 'sent')
        text_node = etree.XML(make_text(sent, delimiter=args.delimiter))
        sent_node.append(text_node)
        if sent.get_tag('translation'):
            etree.SubElement(sent_node, 'br')
            trans_node = etree.SubElement(sent_node, 'trans')
            trans_node.text = sent.get_tag('translation').label
        etree.SubElement(sent_node, 'br')
        etree.SubElement(sent_node, 'br')
    output.write(etree.tostring(doc_node, encoding='unicode', pretty_print=not args.compact))


def sec_str(a_float):
    return "{:.3f}".format(a_float)


def convert_eaf_to_csv(eaf_path, csv_path, encoding='utf-8'):
    with chio.open(eaf_path) as eaf_stream:
        elan = parse_eaf_stream(eaf_stream)
        rows = elan.to_csv_rows()
        chio.write_tsv(csv_path, rows, quoting=chio.QUOTE_MINIMAL, encoding=encoding)


def eaf_to_csv(cli, args):
    ''' Convert ELAN file (*.eaf) to TSV (Tab-separated Values) format '''
    if args.encoding:
        convert_eaf_to_csv(args.eaf, args.output, args.encoding)
    else:
        convert_eaf_to_csv(args.eaf, args.output)
    print("Output has been written to: {}".format(args.output))


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

def main():
    ''' Speach toolkit - managing, annotating, and converting natural language corpuses '''
    app = CLIApp(desc='Speach tools', logger=__name__)
    # add tasks
    task = app.add_task('convert', func=make_db)
    task.add_argument('ttl', help='TTL file')
    task.add_argument('db', help='TTL DB file')
    task.add_argument('corpus', help='Corpus name')
    task.add_argument('doc', help='Document name', default=None)
    task.add_argument('-k', '--topk', help='Only select the top k frequent elements', default=None, type=int)

    task = app.add_task('ig', func=process_tig)
    task.add_argument('ttlig', help='TTLIG file')
    task.add_argument('-o', '--output', help='Output TTL file')
    task.add_argument('-f', '--format', help='Output format', choices=[FORMAT_EXPEX, FORMAT_TTL], default=FORMAT_TTL)

    task = app.add_task('org', func=org_to_ttlig)
    task.add_argument('-f', '--orgfile', help='ORG file')
    task.add_argument('-d', '--orgdir', help='ORG directory (batch mode)')
    task.add_argument('-o', '--output', help='Output TTL file or directory')

    task = app.add_task('html', func=make_html)
    task.add_argument('ttl', help='TTL file')
    task.add_argument('-o', '--output', help='path to output HTML file')
    task.add_argument('-c', '--compact', help='Do not use pretty print', action='store_true')
    task.add_argument('-d', '--delimiter', help='Token delimiter', default=' ')

    task = app.add_task('eaf2csv', func=eaf_to_csv)
    task.add_argument('eaf', help='Input EAF file')
    task.add_argument('-o', '--output', help='path to output CSV file')
    task.add_argument('-e', '--encoding', help='Encoding of the output CSV file, defaulted to utf-8')

    # run app
    app.run()


if __name__ == "__main__":
    main()
