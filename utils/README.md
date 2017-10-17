Scripts for recreating the LoCTerms database
============================================

Dependencies
------------

The implementation of `parse-lcsh-and-create-db` depends on Dave Beckett's [Redland librdf library](http://librdf.org/docs/python.html).  You will probably need to install it on your system.  If you are using MacPorts on macOS, the following will do it:

```csh
port install redland
port install redland-bindings +python27
```

(Note: if you omit the `+python27`, the second step above will lead to an error about "no variants selected".) At the time these notes were written, the version available from MacPorts was 1.0.16. 


Running the scripts
-------------------

The process is basically this:

1. Unzip the copy of `authoritiessubjects.nt.skos.gz` in the directory `../data`, or (if you are trying to use a new edition of the LCSH subject headings RDF file) download a copy from http://id.loc.gov/download/.
2. If there is no `authoritiessubjects.nt.skos` in the current directory, create a symbolic link to the file in `../data`:
   ```
   ln -s ../data/authoritiessubjects.nt.skos
   ```
3. Start MongoDB's `mongod` server process:
   ```
   ./start-empty-mongodb
   ```
   If this encounters any problems, it will report a failure. The problem must be corrected before going on.
4. Assuming that the file `authoritiessubjects.nt.skos` is in the current directory, execute the following command:
   ```
   ./parse-lcsh-and-create-db authoritiessubjects.nt.skos
   ```
   If the above runs successfully, you should see a long list of outputs that begin like this:
   ```
   Adding metadata
   Initial pass and database creation
   1000 triples
   *** skipping children's subject id sj96005973
   *** skipping children's subject id sj96005656
   ...
   ```
5. Once the process is finished, you can kill the database server because it is not needed anymore.  To do this, find the process identifier reported during step 3 and issue the following command:
   ```
   kill PID
   ```
   where `PID` is the process id of the `mongod` process as reported by `start-empty-mongodb`.

If all went well, there will be a database directory named `lcsh-db` in the current directory.  This can be used to replace the `lcsh-db` directory in the parent LoCTerms directory.  It can also be saved as a database dump, and used to replace the file `lcsh-dump.tgz` in `../data`.

