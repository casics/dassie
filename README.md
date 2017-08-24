CASICS LoCTerms
===============

<img align="right" src=".graphics/casics-logo-small.png">

LoCTerms implements a MongoDB-based database of terms from the [Library of Congress Subject Headings](http://id.loc.gov/authorities/subjects.html) controlled vocabulary. Each term entry in the database has links to broader and narrower terms, enabling applications to use ordinary MongoDB network API calls to query the database for term relationships.

*Authors*:      [Michael Hucka](http://github.com/mhucka) and [Matthew J. Graham](https://github.com/doccosmos)<br>
*Repository*:   [https://github.com/casics/locterms](https://github.com/casics/locterms)<br>
*License*:      Unless otherwise noted, this content is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

☀ Introduction
-----------------------------

In CASISCS, we annotated repository entries with terms from the Library of Congress Subject Headings (LCSH).  We developed a simple hierarchical browser for the terms to allow search and navigation in the term hierarchy. To support this functionality, we converted a copy of the LCSH terms into this database format.

⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/casics/locterms/issues) for this repository.

♬ Contributing &mdash; info for developers
------------------------------------------

A lot remains to be done on CASICS in many areas.  We would be happy to receive your help and participation if you are interested.  Please feel free to contact the developers either via GitHub or the mailing list [casics-team@googlegroups.com](casics-team@googlegroups.com).

Everyone is asked to read and respect the [code of conduct](CONDUCT.md) when participating in this project.

❤️ Acknowledgments
------------------

Funding for this and other CASICS work has come from the [National Science Foundation](https://nsf.gov) via grant NSF EAGER #1533792 (Principal Investigator: Michael Hucka).
