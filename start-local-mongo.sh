#!/bin/sh -x

dbpath=lcsh-db
logpath=mongodb.log

mongod --logpath=$logpath --dbpath=$dbpath --directoryperdb
