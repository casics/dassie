Dassie<img align="right" title="Photo of a rock hyrax by Bjørn Christian Tørrissen. Obtained from Wikipedia. License: CC Attribution-Share Alike 3.0 Unported." src=".graphics/dassie.png">
======

Dassie implements a database of the subject term hierarchies found in the [Library of Congress Subject Headings](http://id.loc.gov/authorities/subjects.html) (LCSH).  Each entry in the database has links to broader (hypernym) and narrower (hyponym) terms.  Applications can use [MongoDB](https://docs.mongodb.com/ecosystem/drivers/) network API calls to query the database for terms and relationships.

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.4+-brightgreen.svg)](http://shields.io)
[![Latest version](https://img.shields.io/badge/Latest_version-1.0.2-green.svg)](http://shields.io)

*Authors*:      [Michael Hucka](http://github.com/mhucka) and [Matthew J. Graham](https://github.com/doccosmos)<br>
*Repository*:   [https://github.com/casics/dassie](https://github.com/casics/dassie)<br>
*License*:      Unless otherwise noted, this content is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

Table of Contents
-----------------

  * [Recent news and activities](#-recent-news-and-activities)
  * [Introduction](#-introduction)
  * [Installing and configuring Dassie](#-installing-and-configuring-dassie)
     * [Download Dassie](#-download-dassie)
     * [Install software that Dassie depends upon](#-install-software-that-dassie-depends-upon)
     * [Configure the server process](#-configure-the-server-process)
  * [Basic operation](#︎-basic-operation)
  * [Database structure details](#-database-structure-details)
  * [Database connection details](#️-database-connection-details)
  * [Getting help and support](#-getting-help-and-support)
  * [Contributing: info for developers](#-contributing-info-for-developers)
  * [Acknowledgments](#️-acknowledgments)

🏁 Recent news and activities
------------------------------

Please see the file [NEWS.md](NEWS.md) for a summary of the changes in the most recent release.

☀ Introduction
-----------------------------

Dassie was developed to solve a simple need: to provide a fast way to search and browse the terms in the [Library of Congress Subject Headings (LCSH)](http://id.loc.gov/authorities/subjects.html).  We converted the essential parts of the LCSH linked data graph into a database that makes explicit the ["is-a"](https://en.wikipedia.org/wiki/Hyponymy_and_hypernymy) relationships between LCSH terms.  The database we use is [MongoDB](https://mongodb.com).  The result, Dassie (a loose acronym for _"<b>da</b>tabase of <b>s</b>ubject term<b>s</b> and hierarch<b>ie</b>s"_), is a system that allows programs to use normal MongoDB network API calls to search for LCSH terms and their relationships.

Here's an example of using the `dassie` example program to trace paths from term `sh2008002926` to the top-most terms:

```csh
# dassie -t sh2008002926
======================================================================
sh85118553: Science
└─ sh85076841: Life sciences
   └─ sh85014203: Biology
      └─ sh2003008355: Computational biology
         └─ sh2008002926: Systems biology

sh00007934: Science
└─ sh85076841: Life sciences
   └─ sh85014203: Biology
      └─ sh2003008355: Computational biology
         └─ sh2008002926: Systems biology
======================================================================
```

We used Python 3 to implement `dassie` as an example, but the database served by Dassie does not depend on Python and you can use any [MongoDB API library](https://docs.mongodb.com/ecosystem/drivers/) to interact with Dassie once it is installed and running.

✺ Installing and configuring Dassie
----------------------------------

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

First, choose a user login and password that you want to use for network access to the database.  Next, start a terminal shell and run the program `dassie-server` (found in the [dassie](dassie) subdirectory) with the argument `start`:

```csh
dassie-server start
```

The first time `dassie-server` is executed, it will (1) prompt you for the user name and password and configure the MongoDB database to allow only those credentials to read the database over the network, and (2) load the database contents from a compressed database dump.  This will take extra time but only needs to be done once.  The output should look something like the following:

```txt
No database found in '/Users/mhucka/repos/dassie-git/dassie/lcsh-db'.
Will begin by setting up database.
Creating local database directory /Users/mhucka/repos/dassie-git/dassie/lcsh-db.
Moving old log file to '/Users/mhucka/repos/dassie-git/dassie/dassie.log.old'
Please indicate the port to use (hit return for default 27017):
Using default port number 27017.
Please provide a user name: 
Please provide a password:
Please type the password again:
Please record the user name & password in a safe location.
Extracting database dump from '/Users/mhucka/repos/dassie-git/dassie/data/lcsh-dump.tgz'.
Database process will be forked and run in the background.
Starting unconfigured database process.
about to fork child process, waiting until server is ready for connections.
forked process: 59911
child process started successfully, parent exiting
Loading dump into running database instance. Note: this step
 will take time and print a lot of messages. If it succeeds,
 it will print 'finished restoring /Users/mhucka/repos/dassie-git/dassie/lcsh-db.terms' near the end.

2018-02-03T09:18:08.938-0800    using write concern: w='1', j=false, fsync=false, wtimeout=0
2018-02-03T09:18:08.939-0800    the --db and --collection args should only be used when restoring from a BSON file. Other uses are deprecated and will not exist in the future; use --nsInclude instead
2018-02-03T09:18:08.939-0800    building a list of collections to restore from dump/lcsh dir
2018-02-03T09:18:08.939-0800    found collection lcsh-db.info bson to restore to lcsh-db.info
2018-02-03T09:18:08.939-0800    found collection metadata from lcsh-db.info to restore to lcsh-db.info
2018-02-03T09:18:08.939-0800    found collection lcsh-db.terms bson to restore to lcsh-db.terms
2018-02-03T09:18:08.939-0800    found collection metadata from lcsh-db.terms to restore to lcsh-db.terms
2018-02-03T09:18:08.939-0800    reading metadata for lcsh-db.info from dump/lcsh/info.metadata.json
2018-02-03T09:18:08.939-0800    reading metadata for lcsh-db.terms from dump/lcsh/terms.metadata.json
2018-02-03T09:18:08.940-0800    creating collection lcsh-db.info using options from metadata
2018-02-03T09:18:08.940-0800    creating collection lcsh-db.terms using options from metadata
2018-02-03T09:18:09.003-0800    restoring lcsh-db.info from dump/lcsh/info.bson
2018-02-03T09:18:09.057-0800    no indexes to restore
2018-02-03T09:18:09.057-0800    finished restoring lcsh-db.info (1 document)
2018-02-03T09:18:09.057-0800    restoring lcsh-db.terms from dump/lcsh/terms.bson
2018-02-03T09:18:11.931-0800    [##################......]  lcsh-db.terms  72.0MB/95.5MB  (75.4%)
2018-02-03T09:18:12.920-0800    [########################]  lcsh-db.terms  95.5MB/95.5MB  (100.0%)
2018-02-03T09:18:12.920-0800    restoring indexes for collection lcsh-db.terms from metadata
2018-02-03T09:18:30.156-0800    finished restoring lcsh-db.terms (417763 documents)
2018-02-03T09:18:30.156-0800    done
Saving info to '/Users/mhucka/repos/dassie-git/dassie/lcsh-db/dassie.conf'.

Configuring user credentials in database.
Restarting database server process.
Killing process 59911.
Database process will be forked and run in the background.
Starting normal database process.
about to fork child process, waiting until server is ready for connections.
forked process: 59978
child process started successfully, parent exiting
Cleaning up.
Dassie database process is running with PID 59978.
Using config file /Users/mhucka/repos/dassie-git/dassie/lcsh-db/dassie.conf.
Using port 27017.
```

You can stop the database using the `stop` command, like this:

```csh
dassie-server stop
```

You can also query for the status of the database process using the `status` command, like this:

```csh
dassie-server status
```

There are other options for `dassie-server`.  You can use the `-h` option to display a helpful summary.

```csh
dassie-server -h

```

Note that database server process is **not automatically restarted** after you reboot your computer.  You can set up your computer to restart the process automatically, but the procedure for doing so depends on your computer's operating system.

Finally, the database server (MongoDB) will be configured to listen on a default port, number 27017.  This can be changed during the initial setup process; `dassie-server` will ask for the port number and save it in a configuration file, so that when Dassie is restarted it will automatically use the same port again.

▶︎ Basic operation
------------------

Dassie includes a program, `dassie-server` to load and run a MongoDB database containing the LCSH term data, and a command-line application, `dassie`, that can be used to explore the database interactively. The latter also serves as an example of how to write a Python client program that accesses the database over the network&mdash;the same could be implemented using any of the different [MongoDB drivers available](https://docs.mongodb.com/ecosystem/drivers/).

The basic operation is simple: cd into the `dassie` subdirectory, start the database process using `dassie-server start`, and then connect to the database to perform queries and obtain data.

The `dassie` command line interface (in the `bin` subdirectory) can perform four operations: print descriptive information about one or more LCSH terms, trace the "is-a" hierarchy upward from a given LCSH term until it reaches terms that have no hypernyms, search for terms whose labels or notes contain a given string or regular expression, and print some summary statistics about the database.

Here is an example of using `dassie` describe the term `sh2008002926`:

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

Here is an example of searching for terms using a regular expression.  The regular expression syntax used is [the one supported by Python's `re` module](https://docs.python.org/3/howto/regex.html):

```csh
# bin/dassie -f 'biolog.*simulat.*'
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
# bin/dassie -t sh85118400
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

To prevent security risks that would come from having unrestricted network access to the database, the database requires the use of a user name and password; these are set at the time of first creating installing and configuring Dassie database using `dassie-server` (described in the next section).  By default, `dassie` uses the operating system's keyring/keychain functionality to get the user name and password needed to access the Dassie database over the network so that you do not have to type them every time you call `dassie`.  If no such credentials are found, it will query the user interactively for the user name and password, and then store them in the keyring/keychain so that it does not have to ask again in the future.  It is also possible to supply a user name and password directly using the `-u` and `-p` options to `dassie`, respectively, but this is discouraged because it is insecure on multiuser computer systems. (Other users could run `ps` in the background and see your credentials.)

🗄 Database structure details
----------------------------

The LCSH database in Dassie was generated by beginning with the LCSH linked data file [authoritiessubjects.nt.skos](http://id.loc.gov/static/data/authoritiessubjects.nt.skos.zip), then processing the RDF triples to extract the `broader` and `narrower` relationships between terms while simultaneously skipping all the children's subject identifiers (i.e., terms whose names begin with `sj`), and finally storing the results in a MongoDB database.  Each entry in the resulting database is a structure with the following field-and-value pairs.  The value types are always either a string, a list of strings, an empty list, or the value `None`.

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

The procedure used to create the database contents from the [authoritiessubjects.nt.skos](http://id.loc.gov/static/data/authoritiessubjects.nt.skos.zip) file is encoded in the Python program [parse-lcsh-and-create-db](utils/parse-lcsh-and-create-db), included in the [utils](utils) subdirectory of the Dassie source code repository.

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

This material is based upon work supported by the [National Science Foundation](https://nsf.gov) under Grant Number 1533792 (Principal Investigator: Michael Hucka).  Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.

The photo of a dassie (a type of rock hyrax) at the top of this page came from [Wikipedia](https://commons.wikimedia.org/wiki/File:Procavia-capensis-Frontal.JPG). The author is Bjørn Christian Tørrissen, who made it available under the terms of the Creative Commons Attribution-Share Alike 3.0 Unported license.
    
<br>
<div align="center">
  <a href="https://www.nsf.gov">
    <img width="105" height="105" src=".graphics/NSF.svg">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src=".graphics/caltech-round.svg">
  </a>
</div>
