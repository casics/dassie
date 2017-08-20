#!/usr/bin/env python3.4

import sys
import os
import bson
from collections import defaultdict
from pymongo import MongoClient

# Connect to the database

db      = MongoClient(tz_aware=True, connect=True)
lcsh_db = db['lcsh']
terms   = lcsh_db.terms
topdown = lcsh_db.topdown

# Basic algorithm:
# - iterate over all terms that have no value for 'broader':
#   - add term to collection 'topdown'
#   - if it has nonempty 'narrower' list:
#     - create subdocument
#     - recursively expand

def list_narrower(narrower_terms):
    subdocs = []
    for term in narrower_terms:
        full_item = terms.find_one({'_id': term})
        full_item['narrower'] = list_narrower(full_item['narrower'])
        subdocs.append(full_item)
    return subdocs


try:
    count = 0
    cursor = terms.find({'broader': []}, no_cursor_timeout=True)
    print('{} total terms without a broader term'.format(cursor.count()))
    for entry in terms.find({'broader': []}, no_cursor_timeout=True):
        new_entry = entry.copy()
        new_entry['narrower'] = list_narrower(entry['narrower'])
        topdown.replace_one({'_id': entry['_id']}, new_entry, upsert=True);
        count += 1
        print('{} = {} size {}'.format(count, entry['_id'], len(bson.BSON.encode(new_entry))))

except Exception as err:
    print(err)

print('Done')
