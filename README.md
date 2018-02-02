Dassie<img align="right" title="Photo of a rock hyrax by Bjørn Christian Tørrissen. Obtained from Wikipedia. License: CC Attribution-Share Alike 3.0 Unported." src=".graphics/dassie.png">
======

Dassie implements a database of the subject term hierarchies found in the [Library of Congress Subject Headings](http://id.loc.gov/authorities/subjects.html) (LCSH).  Each entry in the database has links to broader (hypernym) and narrower (hyponym) terms.  Applications can use [MongoDB](https://docs.mongodb.com/ecosystem/drivers/) network API calls to query the database for terms and relationships.

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.4+-brightgreen.svg)](http://shields.io)
[![Latest version](https://img.shields.io/badge/Latest_version-1.0.0-green.svg)](http://shields.io)

*Authors*:      [Michael Hucka](http://github.com/mhucka) and [Matthew J. Graham](https://github.com/doccosmos)<br>
*Repository*:   [https://github.com/casics/dassie](https://github.com/casics/dassie)<br>
*License*:      Unless otherwise noted, this content is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

☀ Introduction
-----------------------------

Dassie was developed to solve a simple need: to provide a fast way to search and browse the terms in the [Library of Congress Subject Headings (LCSH)](http://id.loc.gov/authorities/subjects.html).  We converted the essential parts of the LCSH linked data graph into a database that makes explicit the ["is-a"](https://en.wikipedia.org/wiki/Hyponymy_and_hypernymy) relationships between LCSH terms.  The database we use is [MongoDB](https://mongodb.com).  The result, Dassie (a loose acronym for _"<b>da</b>tabase of <b>s</b>ubject term<b>s</b> and hierarch<b>ie</b>s"_), is a system that allows programs to use normal MongoDB network API calls to search for LCSH terms and their relationships.

Here is an example of using the `dassie` example program to describe the term `sh2008002926`:

```csh
# dassie -d sh2008002926
======================================================================
sh2008002926
         URL: http://id.loc.gov/authorities/subjects/sh2008002926.html
       label: Systems biology
  alt labels: (none)
    narrower: (none)
     broader: sh2003008355
     topmost: sh00007934, sh85118553
        note: (none)
======================================================================
```

We used Python 3 to implement `dassie` as an example, but the database served by Dassie does not depend on Python and you can use any [MongoDB API library](https://docs.mongodb.com/ecosystem/drivers/) to interact with Dassie once it is installed and running.

✺ Installing and configuring Dassie
----------------------------------

Here follow detailed instructions for getting Dassie running on a computer.

### ⓵&nbsp;&nbsp; _Download Dassie_
You can either download the release archive, or clone the repository directly:

```
git clone https://github.com/casics/dassie.git
```

### ⓶&nbsp;&nbsp; _Install software that Dassie depends upon_

Dassie needs the following software to run.  (On macOS, we use the [MacPorts](https://www.macports.org) packages [mongodb](https://www.macports.org/ports.php?by=name&substr=mongodb), [mongo-tools](https://www.macports.org/ports.php?by=name&substr=mongo-tools) and [py-pymongo](https://www.macports.org/ports.php?by=name&substr=py-pymongo) to install the dependencies.)

* [MongoDB](https://www.mongodb.com) version 3.4 or later
* (If using [MacPorts](https://www.macports.org) on macOS) [mongo-tools](https://www.macports.org/ports.php?by=name&substr=mongo-tools)
* [PyMongo](https://api.mongodb.com/python/current/) for Python 3 (to use the short Python programs provided here)

### ⓷&nbsp;&nbsp; _Configure the server process_

First, choose a user login and password that you want to use for network access to the database.  Next, start a terminal shell and cd into the [dassie](dassie) subdirectory and run the program `dassie-server` with the argument `start`:

```csh
cd dassie
./dassie-server start
```

The first time `dassie-server` is executed, it will (1) prompt you for the user name and password and configure the MongoDB database to allow only those credentials to read the database over the network, and (2) load the database contents from a compressed database dump.  This will take extra time but only needs to be done once.  The output should look something like the following:

```txt
No database found in 'lcsh-db'.
Will begin by setting up database.
Creating local database directory lcsh-db.
Moving old log file to '/Users/mhucka/repos/casics-dassie/dassie.log.old'
Please provide a user name: 
Please provide a password:
Please type the password again:
Please record the user name & password in a safe location.
Extracting database dump from 'data/lcsh-dump.tgz'.
Database process will be forked and run in the background.
Starting unconfigured database process.
about to fork child process, waiting until server is ready for connections.
forked process: 10606
child process started successfully, parent exiting
Loading dump into running database instance. Note: this step
 will take time and print a lot of messages. If it succeeds,
 it will print 'finished restoring lcsh-db.terms' near the end.

2017-09-21T10:38:07.332-0700    using write concern: w='1', j=false, fsync=false, wtimeout=0
2017-09-21T10:38:07.332-0700    the --db and --collection args should only be used when restoring from a BSON file. Other uses are deprecated and will not exist in the future; use --nsInclude instead
2017-09-21T10:38:07.333-0700    building a list of collections to restore from dump/lcsh dir
2017-09-21T10:38:07.333-0700    found collection lcsh-db.terms bson to restore to lcsh-db.terms
2017-09-21T10:38:07.333-0700    found collection metadata from lcsh-db.terms to restore to lcsh-db.terms
2017-09-21T10:38:07.333-0700    reading metadata for lcsh-db.terms from dump/lcsh/terms.metadata.json
2017-09-21T10:38:07.333-0700    creating collection lcsh-db.terms using options from metadata
2017-09-21T10:38:07.379-0700    restoring lcsh-db.terms from dump/lcsh/terms.bson
2017-09-21T10:38:10.326-0700    [#######################.]  lcsh-db.terms  94.2MB/95.5MB  (98.6%)
2017-09-21T10:38:10.366-0700    [########################]  lcsh-db.terms  95.5MB/95.5MB  (100.0%)
2017-09-21T10:38:10.366-0700    restoring indexes for collection lcsh-db.terms from metadata
2017-09-21T10:38:27.357-0700    finished restoring lcsh-db.terms (417763 documents)
2017-09-21T10:38:27.357-0700    done

Configuring user credentials in database.
Restarting database server process.
Killing process 10606.
database process will be forked and run in the background.
Starting normal database process.
about to fork child process, waiting until server is ready for connections.
forked process: 10714
child process started successfully, parent exiting
Cleaning up.
Dassie database process is running with PID 10714.
```

You can stop the database using the `stop` command, like this:

```csh
./dassie-server stop
```

You can also query for the status of the database process using the `status` command, like this:

```csh
./dassie-server status
```

There are other options for `dassie-server`.  You can use the `-h` option to display a helpful summary.

```csh
./dassie-server -h

```

Note that database server process is **not automatically restarted** after you reboot your computer.  You can set up your computer to restart the process automatically, but the procedure for doing so depends on your computer's operating system.

Finally, the database server (MongoDB) will be configured to listen on a default port, number 27017.  To change this, you can use the `-p` option when first configuring Dassie using `dassie-server`.  This port number will be saved to a configuration file in the current directory, so that when Dassie is restarted, it will automatically use the same port again.

▶︎ Basic operation
------------------

Dassie includes a program, `dassie-server` to load and run a MongoDB database containing the LCSH term data, and a command-line application, `dassie`, that can be used to explore the database interactively. The latter also serves as an example of how to write a Python client program that accesses the database over the network&mdash;the same could be implemented using any of the different [MongoDB drivers available](https://docs.mongodb.com/ecosystem/drivers/).

The basic operation is simple: cd into the `dassie` subdirectory, start the database process using `dassie-server start`, and then connect to the database to perform queries and obtain data.

The `dassie` command line interface (in the `bin` subdirectory) can perform four operations: print descriptive information about one or more LCSH terms, trace the "is-a" hierarchy upward from a given LCSH term until it reaches terms that have no hypernyms, search for terms whose labels or notes contain a given string or regular exprssion, and print some summary statistics about the database.

Here is an example of searching for terms using a regular expression.  The regular expression syntax used is [the one supported by Python's `re` module](https://docs.python.org/3/howto/regex.html):

```csh
# cd bin
# ./dassie -f 'biolog.*simulat.*'
======================================================================
Found 3 entries containing "biolog.*simulat.*" in label, alt_label, or notes
sh2009117081
         URL: http://id.loc.gov/authorities/subjects/sh2009117081.html
       label: Biological systems--Simulation methods--Congresses
  alt labels: (none)
    narrower: (none)
     broader: (none)
     topmost: (none)
        note: (none)
----------------------------------------------------------------------
sh2009117080
         URL: http://id.loc.gov/authorities/subjects/sh2009117080.html
       label: Biological systems--Computer simulation--Congresses
  alt labels: (none)
    narrower: (none)
     broader: (none)
     topmost: (none)
        note: (none)
----------------------------------------------------------------------
sh93000478
         URL: http://id.loc.gov/authorities/subjects/sh93000478.html
       label: Life (Biology)--Simulation games
  alt labels: (none)
    narrower: (none)
     broader: (none)
     topmost: (none)
        note: (none)
======================================================================
```

And here is an example of output from using `dassie` to trace the term graph from `sh85118400` upward until it reaches the top-most LCSH terms.  This shows that the hypernym links from `sh85118400` end in 4 terms (`sh85008810`, `sh2002007885`, `sh85010480`, and `sh99005029`) that have no further hypernyms, and there are 5 paths that lead there from `sh85118400`:

```csh
# ./dassie -t sh85118400
======================================================================
sh85008810: Associations, institutions, etc
└─ sh85048306: Financial institutions
   └─ sh94000179: Thrift institutions
      └─ sh85117760: Savings banks
         └─ sh85118400: School savings banks

sh85008810: Associations, institutions, etc
└─ sh85048306: Financial institutions
   └─ sh85011609: Banks and banking
      └─ sh85117760: Savings banks
         └─ sh85118400: School savings banks

sh2002007885: Finance
└─ sh85011609: Banks and banking
   └─ sh85117760: Savings banks
      └─ sh85118400: School savings banks

sh85010480: Auxiliary sciences of history
└─ sh85026423: Civilization
   └─ sh85124003: Social sciences
      └─ sh85040850: Economics
         └─ sh85048256: Finance
            └─ sh85011609: Banks and banking
               └─ sh85117760: Savings banks
                  └─ sh85118400: School savings banks

sh99005029: Civilization
└─ sh85124003: Social sciences
   └─ sh85040850: Economics
      └─ sh85048256: Finance
         └─ sh85011609: Banks and banking
            └─ sh85117760: Savings banks
               └─ sh85118400: School savings banks
```

To prevent security risks that would come from having unrestricted network access to the database, the database requires the use of a user name and password; these are set at the time of first creating installing and configuring Dassie database using `dassie-server` (described in the next section).  By default, `dassie` uses the operating system's keyring/keychain functionality to get the user name and password needed to access the Dassie database over the network so that you do not have to type them every time you call `dassie`.  If no such credentials are found, it will query the user interactively for the user name and password, and then store them in the keyring/keychain so that it does not have to ask again in the future.  It is also possible to supply a user name and password directly using the `-u` and `-p` options, respectively, but this is discouraged because it is insecure on multiuser computer systems. (Other users could run `ps` in the background and see your credentials.)

🗄 Database structure details
----------------------------

Each entry in the database (known as _documents_ in MongoDB parlance) is a structure with the following field-and-value pairs.  The value types are always either a string, a list of strings, an empty list, or the value `None`.

```javascript
{
  "_id": "string",
  "label": "string",
  "alt_labels": [ "string", "string", ...],
  "note": "string",
  "broader": [ "id", "id", ...],
  "narrower": [ "id", "id", ...],
  "topmost": [ "id", "id", ...]
}
```

A term in this database is indexed by its LCSH identifier; for example, `sh89003287`.  Identifiers in this scheme are strings that being with two letters followed by a series of integers.  The identifier is used as the value of the `_id` field.  (Note that in a slight deviation from common MongoDB practice, the `_id` field holds the identifier as a string, rather than an `ObjectId` object.  This makes using Dassie simpler.)

The meanings of the fields are as follows:

| Field        | Description | SKOS RDF component |
|--------------|-------------|-------------------|
| `_id`        | The term identifier | URI of the term in the LCSH Linked Data service |
| `label`      | The preferred descriptive label for the term | `http://www.w3.org/2004/02/skos/core#prefLabel` |
| `alt_labels` | One or more alternative descriptive labels | `http://www.w3.org/2004/02/skos/core#altLabel` |
| `note`       | Notes (from LCSH) about the term | `http://www.w3.org/2004/02/skos/core#note` |
| `broader`    | List of hypernyms of the term | `http://www.w3.org/2004/02/skos/core#broader` |
| `narrower`   | List of hyponyms of the term | `http://www.w3.org/2004/02/skos/core#narrower` |
| `topmost`    | List of topmost hyponyms of the term | (computed) |

The Library of Congress runs a [Linked Data Service](http://id.loc.gov/about/), and callers can look up more information about a term by dereferencing the URL `http://id.loc.gov/authorities/subjects/IDENTIFIER` where `IDENTIFIER` is the value of the `_id` in the Dassie database.  For instance, you can visit the page `http://id.loc.gov/authorities/subjects/sh89003287` in your web browser to find out more about `sh89003287`.

Most of the fields in a Dassie entry are taken directly from the LCSH database, except for the field `topmost`.  That field is computed by following hypernyms from a given entry until terms are reached that have no values for `broader`.  The `topmost` field holds a list of the unique topmost hypernyms computing this way.  (Note that there may be more than one path from a given term to a topmost term, and thus for a given number of topmost terms N, running `dassie -t` may show more than N paths.)

⚙️ Database connection details
----------------------------

To connect applications to the database server (for example, using [MongoClient](http://api.mongodb.com/python/current/api/pymongo/mongo_client.html) from [PyMongo](https://docs.mongodb.com/getting-started/python/client/)), you need to know (1) the user name, (2) password, (3) host running the MongoDB database server, (4) the number of the port on which the server is listening, (5) the name of the database (which is `lcsh-db`), and (6) the name of the collection within the database (which is `terms`).  Here is the form of the URI for use with MongoDB API libraries that accept connection strings in the [MongoDB URI](https://docs.mongodb.com/manual/reference/connection-string/) format:

```python
'mongodb://USER:PASSWORD@HOST:PORT/lcsh-db?authSource=admin'
```

where `USER` and `PASSWORD` are the values you used when first configuring the system using `dassie-server`, and `HOST` and `PORT` are the host and port number.  Once connected, access the database `lcsh-db` and collection `terms`.   Here is sample code in Python:

```python
db = MongoClient('mongodb://{}:{}@{}:{}/lcsh-db?authSource=admin'.format(user, password, host, port))
lcsh_terms = db['lcsh-db'].terms
```

After executing the code above, you would be able to issue commands such as `find_one` to search for terms.

```python
entry = lcsh_terms.find_one( {'_id': 'sh95000713'} )
```

⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/casics/dassie/issues) for this repository.

♬ Contributing: info for developers
-----------------------------------

Any constructive contributions &ndash; bug reports, pull requests (code or documentation), suggestions for improvements, and more &ndash; are welcome.  Please feel free to contact me directly, or even better, jump right in and use the standard GitHub approach of forking the repo and creating a pull request.

Everyone is asked to read and respect the [code of conduct](CONDUCT.md) when participating in this project.

❤️ Acknowledgments
------------------

Funding for this and other CASICS work has come from the [National Science Foundation](https://nsf.gov) via grant NSF EAGER #1533792 (Principal Investigator: Michael Hucka).

The photo of a dassie (a type of rock hyrax) at the top of this page came from [Wikipedia](https://commons.wikimedia.org/wiki/File:Procavia-capensis-Frontal.JPG). The author is Bjørn Christian Tørrissen, who made it available under the terms of the Creative Commons Attribution-Share Alike 3.0 Unported license.
