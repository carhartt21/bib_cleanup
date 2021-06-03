# -*- coding: utf-8 -*-
import bibtexparser
import logging

from bs4 import BeautifulSoup
from numpy.lib.shape_base import tile
from argparse import ArgumentParser
from requests import get
from re import sub
from tqdm import tqdm


DBLP_PREFIX = "https://dblp.org/rec/"
DBLP_PREFIX_SIZE = len(DBLP_PREFIX)
DBLP_API = "https://dblp.org/search/publ/api?"


def query_db(title, num_entries=300):
    query = '+'.join(title.lower().split())
    # logging.info('Query: {}'.format(query))
    response = get(DBLP_API + 'q=' + query + '&h=' + str(num_entries))
    # logging.info('Response: {}'.format(resp.text))
    return BeautifulSoup(response.content, 'lxml')


def normalize_title(title):
    # change to lowercase and remove all non alphnumeric characters
    title = title.lower()
    title = sub(': ', ' - ', title)
    title = sub('textendash', '-', title)
    title = sub('\n', ' ', title)
    title = sub('[^0-9a-zA-Z]+', '', title)
    return title


def normalize_bib_title(title):
    # remove latex code
    title = sub(r'’\'', ' ', title)
    title = sub(r'[{}\\\"^,]', "", title)
    title = sub(r'\$.*?\$', '', title)
    return title


def dblp_lookup(title):
    title = normalize_bib_title(title)
    logging.info('Updating: \"{}\"'.format(title))
    soup = query_db(title)
    pub_hits = soup.find_all("hits")
    for hits in pub_hits:
        matches = {}
        if hits['total'] == '0':
            logging.warning('Search results empty')
            return False
        for pub_hit in hits.find_all("hit"):
            _id = pub_hit['id']
            pub_info = pub_hit.find("info")
            pub_title = pub_info.find("title").text.strip()
            _title = normalize_title(title)
            _pub_title = normalize_title(pub_title)
            if not _title == _pub_title:
                #     if _pub_title.startswith(_title):
                #         logging.warning('Expanding {} to {}'.format(title, pub_title))
                #     else:
                continue
            matches[_id] = pub_info
        # If there is only one match accept arxiv tech reports
        if len(matches) == 1:
            match = next(iter(matches.values()))
            doi = ''
            try:
                doi = match.find("doi").text
            except AttributeError:
                logging.warning('No DOI found')
            dblp_url = match.find("url").text
            bib_url = dblp_url[:DBLP_PREFIX_SIZE] + 'bib0/' + dblp_url[DBLP_PREFIX_SIZE:]
            bib_resp = get(bib_url)
            bib_data = bibtexparser.loads(bib_resp.text)
            if doi:
                bib_data.entries[0]['doi'] = doi
            try:
                bib_data.entries[0]['author'] = bib_data.entries[0]['author'].replace('\n', ' ')
                bib_data.entries[0]['title'] = bib_data.entries[0]['title'].replace('\n', ' ')
            except KeyError:
                logging.warning('Author or title missing in dblp entry')
        # otherwise select official publication
        elif len(matches) > 1:
            for match in matches:
                _match = matches[match]
                venue = _match.find("venue").text
                if venue == 'CoRR':
                    continue
                doi = ''
                try:
                    doi = _match.find("doi").text
                except AttributeError:
                    logging.warning('No DOI found')
                dblp_url = _match.find("url").text
                assert(dblp_url.startswith(DBLP_PREFIX))
                bib_url = dblp_url[:DBLP_PREFIX_SIZE] + 'bib0/' + dblp_url[DBLP_PREFIX_SIZE:]
                bib_resp = get(bib_url)
                bib_data = bibtexparser.loads(bib_resp.text)
                if doi:
                    bib_data.entries[0]['doi'] = doi
                try:
                    bib_data.entries[0]['author'] = bib_data.entries[0]['author'].replace('\n', ' ')
                    bib_data.entries[0]['title'] = bib_data.entries[0]['title'].replace('\n', ' ')
                except KeyError:
                    logging.warning('Author or title missing in dblp entry')
        else:
            logging.warning('No matching publication found')
            return False
        return bib_data


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
    args = _parser.parse_args()

    in_bib = args.input

    if args.output:
        out_bib = args.output
    else:
        print("+Warning: Overwriting input file")
        out_bib = in_bib
    
    failed_bib = args.failed

    print("Reading Bibliography")
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
        bib_item = dblp_lookup(title)
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

    print('---')
    print('Completed')
    print('{} Updated, {} Update failed'.format(num_read - num_failed, num_failed))
    print('Bibtex saved to {}'.format(out_bib))
    if failed_bib:
        print('Failed entries written to {}'.format('failed_'))
    print('For further information see {}'.format(log_file))
