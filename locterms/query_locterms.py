#!/usr/bin/env python3
'''
query_locterms: interactively print information about an LCSH term.

This module allows a user to contact the LoCTerms database and query it to
get information about Library of Congress Subject Heading terms.  The
LoCTerms database process must already be running.  The action to be
performed must be indicated by using one of the command line flags.
Please see the definition of main() for more information about the 
available commands.
'''

import getpass
import humanize
import keyring
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


# Global constants.
# .............................................................................

_CONN_TIMEOUT = 5000
'''Time to wait for connection to database, in milliseconds.'''

_DEFAULT_HOST = 'localhost'
'''Default network host for LoCTerms server if no explicit host is given.'''

_DEFAULT_PORT = 27017
'''Default network port for MongoDB if no explicit port number is given.'''

_DB_NAME = 'lcsh-db'
'''The name of our LoCTerms database in MongoDB.'''

_KEYRING_PATH = "org.casics.locterms"
'''The name of the keyring entry for LoCTerms client users.'''


# Main body.
# .............................................................................

# Plac automatically adds a -h argument for help, so no need to do it here.
@plac.annotations(
    describe  = ('print details about given LCSH term(s)',      'flag',   'd'),
    trace     = ('trace paths from given id to root term(s)',   'flag',   't'),
    summarize = ('print summary statistics about the database', 'flag',   'm'),
    user      = ('database user name',                          'option', 'u'),
    pswd      = ('database user password',                      'option', 'p'),
    host      = ('database server host',                        'option', 's'),
    port      = ('database connection port number',             'option', 'o'),
    nocolor   = ('do not color-code the output',                'flag',   'x'),
    nokeyring = ('do not use a keyring',                        'flag',   'X'),
    terms     = 'one or more LCSH identifiers, like sh85118553',
)

def main(describe=False, trace=False, summarize=False, user=None, pswd=None,
         host=None, port=None, nocolor=False, nokeyring=False, *terms):
    '''Query LoCTerms for information about an LCSH term.  The LoCTerms
database process must already be running.  The action to be performed must
be indicated by using one of the following two command line flags:

  -d    Describe the LCSH term(s) given on the command line
  -t    Trace the path from the given LCSH term(s) to root terms
  -m    Print some summary statistics about the database of LCSH terms

By default, this uses the operating system's keyring/keychain functionality
to get the user name, password, port number and host name needed to access
the LoCTerms database over the network.  If no such credentials are found, it
will query the user interactively for the information, and (unless the -X
argument is given) then store them in the user's keyring/keychain so that it
does not have to ask again in the future.  It is also possible to supply the
information directly on the command line using the -u, -p, -s and -o options
but this is discouraged because it is insecure on multiuser computer
systems. (Other users could run "ps" in the background and see your
credentials).  The default for the host is "localhost" and the default port
is whatever is configured in your instance of MongoDB.

If you ever need to change the information in the keyring/keychain, you can
run this program again with the -X option, and it will ask you for the values
and store them in the keyring again.

Finally, the remaining arguments on the command line are assumed to be
identifiers of terms in the Library of Congress Subject Headings (LCSH).
'''
    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "nocolor").
    # Dealing with negated variables is confusing, so turn them around here.
    colorize = 'termcolor' in sys.modules and not nocolor
    keyring  = not nokeyring

    # Check arguments.
    if sum(x for x in [describe, trace, summarize]) > 1:
        raise SystemExit(colorcode('Can only perform one action at a time.', 'error'))
    if not user or not pswd or not host or not port:
        (user, pswd, host, port) = obtain_credentials(user, pswd, host, port, keyring)
    if keyring:
        # Save the credentials if they're different from what's saved.
        (s_user, s_pswd, s_host, s_port) = get_keyring_credentials()
        if s_user != user or s_pswd != pswd or s_host != host or s_port != port:
            save_keyring_credentials(user, pswd, host, port)
    if not any([describe, trace, summarize]):
        raise SystemExit(colorcode('No action specified. (Use -h for help.)', 'warning'))
    if not summarize and not terms:
        raise SystemExit(colorcode('Need LCSH identifiers. (Use -h for help.)', 'error'))

    # Do some simple sanity checks:
    for t in terms:
        if not t.startswith('sh'):
            msg('Identifiers must be LCSH identifiers, like sh89003287',
                'error', colorize)
            return
    if not port_occupied(host, int(port)):
        msg('Cannot connect to port {} -- is the database running?'.format(port),
            'error', colorize)
        return

    # Connect to the LCSH database.
    url = 'mongodb://'
    if user:
        url = url + user
    if pswd:
        url = url + ':' + pswd
    url += '@' + host + ':' + str(port) + '/' + _DB_NAME + '?authSource=admin'
    db = MongoClient(url, tz_aware=True, serverSelectionTimeoutMS=_CONN_TIMEOUT)
    lcsh_db = db[_DB_NAME]
    lcsh_terms = lcsh_db.terms
    lcsh_info = lcsh_db.info

    # Watch out for the fact that with MongoDB, we may be able to connect yet
    # still be unable to actually do anything.  The next step acts as a test.
    try:
        count = lcsh_info.count()
    except Exception as e:
        raise SystemExit(colorcode('Unable to query database: {}'.format(e), 'error'))

    # Do the work.
    try:
        msg('='*70, 'dark', colorize)
        if summarize:
            print_summary(lcsh_terms, lcsh_info, colorize)
        if trace:
            for t in terms:
                trace_term(lcsh_terms, t, colorize)
        if describe:
            for t in terms:
                explain_term(lcsh_terms, t, colorize)
                msg('')
        msg('='*70, 'dark', colorize)
    except Exception as e:
        msg(colorcode(e, 'error'))


def trace_term(lcsh_terms, term, colorize):
    '''Trace a term's "broader" links until we can't go any further.'''
    entry = lcsh_terms.find_one({'_id': term})
    if not entry:
        msg('Could not find {} in the database'.format(term), 'error', colorize)
        return
    print_paths(get_paths(lcsh_terms, entry), colorize)


def explain_term(lcsh_terms, term, colorize):
    '''Print a description of one term.'''
    entry = lcsh_terms.find_one({'_id': term})
    if not entry:
        msg('Could not find {} in the database'.format(term), 'error', colorize)
        return
    print_details(entry, colorize)


def get_paths(lcsh_terms, entry):
    '''Recursively follow "broader" term links, and return a list of results.'''
    paths = []
    if not entry['broader']:
        paths = [[entry]]
    else:
        for broader in entry['broader']:
            parent = lcsh_terms.find_one({'_id': broader})
            if not parent:
                raise SystemExit(colorcode('Broader term {} not found.'.format(broader),
                                           'error', colorize))
            if parent['broader']:
                for path in get_paths(lcsh_terms, parent):
                    paths.append([entry] + path)
            else:
                paths.append([entry] + [parent])
    return paths


def print_paths(paths, colorize):
    '''Print a summary of the terms in the given list of paths.'''
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
    '''Print one term, as an identifier plus its label.'''
    label = term['label'] if term['label'] else '(no label)'
    msg('{}{}: {}'.format(indent, colorcode(term['_id'], 'bold', colorize), label))


def print_details(entry, colorize=False):
    '''Print details about a single term.'''
    label = entry['label'] if entry['label'] else '(no label)'
    msg(colorcode(entry['_id'], 'bold', colorize) + ':')
    msg(colorcode('         URL: ', 'dark', colorize) +
        'http://id.loc.gov/authorities/subjects/' + entry['_id'] + '.html')
    msg(colorcode('       label: ', 'dark', colorize) + label)
    if entry['alt_labels']:
        msg(colorcode('  alt labels: ', 'dark', colorize)
            + '\n              '.join(entry['alt_labels']))
    else:
        msg('  alt labels: (none)', 'dark', colorize)
    if entry['narrower']:
        msg(colorcode('    narrower: ', 'dark', colorize) + ', '.join(entry['narrower']))
    else:
        msg('    narrower: (none)', 'dark', colorize)
    if entry['broader']:
        msg(colorcode('     broader: ', 'dark', colorize) + ', '.join(entry['broader']))
    else:
        msg('     broader: (none)', 'dark', colorize)
    if entry['topmost']:
        msg(colorcode('     topmost: ', 'dark', colorize) + ', '.join(entry['topmost']))
    else:
        msg('     topmost: (none)', 'dark', colorize)
    if entry['note']:
        prefix = colorcode('        note: ', 'dark', colorize)
        indent = len(prefix)
        text = pprint.pformat(entry['note'], width=77-indent)
        text = text[1:-1]
        msg(prefix + text)
    else:
        msg('        note: (none)', 'dark', colorize)


def print_summary(lcsh_terms, lcsh_info, colorize=False):
    '''Print some statistics about the LoCTerms database.'''
    info = lcsh_info.find_one({})
    count = lcsh_terms.count()
    msg('Number of LCSH terms in database: {}'.format(humanize.intcomma(count)))
    msg('Date of issue of LCSH terms: {}'.format(info['lcsh_file_date']))
    msg('Source of LCSH terms: {}'.format(info['lcsh_source']))


# Utilities for printing messages.
# .............................................................................

def msg(text, flags=None, colorize=True):
    if colorize:
        print(colorcode(text, flags), flush=True)
    else:
        print(text, flush=True)


def colorcode(text, flags=None, colorize=True):
    (prefix, color, attributes) = color_codes(flags)
    if colorize:
        if attributes and color:
            return colored(text, color, attrs=attributes)
        elif color:
            return colored(text, color)
        elif attributes:
            return colored(text, attrs=attributes)
        else:
            return text
    elif prefix:
        return prefix + ': ' + text
    else:
        return text


def color_codes(flags):
    color  = ''
    prefix = ''
    attrib = []
    if type(flags) is not list:
        flags = [flags]
    if 'error' in flags:
        prefix = 'ERROR'
        color = 'red'
    if 'warning' in flags:
        prefix = 'WARNING'
        color = 'yellow'
    if 'info' in flags:
        color = 'green'
    if 'white' in flags:
        color = 'white'
    if 'blue' in flags:
        color = 'blue'
    if 'grey' in flags:
        color = 'grey'
    if 'cyan' in flags:
        color = 'cyan'
    if 'underline' in flags:
        attrib.append('underline')
    if 'bold' in flags:
        attrib.append('bold')
    if 'reverse' in flags:
        attrib.append('reverse')
    if 'dark' in flags:
        attrib.append('dark')
    return (prefix, color, attrib)


# Credentials/keyring functions
# .............................................................................
# Explanation about the weird way this is done: the Python keyring module
# only offers a single function for setting a value; ostensibly, this is
# intended to store a password associated with an identifier.  However, we
# need to store several pieces of information, including a user name.  Since
# we don't know the user name ahead of time, we can't use that as a key to
# look up the credentials.  So, the approach here is to subvert the
# set_password() functionality to store the user name under the fake user
# "username", the password under the fake user "password", the host under the
# fake user "host", etc.

def get_keyring_credentials(user=None):
    '''Looks up user credentials for user 'user'.  If 'user' is None, gets
    the user name stored in the "username" field.'''
    if not user:
        user = keyring.get_password(_KEYRING_PATH, "username")
    password = keyring.get_password(_KEYRING_PATH, "password")
    host     = keyring.get_password(_KEYRING_PATH, "host")
    port     = keyring.get_password(_KEYRING_PATH, "port")
    return (user, password, host, port)


def save_keyring_credentials(user, password, host, port):
    '''Saves the user, password, host and port info to the keyring.'''
    keyring.set_password(_KEYRING_PATH, "username", user)
    keyring.set_password(_KEYRING_PATH, "password", password)
    keyring.set_password(_KEYRING_PATH, "host", host)
    keyring.set_password(_KEYRING_PATH, "port", str(port))
    msg('Credentials for user "{}" saved to keyring'.format(user), 'info')


def obtain_credentials(user=None, pswd=None, host=None, port=None, keyring=True):
    (s_user, s_pswd, s_host, s_port) = (None, None, None, None)
    if keyring:
        (s_user, s_pswd, s_host, s_port) = get_keyring_credentials()

    if not host:
        host = s_host or input("Database host (default: {}): ".format(_DEFAULT_HOST))
        host = host or _DEFAULT_HOST
    if not port:
        port = s_port or input("Database port (default: {}): ".format(_DEFAULT_PORT))
        port = port or _DEFAULT_PORT
    if not user:
        user = s_user or input("User name: ")
    if not pswd:
        pswd = s_pswd or getpass.getpass()

    return (user, pswd, host, port)


# Miscellaneous utilities.
# .............................................................................

def port_occupied(host, port):
    '''Returns True if the given port occupied, false if not.'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
    except socket.error as e:
        # This has value 48 on macOS but apparently 98 on others.
        return (e.errno in [48, 98])
    finally:
        sock.close()


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
