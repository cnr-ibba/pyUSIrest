=======
History
=======

TODO
----

* get a ``Team`` instance from ``Submission`` instance
* ``Submission.has_errors`` make two identical queries, on to determine the
  status and one to search errors, simplify it by doing only a query
* filtering sample by status or error make a lot of queries. Consider writing
  coroutines or reading ValidationResult as pages

0.3.1.dev0
----------

* fix a bug when patching a sample: deal with team in relationship
* Change ``Auth.__str__()``: now it returns ``Token for Foo Bar will expire in HH:MM:SS``
* add ``Auth.get_domains`` which returns ``self.claims['domains']``

0.3.0 (2020-01-14)
------------------

Features
^^^^^^^^

* modelled custom exceptions
* Set a default date if ``releaseDate`` attribute is missing
* improved documentation by describing how to sort and filter objects
* fix bug when adding samples to a submission retrieved with ``team.get_submission()``
* Update documentation. Set ``taxon`` in sample data (mandatory attribute)
* displaying dates when ``print(Submission)`` instances
* ``Root.get_user_submissions()`` and other methods which returned list of objects
  now return iterator objects
* ``str(auth)`` will report duration in ``hh:mm:ss``
* compiling PDF using PNG images (change badges)
* raise no exceptions where no team is found (using ``Root.get_user_teams``)
* Using namespaces to configure API endpoints (``pyUSIrest.settings``)
* move ``Root``, ``User``, ``Domain``, ``Team``, ``Submission``, ``Sample``
  ``ValidationResult`` classes inside ``pyUSIrest.usi`` module

0.2.2 (2019-03-28)
------------------

Features
^^^^^^^^

* Deal with API errors (50x, 40x)

0.2.1 (2019-01-15)
------------------

Features
^^^^^^^^

* test for an empty submission (no samples)
* updated `root.json`, `userSubmission.json` test data
* submissionStatus is no longer an attribute, when feching submission by name
  is present when getting user submissions
* follow submissionStatus link (if necessary)
* update submission status after create a new submission
* update submission status after ``get_submission_by_name``
* update submission status after reload a just finalized submission
* ``Domain.users`` returns ``User`` objects in a list
* improved ``Submission.get_samples`` method

0.2.0 (2018-10-23)
------------------

Features
^^^^^^^^

* Fetch submission by name
* changed library name to ``pyUSIrest``
* published to pypi
* Finalize submission with *PUT*

0.1.0 (2018-10-17)
------------------

Features
^^^^^^^^

* submit into biosample with python methods
