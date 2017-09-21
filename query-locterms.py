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
from   pymongo import MongoClient
import socket
try:
    from termcolor import colored
except:
    pass

# Main body.
# .............................................................................

def main(describe=False, trace=False, user=None, password=None,
         host="localhost", port=None, nocolor=False, *terms):
    '''Query LoCTerms for information about an LCSH term. The LoCTerms database
process must already be running.  This program will connect to the database
using the user login name and password provided as arguments (-u and -p,
respectively). Additional arguments can be used to specify the host (-H) and
port (-P) on which the database process is listening.  The default for the
host is "localhost" and the default port is whatever is configured in your
instance of MongoDB.

This program also requires an argument to dictate the action to perform.
The following actions are understood; note that only one can be indicated
at a time:

  -d    Describe the term(s) given on the command line
  -t    Trace the path from the given term(s) to root terms

Finally, the remaining arguments on the command line are assumed to be
identifiers of terms in the Library of Congress Subject Headings (LCSH).
'''
    # Our default is to color output for easier reading, which means the
    # command line flag makes more sense as a negated value (i.e., "nocolor").
    # Dealing with a negated variable is confusing, so turn it around here.
    colorize = 'termcolor' in sys.modules and not nocolor

    # Check arguments are provided.
    if not trace and not describe:
        raise SystemExit(colorized('No action specified. Use -h for help.', 'error'))
    if trace and describe:
        raise SystemExit(colorized('Can only perform one action at a time.', 'error'))
    if not user or not password:
        raise SystemExit(colorized('Must provide a database user login and password.', 'error'))
    if not terms:
        raise SystemExit(colorized('No LCSH terms given. Use -h for help.', 'error'))

    # Do some simple sanity checks:
    for t in terms:
        if not t.startswith('sh'):
            msg('Identifiers must be LCSH identifiers, like sh960086680',
                'error', colorize)
            return
    if port and not port_occupied(host, int(port)):
        msg('Nothing appears to be listening at port {}'.format(port),
            'error', colorize)
        return

    # Connect to the LCSH database
    pass
    url = 'mongodb://' + user + ':' + password + '@' + host
    if port:
        url = url + ':' + port
    url = url + '/lcsh-db?authSource=admin'

    db      = MongoClient(url, tz_aware=True,
                          connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
    lcsh_db = db['lcsh-db']
    lcsh    = lcsh_db.terms

    # Do the work.
    if trace:
        for t in terms:
            msg('='*70, colorize)
            trace_term(lcsh, t, colorize)
    if describe:
        for t in terms:
            msg('='*70, colorize)
            explain_term(lcsh, t, colorize)
    if trace or describe:
        msg('='*70, colorize)


def trace_term(lcsh, term, colorize):
    entry = lcsh.find_one({'_id': term})
    if not entry:
        msg('Could not find {} in the database'.format(term), 'error', colorize)
        return
    print_paths(get_paths(lcsh, entry), colorize)


def explain_term(lcsh, term, colorize):
    entry = lcsh.find_one({'_id': term})
    if not entry:
        msg('Could not find {} in the database'.format(term), 'error', colorize)
        return
    print_details(entry, colorize)


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


def print_paths(paths, colorize):
    # Paths assumed to be a list of lists of the form:
    # [ [leaf_term, parent_term, parent_parent_term, ...],
    #   [leaf_term, parent_term, parent_parent_term, ...],
    #   ...
    # ]
    for p in paths:
        from_top = list(reversed(p))
        print_one(from_top[0], indent='', colorize=colorize)
        indent = '└─ '
        for index, term in enumerate(from_top[1:]):
            print_one(term, indent, colorize)
            indent = '   ' + indent
        msg('')


def print_one(term, indent='', colorize=False):
    label = term['label'] if term['label'] else '(no label)'
    msg('{}{}: {}'.format(indent, colorized(term['_id'], 'underline', colorize), label))


def print_details(entry, colorize=False):
    label = entry['label'] if entry['label'] else '(no label)'
    msg(entry['_id'] + ':')
    msg('         URL: http://id.loc.gov/authorities/subjects/'
        + entry['_id'] + '.html')
    msg('       label: ' + label)
    if entry['alt_labels']:
        msg('  alt labels: ' + '\n              '.join(entry['alt_labels']))
    else:
        msg('  alt labels: (none)')
    if entry['narrower']:
        msg('    narrower: ' + ', '.join(entry['narrower']))
    else:
        msg('    narrower: ' + ', '.join(entry['narrower']))
    if entry['broader']:
        msg('     broader: ' + ', '.join(entry['broader']))
    else:
        msg('     broader: (none)')
    if entry['topmost']:
        msg('     topmost: ' + ', '.join(entry['topmost']))
    else:
        msg('     topmost: (none)')
    if entry['note']:
        prefix = '        note: '
        indent = len(prefix)
        text = pprint.pformat(entry['note'], width=77-indent)
        text = text[1:-1]
        msg(prefix + text)
    else:
        msg('        note: (none)')


def port_occupied(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
    except socket.error as e:
        # True if occupied, false if not
        return (e.errno == 98)
    finally:
        sock.close()


def msg(text, flag=None, colorize=True):
    if colorize:
        print(colorized(text), flush=True)
    else:
        print(text, flush=True)


def colorized(text, flag=None, colorize=True):
    (prefix, color, attributes) = color_codes(flag)
    if colorize:
        if attributes:
            return colored(text, attrs=attributes)
        elif color:
            return colored(text, color)
        else:
            return text
    else:
        if prefix:
            return prefix + ': ' + text
        else:
            return text


def color_codes(flag):
    color  = ''
    prefix = ''
    attrib = ''
    if flag is 'error':
        prefix = 'ERROR'
        color = 'red'
    elif flag is 'warning':
        prefix = 'WARNING'
        color = 'yellow'
    elif flag is 'info':
        color = 'green'
    elif flag is 'underline':
        attrib = ['underline']
    return (prefix, color, attrib)


# Plac annotations for main function arguments
# .............................................................................
# Argument annotations are: (help, kind, abbrev, type, choices, metavar)
# Plac automatically adds a -h argument for help, so no need to do it here.

main.__annotations__ = dict(
    describe = ('print details about given LCSH term(s)',    'flag',   'd'),
    host     = ('database server host',                      'option', 'H'),
    password = ('database user password',                    'option', 'p'),
    port     = ('database connection port number',           'option', 'P'),
    user     = ('database user login',                       'option', 'u'),
    trace    = ('trace paths from given id to root term(s)', 'flag',   't'),
    nocolor  = ('do not color-code the output',              'flag',   'x'),
    terms    = 'one or more LCSH identifiers, like sh85118553',
)

# Entry point
# .............................................................................

def cli_main():
    plac.call(main)

cli_main()
