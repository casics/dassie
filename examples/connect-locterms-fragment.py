#!/usr/bin/env python3.4

import sys
import os
from collections import defaultdict
from pymongo import MongoClient

# Fix up handling of utf8

# reload(sys)
# sys.setdefaultencoding('utf8')

# Connect to the database

db = MongoClient(tz_aware=True, connect=True)
lcsh_db = db['lcsh-db']
lcsh = lcsh_db.terms
