2016-07-01 <mhucka@caltech.edu>

How to start a local copy of the mongo db for LCSH terms.

1. Make sure to have a recent version of mongo 3.x.  I use the installation
   from MacPorts but any similar installation should work.

2. Run the script ./load-local-mongo.sh.  It should start up mongod, untar a
   dump of our LCSH database, and load it into the mongod process.  If all
   goes well, you should see output similar to this:

    > ./load-local-mongo.sh
    Extracting mongodb dump from data/lcsh-dump.tgz
    Starting mongod
    Loading dump into running mongodb instance.
    + dbpath=lcsh-db
    + logpath=mongodb.log
    + '[' '!' -d lcsh-db ']'
    + mkdir lcsh-db
    + mongod --logpath=mongodb.log --dbpath=lcsh-db --directoryperdb
    2016-07-01T09:15:07.276-0700 I CONTROL  [main] log file "/Users/mhucka/projects/casics/repos/casics/src/casics/lcsh/mongodb.log" exists; moved to "/Users/mhucka/projects/casics/repos/casics/src/casics/lcsh/mongodb.log.2016-07-01T16-15-07".
    2016-07-01T09:15:08.588-0700    using write concern: w='1', j=false, fsync=false, wtimeout=0
    2016-07-01T09:15:08.589-0700    building a list of collections to restore from dump/lcsh dir
    2016-07-01T09:15:08.590-0700    found collection lcsh-db.terms bson to restore
    2016-07-01T09:15:08.590-0700    found collection lcsh-db.terms metadata to restore
    2016-07-01T09:15:08.590-0700    reading metadata for lcsh-db.terms from dump/lcsh/terms.metadata.json
    2016-07-01T09:15:08.591-0700    creating collection lcsh-db.terms using options from metadata
    2016-07-01T09:15:08.621-0700    restoring lcsh-db.terms from dump/lcsh/terms.bson
    2016-07-01T09:15:11.593-0700    [#########...............]  lcsh-db.terms  37.5 MB/91.4 MB  (41.0%)
    2016-07-01T09:15:14.592-0700    [####################....]  lcsh-db.terms  77.2 MB/91.4 MB  (84.4%)
    2016-07-01T09:15:15.761-0700    [########################]  lcsh-db.terms  91.4 MB/91.4 MB  (100.0%)
    2016-07-01T09:15:15.761-0700    restoring indexes for collection lcsh-db.terms from metadata
    2016-07-01T09:15:33.101-0700    finished restoring lcsh-db.terms (414717 documents)
    2016-07-01T09:15:33.101-0700    done
    Done.
    Mongodb instance left running.


After this, you only need to restart mongod itself, and not re-run
load-local-mongo.sh.  To do that, run the script ./start-local-mongo.sh.
