#!/usr/bin/env python3
'''
query_dassie: interactively print information about an LCSH term.

This module allows a user to contact the Dassie database and query it to
get information about Library of Congress Subject Heading terms.  The
Dassie database process must already be running.  The action to be
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
import re
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
'''Default network host for Dassie server if no explicit host is given.'''

_DEFAULT_PORT = 27890
'''Default network port for MongoDB if no explicit port number is given.'''

_DB_NAME = 'lcsh-db'
'''The name of our Dassie database in MongoDB.'''

_KEYRING = "org.casics.dassie"
'''The name of the keyring entry for Dassie client users.'''


# Main body.
# .............................................................................

# Plac automatically adds a -h argument for help, so no need to do it here.
@plac.annotations(
    describe  = ('print details about given LCSH term(s)',      'flag',   'd'),
    find      = ('find LCSH terms containing the given regex',  'flag',   'f'),
    trace     = ('trace paths from given id to root term(s)',   'flag',   't'),
    summarize = ('print summary statistics about the database', 'flag',   'm'),
    user      = ('database user name',                          'option', 'u'),
    pswd      = ('database user password',                      'option', 'p'),
    host      = ('database server host',                        'option', 's'),
    port      = ('database connection port number',             'option', 'o'),
    nocolor   = ('do not color-code the output',                'flag',   'x'),
    nokeyring = ('do not use a keyring',                        'flag',   'X'),
    args      = 'a string or regex to search for, or one or more LCSH identifiers',
)

def main(describe=False, find=False, trace=False, summarize=False,
         user=None, pswd=None, host=None, port=None,
         nocolor=False, nokeyring=False, *args):
    '''Query Dassie for information about an LCSH term.  The Dassie database
process must already be running.  The action to be performed must be
indicated by using one of the following two command line flags:

  -d    Describe the LCSH term(s) given on the command line
  -f    Search the label, alt_label and note fields for a string or regex
  -t    Trace the path from the given LCSH term(s) to root terms
  -m    Print some summary statistics about the database of LCSH terms

By default, this uses the operating system's keyring/keychain functionality
to get the user name, password, port number and host name needed to access
the Dassie database over the network.  If no such credentials are found, it
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

The -f option uses Python regular expression syntax.  An explanation of the
syntax can be found here: https://docs.python.org/3/howto/regex.html
Note that it is best to quote the string given to -f in order to avoid the
string being evaluated by your command shell interpreter.

The -x option (do not color the output) is useful when piping the output to
a pagination program like "more" or "less".

The commands that take identifiers (-d and -t) assume that the remaining
arguments on the command line are identifiers of terms in the Library of
Congress Subject Headings (LCSH).
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
        (user, pswd, host, port) = obtain_credentials(_KEYRING, "Dassie database",
                                                      user, pswd, host, port,
                                                      default_host=_DEFAULT_HOST,
                                                      default_port=_DEFAULT_PORT)
    if keyring:
        # Save the credentials if they're different from what's currently saved.
        (s_user, s_pswd, s_host, s_port) = get_credentials(_KEYRING)
        if s_user != user or s_pswd != pswd or s_host != host or s_port != port:
            save_credentials(_KEYRING, user, pswd, host, port)
    if not any([describe, find, trace, summarize]):
        raise SystemExit(colorcode('No action specified. (Use -h for help.)', 'warning'))
    if not find and (not summarize and not args):
        raise SystemExit(colorcode('Need LCSH identifiers. (Use -h for help.)', 'error'))

    # Do some simple sanity checks:
    if not find:
        for t in args:
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
            for t in args:
                trace_term(lcsh_terms, t, colorize)
        if find:
            find_terms(lcsh_terms, args[0], colorize)
        if describe:
            for t in args:
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
    msg(colorcode(entry['_id'], ['bold', 'reverse'], colorize))
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
    '''Print some statistics about the Dassie database.'''
    info = lcsh_info.find_one({})
    count = lcsh_terms.count()
    msg('Number of LCSH terms in database: {}'.format(humanize.intcomma(count)))
    msg('Date of issue of LCSH terms: {}'.format(info['lcsh_file_date']))
    msg('Source of LCSH terms: {}'.format(info['lcsh_source']))


def find_terms(lcsh_terms, text, colorize=False):
    expr = re.compile(text, re.IGNORECASE)
    entries = lcsh_terms.find({'$or': [{'label': expr},
                                       {'alt_label': expr},
                                       {'note': expr}]})
    if entries.count() > 0:
        msg('Found {} entries containing "{}" in label, alt_label, or notes'
            .format(entries.count(), text))
        stop_index = entries.count() - 1
        for index, entry in enumerate(entries):
            print_details(entry, colorize=colorize)
            if index < stop_index:
                msg('-'*70, 'dark', colorize)
    else:
        msg('Found no LCSH entries containing "{}".'.format(text))


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
# intended to store a password associated with an identifier (a user name),
# and this identifier is expected to be obtained some other way, such as by
# using the current user's computer login name.  This poses 2 problems for us:
#
#  1. The user may want to use a different user name for the remote service,
#  so we can't assume the user's computer login name is the same.  We also
#  don't want to ask for the remote user name every time we need the
#  information, because that can end up presenting a dialog to the user every
#  time, which quickly becomes unbearably annoying.  This means we can't use
#  a user-generated identifer to access the keyring value -- we have to
#  invent a value, and then store the user's name for the remote service as
#  part of the value we store.  (Here, we use the fake user name "credentials" to
#  access the value stored in the user's keyring for a given service.)
#
#  2. We need to store several pieces of information, not just a password,
#  but the Python keyring module interface (and presumably most system
#  keychains) does not allow anything but a string value.  The hackacious
#  solution taken here is to concatenate several values into a single string
#  used as the actual value stored.  The individual values are separated by a
#  character that is unlikely to be part of any user-typed value.

def get_credentials(service, user=None):
    '''Looks up the user's credentials for the given 'service' using the
    keyring/keychain facility on this computer.  If 'user' is None, this uses
    the fake user named "credentials".  The latter makes it possible to access a
    service with a different user login name than the user's current login
    name without having to ask the user for the alternative name every time.
    '''
    value = keyring.get_password(service, user if user else 'credentials')
    return _decode(value) if value else (None, None, None, None)


def save_credentials(service, user, pswd, host=None, port=None):
    '''Saves the user, password, host and port info for 'service'.'''
    user = user if user else ''
    pswd = pswd if pswd else ''
    host = host if host else ''
    port = port if port else ''
    keyring.set_password(service, 'credentials', _encode(user, pswd, host, port))


def obtain_credentials(service, display_name,
                       user=None, pswd=None, host=None, port=None,
                       default_host=None, default_port=None):
    '''As the user for credentials for 'service'.'''
    (s_user, s_pswd, s_host, s_port) = (None, None, None, None)
    if service:
        # If we're given a service, retrieve the stored (if any) for defaults.
        (s_user, s_pswd, s_host, s_port) = get_credentials(service)

    if host is not -1 and not host:
        host = s_host or input("{} host (default: {}): ".format(display_name,
                                                                default_host))
        host = host or default_host
    if port is not -1 and not port:
        port = s_port or input("{} port (default: {}): ".format(display_name,
                                                                default_port))
        port = port or default_port
    if not user:
        user = s_user or input("{} user name: ".format(display_name))
    if not pswd:
        pswd = s_pswd or getpass.getpass('{} password: '.format(display_name))

    return (user, pswd, host, port)


_sep = ''
'''Character used to separate multiple actual values stored as a single
encoded value string.  This character is deliberately chosen to be something
very unlikely to be part of a legitimate string value typed by user at a
shell prompt, because control-c is normally used to interrupt programs.
'''

def _encode(user, pswd, host, port):
    return '{}{}{}{}{}{}{}'.format(user, _sep, pswd, _sep, host, _sep, port)


def _decode(value_string):
    return tuple(value_string.split(_sep))


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
