=======
History
=======

0.3.0.dev0
----------

TODO
^^^^

* document how to sort objects like submissions (consider iterators)
* filter by date?
* Model custom exceptions
* after completed, check available submission statuses

  * To check if a submission is submittable you can check the available statuses
    with this link: https://submission-test.ebi.ac.uk/api/submissions/<SUBMISSION_ID>/availableSubmissionStatuses
  * If the "Submitted" is available, then you can submit it.

* get a ``Team`` instance from ``Submission`` instance
* Set a default date for ``releaseDate`` (``str(datetime.now().date())`` could be
  ok)
* Filter a sample by status (ex. pending validation)

Features
^^^^^^^^

* fix bug when adding samples to a submission retrieved with ``team.get_submission``
* Update documentation. Set ``taxon`` in sample data (mandatory attribute)
* displaying dates when ``print(Submission)`` instances
* ``Root.get_user_submissions()`` and other methods which returned list of objects
  now return iterator objects
* str(auth) will report duration in ``hh:mm:ss``
* compiling PDF using PNG images (change badges)
* raise no exceptions where no team is found (using ``Root.get_user_teams``)
* Using namespaces to configure API endpoints (``pyUSIrest.settings``)

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
