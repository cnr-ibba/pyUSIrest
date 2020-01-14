
==============
Advanced Usage
==============

The Python USI submission REST API could be used to manage multiple submissions
and samples in the same time. Most of its functions returns iterator objects, in
such way some time consiming tasks can be executed lazily and can be filtered and
sorted using the appropriate methods. Here there are described some useful tips
useful to manage user submission data

Retrieving Submission Objects
-----------------------------

You could retrieve all submission objects from :py:class:`Root <pyUSIrest.usi.Root>`
using :py:meth:`get_user_submissions <pyUSIrest.usi.Root.get_user_submissions>`: such
method returns an iterator object::

  from pyUSIrest.auth import Auth
  from pyUSIrest.usi import Root

  auth = Auth(user=<usi_username>, password=<usi_password>)
  root = Root(auth)

  for submission in root.get_user_submissions():
      print(submission)

:py:class:`Submission <pyUSIrest.usi.Submission>` objects could be also filtered
by status or by team name::

  for submission in root.get_user_submissions(status="Draft", team='subs.test-team-19'):
      print(submission)

Submission could be sorted using attributes, as described in `Sorting HOW TO <https://docs.python.org/3/howto/sorting.html>`_::

  from operator import attrgetter

  for submission in sorted(root.get_user_submissions(), key=attrgetter('lastModifiedDate'), reverse=True):
      print(submission)

In a similar way, submission could be filtered reling their attributes, for example
you can retrieve the recent modified submissions in a similar way::

  from datetime import datetime, timezone
  from dateutil.relativedelta import relativedelta

  recent_submission = lambda submission: submission.lastModifiedDate + relativedelta(months=+1) > datetime.now(timezone.utc)

  for submission in filter(recent_submission, root.get_user_submissions()):
      print(submission)

Submission could be derived also from :py:meth:`get_submissions <pyUSIrest.usi.Team.get_submissions>`
from a :py:class:`Team <pyUSIrest.usi.Team>` instance. In this case, the submission will
be filtered accordingly to the team, and can be filtered or sorted in the same
way as described before::

  team = root.get_team_by_name('subs.test-team-19')

  for submission in team.get_submissions():
      print(submission)

Working with samples
--------------------

The :py:meth:`get_samples <pyUSIrest.usi.Submission.get_samples>` method from
:py:class:`Submission <pyUSIrest.usi.Submission>` returns an iterator of
:py:class:`Sample <pyUSIrest.usi.Sample>` instances, and so can be filtered in
a similar way as :py:class:`Submission <pyUSIrest.usi.Submission>` instances::

  submission = root.get_submission_by_name('40549619-7797-4672-b703-93a72c3f984a')

  # get all samples in 'Pending' validation status
  for sample in submission.get_samples(status="Pending"):
      print(sample)

  # get all samples with errors in USI validation
  for sample in submission.get_samples(has_errors=True):
      print(sample)

  # returning samples with errors in other checks than Ena
  for sample in submission.get_samples(has_errors=True, ignorelist=['Ena'])
      print(sample)

You can also filter a :py:class:`Sample <pyUSIrest.usi.Sample>` by an attribute,
like you can do with :py:class:`Submission <pyUSIrest.usi.Submission>` objects,
for example you can retrieve a sample in a submission by title::

  for sample in filter(lambda sample: sample.title == 'SampleTitle', submission.get_samples()):
      print(sample)
