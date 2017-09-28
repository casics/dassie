#!/usr/bin/env python2.7
#
# @file    parse-lcsh-stream.py
# @brief   Parse LCSH .nt file and build a simple index in a MongoDB database
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->
#
# SUMMARY
#
# This program is designed to parse the Library of Congress subject terms
# file "authoritiessubjects.nt.skos" (from http://id.loc.gov/download/) and
# create a MongoDB database collection containing the terms found in the file.
# The parts of the LCSH terms we are interested in are the following:
# - the identifier, from (e.g.) http://id.loc.gov/authorities/subjects/sh85098119
# - one preflabel (a string)
# - one or more altlabels
# - one or more broader terms
# - one or more narrower terms
# - one 'note' associated with a term
#
# PREREQUISITES
#
# This purposefully uses Python 2.7, because on my OS X 10.10 laptop, I
# couldn't get RDF installed under python 3.
#
# This assumes that a Mongo DB is already running on the local host.  It also
# assumes that there are no authentication issues.  (If those conditions are
# not held, you need to change the parameters to the MongoClient call below.)
#
# USAGE
#
# Start MongoDB on the local host.
# Run the following in a terminal shell:
#   ./parse-lcsh-and-create-db.py  authoritiessubjects.nt.skos
#

import RDF
import sys
import os
from collections import defaultdict
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT


# Helpers
# .............................................................................

def get_id(term):
    return term[term.rfind('/') + 1:].encode('utf-8')


def get_topmost(term):
    if not term['broader']:
        return [term['_id']]
    broader_list = []
    for parent in term['broader']:
        # The values will be identifiers, so we look up each one.
        entry = lcsh.find_one({'_id': parent}, {'broader': 1, 'topmost': 1})
        if entry['topmost'] == None:
            # We've already computed the top-most term for this one, and
            # this *is* the top-most for this chain.
            broader_list.append(entry['_id'])
        elif entry['topmost']:
            # We've already computed the top-most term for this one.
            broader_list.append(entry['topmost'])
        elif entry['broader']:
            broader_list.append(get_topmost(entry))
        else:
            broader_list.append(entry['_id'])
    # Flatten the nested lists that result from the code above, then also
    # remove possible duplicate.
    return list(set(flatten(broader_list)))


def flatten(items, seqtypes=(list, tuple)):
    # Solution from http://stackoverflow.com/a/10824086/743730
    for i, x in enumerate(items):
        while i < len(items) and isinstance(items[i], seqtypes):
            items[i:i+1] = items[i]
    return items


# Main code.
# .............................................................................

# Check command line args.

if len(sys.argv) < 2:
    raise RuntimeError('Missing file argument')

# Fix up handling of utf8.

reload(sys)
sys.setdefaultencoding('utf8')

# Make print be unbuffered.

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# Connect to the database

db = MongoClient(tz_aware=True, connect=True)
lcsh_db = db['lcsh']
lcsh = lcsh_db.terms

# Parse and build basic database.
#
# Note: we need to make sure that all terms have an entry in the database
# before we try to fill in values for the 'broader' and 'narrower' fields, so
# that we have a place to put broader/narrower info as we encounter it.  For
# reasons I can't fathom, when using parse_as_stream() on the file, the Pyton
# RDF library parser does NOT return triples in the linear order present in
# the file.  It seems to group them by subject when the same subject has a
# run of triples one after the other, and then it returns them in
# (apparently) reverse order -- but not completely reverse order.  It's
# baffling, and it would be a problem for making sure that all the prefLabels
# are entered first.  HOWEVER, we are saved from having to do multiple passes
# over the file by the fact that the LCSH .nt file puts all the prefLabel
# triples at the beginning, so the following one-pass approach still ends up
# working.  (Thank you, Library of Congress Linked Data creators!)

print('Initial pass and database creation')
try:
    parser = RDF.NTriplesParser()
    count_triples = 0
    count_terms = 0
    for triple in parser.parse_as_stream('file:' + sys.argv[1]):
        count_triples += 1

        # This assumes that all the prefLabels appear first in the file,
        # before any other components, so that we will insert all the terms
        # into the database before we move on to adding other info.  We can't
        # build up the objects in memory before adding them to the database
        # because we'll end up with too much in memory.

        predicate = str(triple.predicate)
        if predicate.endswith('prefLabel'):
            count_terms += 1
            id = get_id(str(triple.subject))
            if id.startswith('sj'):
                print("*** skipping children's subject id {}".format(id))
                continue
            if lcsh.find_one({'_id': id}, {}):
                print('*** skipping duplicate id {}'.format(id))
                continue
            label = str(triple.object).encode('utf-8', 'replace')
            lcsh.insert_one({'_id' : id, 'label': label, 'alt_labels': [],
                             'broader': [], 'narrower': [], 'topmost': [],
                             'note': None})
            continue

        if predicate.endswith('altLabel'):
            label = str(triple.object).encode('utf-8', 'replace')
            if label == 'LL':
                continue
            id = get_id(str(triple.subject))
            if id.startswith('sj'):
                print("*** skipping children's subject id {}".format(id))
                continue
            entry = lcsh.find_one({'_id': id}, {'alt_labels': 1})
            new = entry['alt_labels'] + [label]
            lcsh.update_one({'_id': id}, {'$set': {'alt_labels': new}}, upsert=False)
            continue

        if predicate.endswith('broader'):
            id = get_id(str(triple.subject))
            if id.startswith('sj'):
                print("*** skipping children's subject id {}".format(id))
                continue
            broader_id = get_id(str(triple.object))
            if broader_id.startswith('sj'):
                print("*** skipping children's subject broader_id {}".format(broader_id))
                continue
            entry = lcsh.find_one({'_id': id}, {'broader': 1})
            if not entry:
                print('*** no entry for broader {}'.format(id))
                continue
            new = entry['broader'] + [broader_id]
            lcsh.update_one({'_id': id}, {'$set': {'broader': new}}, upsert=False)
            continue

        if predicate.endswith('core#note'):
            id = get_id(str(triple.subject))
            if id.startswith('sj'):
                print("*** skipping children's subject id {}".format(id))
                continue
            entry = lcsh.find_one({'_id': id}, {'note': 1})
            if not entry:
                print('*** no entry for note {}'.format(id))
                continue
            note = str(triple.object).strip()
            if entry['note']:
                note = entry['note'] + '\n' + note
            lcsh.update_one({'_id': id}, {'$set': {'note': note}}, upsert=False)
            continue

        if predicate.endswith('core#editorialNote'):
            id = get_id(str(triple.subject))
            if id.startswith('sj'):
                print("*** skipping children's subject id {}".format(id))
                continue
            note = str(triple.object).strip()
            if 'Record generated for validation purposes' in note:
                lcsh.update_one({'_id': id}, {'$set': {'validation-record': True}},
                                upsert=False)
                print('*** {} marked as validation record'.format(id))
            else:
                entry = lcsh.find_one({'_id': id}, {'note': 1})
                if entry['note']:
                    note = entry['note'] + '\n' + note
                lcsh.update_one({'_id': id}, {'$set': {'note': note}}, upsert=False)
            continue

        if predicate.endswith('collection_TopicSubdivisions'):
            id = get_id(str(triple.subject))
            if id.startswith('sj'):
                print("*** skipping children's subject id {}".format(id))
                continue
            lcsh.update_one({'_id': id}, {'$set': {'topic-subdivision': True}},
                            upsert=False)
            print('*** {} marked as topic subdivision'.format(id))
            continue

        if predicate.endswith('core#member'):
            if str(triple.object).endswith('GenreFormSubdivisions'):
                id = get_id(str(triple.subject))
                if id.startswith('sj'):
                    print("*** skipping children's subject id {}".format(id))
                    continue
                lcsh.update_one({'_id': id}, {'$set': {'genre-form': True}}, upsert=False)
                print('*** {} marked as genre form'.format(id))
            continue

        if count_triples % 1000 == 0:
            print('{} triples'.format(count_triples))
        if count_terms != 0 and count_terms % 1000 == 0:
            print('{} terms'.format(count_terms))

except Exception as err:
    print(err)
    import ipdb; ipdb.set_trace()


# Trace the narrower terms, and populate the 'narrower' field values.
#
# The 2014 version had URIs for narrower, but the 2016 deoesn't.
# So, we have to compute it ourselves.

print('Populating field "narrower"')
try:
    count = 0
    for entry in lcsh.find({'broader': {'$ne': []}}, {'broader': 1}):
        count += 1
        for id in entry['broader']:
            broader = lcsh.find_one({'_id': id}, {'narrower': 1})
            if not broader:
                print('*** broader id {} not found'.format(id))
                import ipdb; ipdb.set_trace()
            value = broader['narrower'] + [entry['_id']]
            lcsh.update_one({'_id': id}, {'$set': {'narrower': value}}, upsert=False)
        if count % 1000 == 0:
            print('{}'.format(count))
except Exception as err:
    print(err)
    import ipdb; ipdb.set_trace()


# Trace the topmost terms, and populate the fields.
#
# We can't do this step until we have all of the terms in the database.
#
# The simple-minded approach used here is to trace the 'broader' links from
# every term upward, until we hit a term that has no value for 'broader'.
# Terms with no 'broader' term are assumed to be the topmost terms.

print('Populating field "topmost"')
try:
    count = 0
    # First find all the terms that have no broader terms, and set the values
    # of their 'topmost' fields to None to indicate that there are no higher-
    # level terms for those.
    for entry in lcsh.find({'broader': []}, {'broader': 1, 'topmost': 1}):
        lcsh.update_one({'_id': entry['_id']}, {'$set': {'topmost': None}})
        count += 1
        if count % 1000 == 0:
            print(count)
    print('{} terms are topmost'.format(count))

    count = 0
    for entry in lcsh.find({'topmost': []}, {'broader': 1, 'topmost': 1}):
        top = get_topmost(entry)
        lcsh.update_one({'_id': entry['_id']}, {'$set': {'topmost': top}})
        count += 1
        if count % 1000 == 0:
            print(count)

except Exception as err:
    print(err)
    import ipdb; ipdb.set_trace()


print('Creating indexes')

lcsh.create_index( [('broader', ASCENDING )], background=True)
lcsh.create_index( [('narrower', ASCENDING )], background=True)
lcsh.create_index( [('topmost', ASCENDING )], background=True)
lcsh.create_index( [('label', TEXT ), ('alt_labels', TEXT )], background=True)

print('Done')
