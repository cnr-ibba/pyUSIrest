=======
History
=======

0.2.1-dev
---------

TODO
^^^^

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
