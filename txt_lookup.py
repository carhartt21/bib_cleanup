# -*- coding: utf-8 -*-
import logging
import bibtexparser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
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
    _parser = ArgumentParser(description='Parameters', formatter_class=ArgumentDefaultsHelpFormatter)
    _parser.add_argument('input', metavar='<input file>', type=str, help='Input txt file')
    _parser.add_argument('--output', metavar='<output file>', type=str, help='Output bib file')
    _parser.add_argument(
        '--failed',
        type=str,
        metavar='<additional output file>',
        default=None,
        help='File for failed entries'
    )
    _parser.add_argument('--long', type=bool, default=False, help='Use standard version of dblp entries')

    args = _parser.parse_args()

    in_txt = args.input
    if args.output:
        out_bib = args.output
    else:
        out_bib = in_txt
    failed_txt = args.failed

    pub_titles = set()

    print('Reading titles from {}'.format(in_txt))
    with open(in_txt, encoding='utf-8', errors='ignore') as input_file:
        for line in input_file:
            pub_titles.add(line)

    num_read, num_failed = 0, 0
    num_entries = len(pub_titles)

    print('{} entries found'.format(num_entries))
    failed_entries = []
    bib_output = []
    entries_updated = 0
    for title in tqdm(pub_titles, desc='Processing', ascii=True):
        num_read += 1
        bib_item = utils.dblp_lookup(title, args.long)
        if bib_item:
            bib_output.append(bib_item)
        else:
            failed_entries.append(title)
            num_failed += 1

    writer = bibtexparser.bwriter.BibTexWriter(write_common_strings=True)
    writer.indent = '    '
    with open(out_bib, 'w') as bib_file:
        for item in bib_output:
            bib_file.write(writer.write(item))
        if not failed_txt and failed_entries:
            bib_file.write('''%----------------------
% Failed publication titles:
%----------------------\n\n''')
            for entry in failed_entries:
                bib_file.write(entry + '\n\n')
        elif failed_entries:
            with open(failed_txt, 'w') as f_file:
                for entry in failed_entries:
                    f_file.write(entry + '\n\n')

    print('''-----
Completed
{} entries updated | {} updates failed
Bibtex saved to: {}'''.format(num_read - num_failed, num_failed, out_bib))
    if failed_txt:
        print('Failed entries written to: {}'.format(failed_txt))
    print('For further information see: {}'.format(log_file))
