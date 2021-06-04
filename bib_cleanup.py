# -*- coding: utf-8 -*-
import bibtexparser
import logging

from argparse import ArgumentParser
from tqdm import tqdm
# own import
import utils


if __name__ == '__main__':
    log_file = 'info.log'
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    _parser = ArgumentParser(description='Parameters')
    _parser.add_argument('--input', type=str, help='Input bib file')
    _parser.add_argument('--output', type=str, default=None, help='Output bib file')
    _parser.add_argument('--failed', type=str, default=None, help='File for failed entries')
    _parser.add_argument('--long', type=bool, default=False, help='Use standard version of dblp entries')

    args = _parser.parse_args()

    in_bib = args.input

    if args.output:
        out_bib = args.output
    else:
        print("+Warning: Overwriting input file")
        out_bib = in_bib
    failed_bib = args.failed

    print("Reading bibliography")
    with open(in_bib, encoding='utf-8', errors='replace') as bibtex_file:
        parser = bibtexparser.bparser.BibTexParser(ignore_nonstandard_types=False)
        parser.bib_database.load_common_strings()
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    pub_titles = {}
    original_entries = {}

    num_read, num_failed, num_entries, num_skip = 0, 0, 0, 0
    for item in bib_database.entries:
        try:
            original_entries[item['ID']] = item
            pub_titles[item['ID']] = (item['title'])
        except KeyError:
            logging.warning('No title given for {}'.format(item['ID']))
            num_skip += 1
    num_entries = len(pub_titles)

    print('{} entries found - {} entries skipped'.format(num_entries, num_skip))
    failed_entries = bibtexparser.bibdatabase.BibDatabase()
    bib_output = []
    entries_updated = 0
    for id in tqdm(pub_titles, desc='Processing', ascii=True):
        title = pub_titles[id]
        num_read += 1
        bib_item = utils.dblp_lookup(title, args.long)
        if bib_item:
            bib_item.entries[0]['ID'] = id
            bib_output.append(bib_item)
        else:
            failed_entries.entries.append(original_entries[id])
            num_failed += 1

    writer = bibtexparser.bwriter.BibTexWriter(write_common_strings=True)
    writer.indent = '    '
    with open(out_bib, 'w') as bib_file:
        for item in bib_output:
            bib_file.write(writer.write(item))
        if not args.failed:
            bib_file.write('----------------------\n\n')
            bib_file.write('Original entries of publications where the update failed:')
            bib_file.write('\n\n----------------------\n\n')
            bib_file.write(writer.write(failed_entries))
        else:
            with open(failed_bib, 'w') as f_file:
                f_file.write(writer.write(failed_entries))

    print('-----')
    print('Completed')
    print('{} Updated, {} Updates failed'.format(num_read - num_failed, num_failed))
    print('Bibtex saved to {}'.format(out_bib))
    if failed_bib:
        print('Failed entries written to {}'.format('failed_'))
    print('For further information see {}'.format(log_file))
