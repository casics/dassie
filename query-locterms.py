#!/usr/bin/env python3
#
# @file    cataloguer.py
# @brief   Creates a database of all projects in repository hosts
# @author  Michael Hucka

import sys
import operator
import os
import plac
import pprint
from pymongo import MongoClient

sys.path.append('../lcsh')
sys.path.append('../common')

from utils import *


# Main body.
# .............................................................................

def main(print_term=False, trace=False, *terms):
    if not trace and not print_term:
        raise SystemExit('No action specified. Use -h for help.')
    if trace and print_term:
        raise SystemExit('Can only perform one action at a time.')
    if not terms:
        raise SystemExit('No LCSH terms given. Use -h for help.')
    for t in terms:
        if not t.startswith('sh'):
            raise SystemExit('identifiers must be LCSH identifiers, like sh960086680')

    # Connect to the LCSH database
    db      = MongoClient(tz_aware=True, connect=True)
    lcsh_db = db['lcsh-db']
    lcsh    = lcsh_db.terms

    # Do the work.
    if trace:
        for t in terms:
            print('='*70)
            trace_term(lcsh, t)
    if print_term:
        for t in terms:
            print('='*70)
            explain_term(lcsh, t)
    if trace or print_term:
        print('='*70)


def trace_term(lcsh, term):
    entry = lcsh.find_one({'_id': term})
    if not entry:
        raise SystemExit('Could not find {}'.format(term))
    print_paths(get_paths(lcsh, entry))


def explain_term(lcsh, term):
    entry = lcsh.find_one({'_id': term})
    if not entry:
        raise SystemExit('Could not find {}'.format(term))
    print_details(entry)


def get_paths(lcsh, entry):
    paths = []
    if not entry['broader']:
        paths = [[entry]]
    else:
        for broader in entry['broader']:
            parent = lcsh.find_one({'_id': broader})
            if not parent:
                raise SystemExit('Broader term {} not found.'.format(broader))
            if parent['broader']:
                for path in get_paths(lcsh, parent):
                    paths.append([entry] + path)
            else:
                paths.append([entry] + [parent])
    return paths


def print_paths(paths):
    # Paths assumed to be a list of lists of the form:
    # [ [leaf_term, parent_term, parent_parent_term, ...],
    #   [leaf_term, parent_term, parent_parent_term, ...],
    #   ...
    # ]
    for p in paths:
        from_top = list(reversed(p))
        print_one(from_top[0])
        indent = '└─ '
        for index, term in enumerate(from_top[1:]):
            print_one(term, indent)
            indent = '   ' + indent
        print('')


def print_one(term, indent=''):
    label = term['label'] if term['label'] else '(no label)'
    print('{}{}: {}'.format(indent, term['_id'], label))


def print_details(entry):
    label = entry['label'] if entry['label'] else '(no label)'
    print(entry['_id'] + ':')
    print('         URL: http://id.loc.gov/authorities/subjects/' + entry['_id'] + '.html')
    print('       label: ' + label)
    if entry['alt_labels']:
        print('  alt labels: ' + '\n              '.join(entry['alt_labels']))
    else:
        print('  alt labels: (none)')
    if entry['narrower']:
        print('    narrower: ' + ', '.join(entry['narrower']))
    else:
        print('    narrower: ' + ', '.join(entry['narrower']))
    if entry['broader']:
        print('     broader: ' + ', '.join(entry['broader']))
    else:
        print('     broader: (none)')
    if entry['topmost']:
        print('     topmost: ' + ', '.join(entry['topmost']))
    else:
        print('     topmost: (none)')
    if entry['note']:
        prefix = '        note: '
        indent = len(prefix)
        text = pprint.pformat(entry['note'], width=77-indent)
        text = text[1:-1]
        print(prefix + text)
    else:
        print('        note: (none)')


# Plac annotations for main function arguments
# .............................................................................
# Argument annotations are: (help, kind, abbrev, type, choices, metavar)
# Plac automatically adds a -h argument for help, so no need to do it here.

main.__annotations__ = dict(
    print_term = ('print details about given LCSH term',             'flag', 'p'),
    trace      = ('trace paths from given identifier to root terms', 'flag', 't'),
    terms      = 'one or more LCSH identifiers, like sh85118553',
)

# Entry point
# .............................................................................

def cli_main():
    plac.call(main)

cli_main()
