#!/usr/bin/env python2.7

import RDF
import sys
import os
from collections import defaultdict
from pymongo import MongoClient

# Fix up handling of utf8

reload(sys)
sys.setdefaultencoding('utf8')

# Connect to the database

db = MongoClient(tz_aware=True, connect=True)
lcsh_db = db['lcsh']
lcsh = lcsh_db.terms

# Basic algorithm:
# - put all terms that have a null 'narrower' into list "unfound"
# - iterate over all terms that have a non-null 'narrower'
#   - call emitter(term, indentation)
#
# emitter(term, indentation):
# - emit term label & newline
# - if term has a non-null 'narrower' term:
#   - remove term from M
#   - for each item in term's 'narrower' list:
#     - call emitter(term, indentation + 4)

def output(entry, indentation=''):
    print('{}{} ({})'.format(indentation, entry['_id'], str(entry['label'])))
    for item in entry['narrower']:
        unfound.discard(item)
        output(lcsh.find_one({'_id': item}), indentation + '\t')

try:
    unfound = set()
    for entry in lcsh.find({'narrower': {'$eq': []}}, {},
                           no_cursor_timeout=True):
        unfound.add(entry['_id'])

    for entry in lcsh.find({'narrower': {'$ne': []}}, {'narrower': 1, 'label': 1},
                           no_cursor_timeout=True):
        output(entry)

    if len(unfound) > 0:
        print('*** {} terms left not found'.format(len(unfound)))

except Exceptions as err:
    print(err)
    import ipdb; ipdb.set_trace()

print('Done')
