LoCTerms
========

<img align="right" src=".graphics/casics-logo-small.png">

LoCTerms implements a database of terms from the [Library of Congress Subject Headings](http://id.loc.gov/authorities/subjects.html) (LCSH) controlled vocabulary. Each term entry in the database has links to broader (hypernym) and narrower (hyponym) terms.  Applications can use [MongoDB](https://docs.mongodb.com/ecosystem/drivers/) network API calls to query the database for term relationships.

*Authors*:      [Michael Hucka](http://github.com/mhucka) and [Matthew J. Graham](https://github.com/doccosmos)<br>
*Repository*:   [https://github.com/casics/locterms](https://github.com/casics/locterms)<br>
*License*:      Unless otherwise noted, this content is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

☀ Introduction
-----------------------------

In [CASISCS](https://github.com/casics), we annotate GitHub repository entries with terms from the [Library of Congress Subject Headings (LCSH)](http://id.loc.gov/authorities/subjects.html).  To do this, we developed a simple hierarchical browser for LCSH terms to allow search and navigation in the term hierarchy. To support this functionality, we converted a copy of the LCSH terms into a database that makes explicit the ["is-a"](https://en.wikipedia.org/wiki/Hyponymy_and_hypernymy) relationships between LCSH terms.  The database we use is [MongoDB](https://mongodb.com).  The result, LoCTerms (short for "Library of Congress Terms"), is a system that allows programs to make normal MongoDB network API calls from any programming language.

▶︎ Basic operation
------------------

LoCTerms includes a program, `locterms-server` to load and run a MongoDB database containing the LCSH term data, and a command-line application, `query-locterms`, that can be used to explore the database interactively. The latter also serves as an example of how to write a Python client program that accesses the database over the network&mdash;the same could be implemented using any of the different [MongoDB drivers available](https://docs.mongodb.com/ecosystem/drivers/).

The basic operation is simple: start the database process using `locterms-server start`, and then connect to the database to perform queries and obtain data.  The operation of `locterms-server` is described in the next section below.

`query-locterms` can perform two operations: print descriptive information about one or more LCSH terms, and trace the "is-a" hierarchy upward from a given LCSH term until it reaches terms that have no hypernyms.  The following is an example of doing the first operation; this shows the output of using `query-locterms` to describe the term `sh85118400`:

```csh
> ./query-locterms -d sh85118400
======================================================================
sh85118400:
         URL: http://id.loc.gov/authorities/subjects/sh85118400.html
       label: School savings banks
  alt labels: (none)
    narrower:
     broader: sh85117760
     topmost: sh99005029, sh85010480, sh2002007885, sh85008810
        note: (none)
======================================================================
```

And here is an example of output from using `query-locterms` to trace the term graph from `sh85118400` upward until it reaches the top-most LCSH terms.  This shows that the hypernym links from `sh85118400` end in 4 terms (`sh85008810`, `sh2002007885`, `sh85010480`, and `sh99005029`) that have no further hypernyms, and there are 5 paths that lead there from `sh85118400`:

```csh
> ./query-locterms -t sh85118400
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

To prevent security risks that would come from having unrestricted network access to the database, the database requires the use of a user name and password; these are set at the time of first creating installing and configuring LoCTerms database using `locterms-server` (described in the next section).  By default, `query-locterms` uses the operating system's keyring/keychain functionality to get the user name and password needed to access the LoCTerms database over the network so that you do not have to type them every time you call `query-locterms`.  If no such credentials are found, it will query the user interactively for the user name and password, and then store them in the keyring/keychain so that it does not have to ask again in the future.  It is also possible to supply a user name and password directly using the `-u` and `-p` options, respectively, but this is discouraged because it is insecure on multiuser computer systems. (Other users could run `ps` in the background and see your credentials).

☛ Installation and configuration
--------------------------------

Before using LoCTerms, you will need to install the following software that LoCTerms depends upon:

* [MongoDB](https://www.mongodb.com) version 3.4 or later
* (If using [MacPorts](https://www.macports.org) on macOS) [mongo-tools](https://www.macports.org/ports.php?by=name&substr=mongo-tools)
* [PyMongo](https://api.mongodb.com/python/current/) for Python 3 (to use the short Python programs provided here)

On macOS, we use the [MacPorts](https://www.macports.org) packages [mongodb](https://www.macports.org/ports.php?by=name&substr=mongodb), [mongo-tools](https://www.macports.org/ports.php?by=name&substr=mongo-tools) and [py-pymongo](https://www.macports.org/ports.php?by=name&substr=py-pymongo) to install the dependencies above.  We use Python to implement the short programs in this repository, but the database served by LoCTerms is not dependent on Python and you can use any [MongoDB API library](https://docs.mongodb.com/ecosystem/drivers/) to interact with it once it is installed and running.

The next step after installing the dependencies above is to start a shell terminal in the directory where you installed LoCTerms.  First, choose a user login and password that you want to use for network access to the database.  Next, in a terminal shell with the LoCTerms directory as the current working directory, execute the program `locterms-server` with the argument `start`:

```csh
./locterms-server start
```

The first time `locterms-server` is executed, it will (1) prompt you for the user name and password and configure the MongoDB database to allow only those credentials to read the database over the network, and (2) load the database contents from a database dump.  This will take extra time but only needs to be done once.  The output should look something like the following:

```txt
No database found in 'lcsh-db'.
Will begin by setting up database.
Creating local database directory lcsh-db.
Moving old log file to '/Users/mhucka/repos/casics-locterms/locterms.log.old'
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
LoCTerms database process is running with PID 10714.
```

This procedure will leave the database running on your computer, so that you can immediately try `query-locterms` to experiment with the system.

You can stop the database using the `stop` command, like this:

```csh
./locterms-server stop
```

You can also query for the status of the database process using the `status` command, like this:

```csh
./locterms-server status
```

There are other options for `locterms-server`.  You can use the `-h` option to display a helpful summary.

```csh
./locterms-server -h
```

Note that database process is not automatically restarted after you reboot your computer.  You can set up your computer to restart the process automatically, but the procedure for doing so depends on your computer's operating system.


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/casics/locterms/issues) for this repository.

♬ Contributing: info for developers
-----------------------------------

A lot remains to be done on CASICS in many areas.  We would be happy to receive your help and participation if you are interested.  Please feel free to contact the developers either via GitHub or the mailing list [casics-team@googlegroups.com](casics-team@googlegroups.com).

Everyone is asked to read and respect the [code of conduct](CONDUCT.md) when participating in this project.

❤️ Acknowledgments
------------------

Funding for this and other CASICS work has come from the [National Science Foundation](https://nsf.gov) via grant NSF EAGER #1533792 (Principal Investigator: Michael Hucka).
