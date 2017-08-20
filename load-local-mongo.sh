#!/bin/sh

dbpath=lcsh-db
logpath=mongodb.log

echo "Extracting mongodb dump from data/lcsh-dump.tgz"
tar xzf data/lcsh-dump.tgz

echo "Creating local database directory"
mkdir lcsh-db

echo "Starting mongod"
./start-local-mongo.sh &

echo "Loading dump into running mongodb instance."
mongorestore -v --db $dbpath dump/lcsh

echo "Cleaning up."
/bin/rm -rf dump

echo "Done."
echo "Mongodb instance left running."
