#!/usr/bin/env python2.7
#
# The parts of the LCSH terms we are interested in are the following:
# - its own identifier, of the form http://id.loc.gov/authorities/subjects/sh85098119
# - one preflabel (a string)
# - one or more altlabels
# - one or more broader terms

import RDF
import sys
from collections import defaultdict
from pymongo import MongoClient

# Fix up handling of utf8

reload(sys)
sys.setdefaultencoding('utf8')

# Warm up the parser.

if len(sys.argv) < 2:
    raise RuntimeError('Missing file argument')

file   = sys.argv[1]

parser = RDF.Parser(name="ntriples")
store  = RDF.HashStorage("db4", options="new='yes', hash-type='bdb'")
model  = RDF.Model()
stream = parser.parse_into_model(model, 'file:' + file)

# Connect to our database.

db = MongoClient('mongodb://{}:{}@{}:{}'.format(
    'mhucka', 'casics4me', 'hyponym.caltech.edu', 9988),
                 tz_aware=True, connect=True, socketKeepAlive=True)
lcsh_db = db['lcsh']
lcsh = lcsh_db.terms

# Helper functions

def get_id(term):
    return term[term.rfind('/') + 1:].encode('utf-8')

try:
    count = 0
    for triple in model:
        if str(triple.predicate).endswith('prefLabel'):
            id = get_id(str(triple.subject))
            label = str(triple.object).encode('utf-8', 'replace')
            lcsh.insert_one({'_id' : id, 'label': label, 'alt_labels': [],
                             'broader': [], 'narrower': []})
        count += 1
        if count % 100 == 0:
            print('[{}]'.format(count))

    print('Done adding {} terms'.format(lcsh.count()))


    count = 0
    for triple in model:
        if str(triple.predicate).endswith('altLabel'):
            label = str(triple.object).encode('utf-8', 'replace')
            if label == 'LL':
                continue
            id = get_id(str(triple.subject))
            entry = lcsh.find_one({'_id': id}, {'alt_labels': 1})
            new = entry['alt_labels'] + [label]
            lcsh.update_one({'_id': id}, {'$set': {'alt_labels': new}}, upsert=False)
        count += 1
        if count % 100 == 0:
            print('[{}]'.format(count))

    print('Done adding alt labels')


    count = 0
    for triple in model:
        if str(triple.predicate).endswith('broader'):
            id = get_id(str(triple.subject))
            entry = lcsh.find_one({'_id': id}, {'broader': 1})

            if not entry:
                print('*** no entry for broader {}'.format(id))
                continue

            new = entry['broader'] + [get_id(str(triple.object))]
            lcsh.update_one({'_id': id}, {'$set': {'broader': new}}, upsert=False)
        count += 1
        if count % 100 == 0:
            print('[{}]'.format(count))

    print('Done adding broader terms')


    count = 0
    for triple in model:
        if str(triple.predicate).endswith('narrower'):
            id = get_id(str(triple.subject))
            entry = lcsh.find_one({'_id': id}, {'narrower': 1})

            if not entry:
                print('*** no entry for narrower {}'.format(id))
                continue

            new = entry['narrower'] + [get_id(str(triple.object))]
            lcsh.update_one({'_id': id}, {'$set': {'narrower': new}}, upsert=False)
        count += 1
        if count % 100 == 0:
            print('[{}]'.format(count))

    print('Done adding narrower terms')
except Exception as err:
    print(err)
    import ipdb; ipdb.set_trace()


import ipdb; ipdb.set_trace()

# broader = defaultdict(list)
# for key, value_tuple in terms.iteritems():
#     for term in value_tuple[2]:
#         broader[term] = broader[term].append(key)





pass
# Approach:
# - reduce the term id to the shxxxxx string.
# - create a dictionary of tuples:
#     term: (label, [alt labels...], [broader terms...])
#        where "term" is a string of the form shxxxxx.
# - then walk down the structure and create a second dictionary:
#     term: [narrower terms...]
#
# still need to figure out how to find the top-most terms
#
# Output:
# term (label)
#    term (label == altlabel == altlabel)
#    term (label == altlabel == altlabel)
#       term (label == altlabel == altlabel)
#    term (label == altlabel == altlabel)
