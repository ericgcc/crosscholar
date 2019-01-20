===========
crosscholar
===========

Crosscholar is an application that collects scholarly data from Google Scholar and Crossref.

It's a command line scraper made with python that queries and parses Google Scholar's output crossing each record with crossref. This project is inspired by [PyScholar](https://github.com/dnlcrl/PyScholar), and until now, is able to scrap Google Scholar more than 10 hours in a row, without being banned.


* Free software: MIT License


Features
--------

* Gets a list of authors related to a query string.
* For each author, gets data like name and citations distributed in the time.
* Also for each author, extracts the data related to each work.
* When getting work's data, the program connects to crossref to verify the record and get the DOI number.
* Each work is retrieved with title, total citations, citations distribution, wos citations, publisher, authors,
  work type, volume, issue and page, when the information is available.

Todo
----
* Writting a command line tool.
* Improve code quality.

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

