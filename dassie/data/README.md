Dassie data subdirectory
========================

This directory contains the following:

* [lcsh-dump.tgz](lcsh-dump.tgz): A compressed MongoDB database dump of the Dassie database. This is used by the program [../dassie/dassie-server](../dassie/dassie-server) to restore the database during first-time setup.

* [authoritiessubjects.nt.skos.gz](authoritiessubjects.nt.skos.gz): A copy of the [Library of Congress Subject Headings](http://id.loc.gov/authorities/subjects.html) (LCSH) RDF file, obtained from the [downloads page of the Library of Congress Linked Data Service](http://id.loc.gov/download/) in mid-2017.  This file is included here in order to be able to reproduce exactly how the data in Dassie was created.  The utility programs in [../utils](../utils) make use of this.

According to the [terms of service](http://id.loc.gov/about/) of the Library of Congress Linked Data Service, the vocabulary is provided as a public domain data set.




