import bibtexparser
import logging

from bs4 import BeautifulSoup
from numpy.lib.shape_base import tile
from requests import get
from re import sub, UNICODE

DBLP_PREFIX = "https://dblp.org/rec/"
DBLP_PREFIX_SIZE = len(DBLP_PREFIX)
DBLP_API = "https://dblp.org/search/publ/api?"


def query_db(title, num_entries=300):
    query = '+'.join(title.lower().split())
    logging.info('Query: {}'.format(query))
    response = get(DBLP_API + 'q=' + query + '&h=' + str(num_entries))
    # logging.info('Response: {}'.format(resp.text))
    return BeautifulSoup(response.content, 'lxml')


def normalize_title(title):
    # change to lowercase and remove all non alphnumeric characters
    title = title.lower()
    title = sub(': ', ' - ', title)
    title = sub('\n', ' ', title)
    title = sub(r'[^0-9a-zA-Z]+', '', title)
    return title


def normalize_bib_title(title):
    # remove latex code and encoding problems
    title = sub(r'[’\'–]', ' ', title)
    title = sub(r'[{}\\\"^,]', '', title)
    title = sub('textendash', '', title)
    title = sub(r'\$.*?\$', '', title)
    return title


def get_bib_entry(match, long=False):
    dblp_url = match.find("url").text
    assert(dblp_url.startswith(DBLP_PREFIX))
    bib_url = dblp_url[:DBLP_PREFIX_SIZE] + 'bib' + str(int(long)) + '/' + dblp_url[DBLP_PREFIX_SIZE:]
    bib_resp = get(bib_url)
    bib_entry = bibtexparser.loads(bib_resp.text)
    if not long:
        try:
            bib_entry.entries[0]['doi'] = match.find("doi").text
        except AttributeError:
            logging.warning('No DOI found')
    try:
        bib_entry.entries[0]['author'] = bib_entry.entries[0]['author'].replace('\n', ' ')
        bib_entry.entries[0]['title'] = bib_entry.entries[0]['title'].replace('\n', ' ')
    except KeyError:
        logging.warning('Author or title missing in dblp entry')
    return bib_entry


def dblp_lookup(title, long=False):
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
                # ToDo: Allow title expansion for incomplete titles
                continue
            matches[_id] = pub_info
        # If there is only one match accept arxiv tech reports
        if len(matches) == 1:
            match = next(iter(matches.values()))
            return get_bib_entry(match, long)
        # otherwise select an official publication
        elif len(matches) > 1:
            for match in matches:
                _match = matches[match]
                if _match.find("venue").text == 'CoRR':
                    continue
                return get_bib_entry(_match, long)
        else:
            logging.warning('No matching publication found')
            return False
