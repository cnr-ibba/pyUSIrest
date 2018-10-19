==============================
Python USI submission REST API
==============================


.. image:: https://img.shields.io/pypi/v/pyUSIrest.svg
        :target: https://pypi.python.org/pypi/pyUSIrest

.. image:: https://img.shields.io/travis/cnr-ibba/pyUSIrest.svg
        :target: https://travis-ci.org/cnr-ibba/pyUSIrest

.. image:: https://readthedocs.org/projects/pyusirest/badge/?version=latest
        :target: https://pyusirest.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/cnr-ibba/pyUSIrest/badge.svg?branch=master
        :target: https://coveralls.io/github/cnr-ibba/pyUSIrest?branch=master



Python USI submission REST API contain all methods to interact with EMBL-EBI
Unified Submissions Interface

* Free software: GNU General Public License v3
* Documentation: https://pyusirest.readthedocs.io.


Features
--------

* Deal with EBI AAP_  (Authentication, Authorisation and Profile) service,
  generating tokens and dealing with User and Groups
* Interact with EBI USI (Unified Submission Interface) in order to submit data to
  biosample as described by this guide_. In details:

  * Getting `USI API root`_
  * Selecting a Team_
  * Creating a Submission_
  * Adding `items to Submission`_
  * Checking Biosample `Validation`_
  * Finalising_ a Submission

.. _AAP: https://explore.api.aai.ebi.ac.uk/docs/
.. _guide: https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html
.. _`USI API root`: https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html#_start_from_the_root
.. _Team: https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html#_pick_a_team
.. _Submission: https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html#_creating_a_submission
.. _`items to Submission`: https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html#_adding_documents_to_a_submission
.. _Validation: https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html#_validation
.. _Finalising: https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html#_finalising_your_submission

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
