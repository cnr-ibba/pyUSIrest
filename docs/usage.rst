=====
Usage
=====

To use Python USI submission REST API in a project, you should import
:py:class:`Root <pyUSIrest.client.Root>` and :py:class:`Auth <pyUSIrest.auth.Auth>`
in order to interact with USI_ endpoint ad EBI AAP_::

  from pyUSIrest.auth import Auth
  from pyUSIrest.client import Root

.. _USI: https://submission-test.ebi.ac.uk/api/browser/index.html#/api/
.. _AAP: https://explore.api.aai.ebi.ac.uk/docs/

Creating an Auth object
-----------------------

With an :py:class:`Auth <pyUSIrest.auth.Auth>` object, you're able to generate a
AAP_ token from EBI and use it in browsing USI_ endpoint. You can instantiate a
new :py:class:`Auth <pyUSIrest.auth.Auth>` providing your AAP_ username and password::

  auth = Auth(user=<usi_username>, password=<usi_password>)

Alternatively you can create an :py:class:`Auth <pyUSIrest.auth.Auth>` object
starting from a valid token::

  auth = Auth(token=<token_string>)

Creating an USI user
--------------------

In order to create a new USI user, with ``pyUSIrest`` you can use the method
:py:meth:`create_user <pyUSIrest.client.User.create_user>` of the
:py:class:`User <pyUSIrest.client.User>` class::

  from pyUSIrest.client import User

  user_id = User.create_user(
      user=<new_usi_username>,
      password=<new_password>,
      confirmPwd=<new_password>,
      email=<your_email>,
      full_name=<your full name>,
      organization=<your_organization
  )

Creating a team
---------------

To create a team, you will need to create a new :py:class:`User <pyUSIrest.client.User>`
from a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object, then you could create
a team using the :py:meth:`create_team <pyUSIrest.client.User.create_team>` method::

  from pyUSIrest.client import User
  user = User(auth)
  team = user.create_team(description="Your description")

.. warning::

  remember to ri-generate the token in order to see the new generated team using
  ``pyUSIrest`` objects

.. _add_profile_to_domain:

Add profile to domain
+++++++++++++++++++++

.. warning::

  You don't need to do this with a new generated user. You should use this method only
  if you experience problems when :ref:`creating a submission <create_a_submission>`.

To create a profile for a team::

  domain = user.get_domain_by_name(<team name>)
  domain.create_profile(attributes={"centre name": "My Institution"})

For more informations, take a look to `creating a domain profile`_

.. _`creating a domain profile`: https://explore.api.aai.ebi.ac.uk/docs/profile/index.html#resource-create_domain_profile

Adding user to team
-------------------

To add a user to a team, you need to provide a ``user_id``, like the one
obtained by creating a user, or by calling :py:meth:`get_my_id <pyUSIrest.client.User.get_my_id>`
from a :py:class:`User <pyUSIrest.client.User>` instance::

  user = User(auth)
  user_id = user.get_my_id()

Next, you need to find out the domain reference of a team using a team name and
:py:meth:`get_domain_by_name <pyUSIrest.client.User.get_domain_by_name>` method::

  domain = user.get_domain_by_name(team.name)
  domain_id = domain.domainReference

To add user to a team call :py:meth:`add_user_to_team <pyUSIrest.client.User.add_user_to_team>`::

  user.add_user_to_team(user_id=user_id, domain_id=domain_id)

.. _create_a_submission:

Create a submission
-------------------

From a valid :py:class:`Root <pyUSIrest.client.Root>` object, get the
:py:class:`Team <pyUSIrest.client.Team>` object providing the ``team_name`` in which the
submission will be created. Then create a new :py:class:`Submission <pyUSIrest.client.Submission>`
using the :py:meth:`create_submission <pyUSIrest.client.Team.create_submission>` method::

  team = root.get_team_by_name(<your team name>)
  submission = team.create_submission()

If you got a :py:exc:`ConnectionError` exception during last command, you need to add
a profile to your domain as described in :ref:`add profile to domain <add_profile_to_domain>`.

Add samples to a submission
+++++++++++++++++++++++++++

In order to add sample to a submission, define a :py:class:`dict` for sample data,
then add them using :py:meth:`create_sample <pyUSIrest.client.Submission.create_sample>`.
In the following example, a test animal and a sample from that animal are created::

  # define data as dictionaries. Ensure that mandatory keys
  # are provided or biosample will throw an error
  animal_data = {
    'alias': 'animal_1',
    'title': 'A Sample Organism',
    'releaseDate': '2018-06-19',
    'taxonId': 9940,
    'attributes': {'material': [{'value': 'organism',
      'terms': [{'url': 'http://purl.obolibrary.org/obo/OBI_0100026'}]}],
    'project': [{'value': 'A Sample Project'}]},
    'sampleRelationships': []}

  # add this animal to submission
  sample = submission.create_sample(animal_data)

  # Now generate a sample derived from the previous one.
  # This link is provided by sampleRelationships key
  sample_data = {'alias': 'sample_1',
    'title': 'A Sample Speciemen',
    'releaseDate': '2018-06-19',
    'taxonId': 9940,
    'description': 'A Useful Description',
    'attributes': {'material': [{'value': 'specimen from organism',
       'terms': [{'url': 'http://purl.obolibrary.org/obo/OBI_0001479'}]}],
     'project': [{'value': 'A Sample Project'}]},
    'sampleRelationships': [{'alias': 'animal_1',
      'relationshipNature': 'derived from'}]}

  # add this sample to the submission
  sample = submission.create_sample(sample_data)

Check and finalize a Submission
-------------------------------

Querying for biosample validation status
++++++++++++++++++++++++++++++++++++++++

After submitting all data, before finalize a submission, you need to ensure that
all the validation steps performed by USI_ are done with success. You can query
status with :py:meth:`get_status <pyUSIrest.client.Submission.get_status>`::

  status = submission.get_status()
  print(status)  # Counter({'Complete': 2})

status will be a :py:class:`collections.Counter` object. In order to finalize a
submission to biosample, :py:meth:`get_status <pyUSIrest.client.Submission.get_status>`
need to return only ``Complete`` as status (not ``Pending``), with a number equal
to the number of samples attached to submission

Checking errors
+++++++++++++++

Another method to check submission status before finalizing it is to check for errors
with :py:meth:`has_errors <pyUSIrest.client.Submission.has_errors>` method::

  errors = submission.has_errors()
  print(errors)  # Counter({False: 1, True: 1})

If there is any ``True`` in this :py:class:`collections.Counter` object,
submission has errors and can't be finalized. You will need to search
for sample with errors in order to remove or update it. Only when this function
return ``False`` with a number equal to the number of attached samples, a
submission can be finalized.

Finalize a submission
+++++++++++++++++++++

After managing sample and validation statuses, if everything is ok you can finalize
your submission with :py:meth:`finalize <pyUSIrest.client.Submission.finalize>`::

  submission.finalize()

After finalization, you can't add more data to this submission. You may want to
reload your data in order to retrieve the *biosample ids*, as described by
:ref:`get samples from a submission <get_samples_from_a_submission>`.

Fetch a submission by name
--------------------------

In order to get a submission by name, call :py:meth:`get_submission_by_name <pyUSIrest.client.Root.get_submission_by_name>`
from a valid :py:class:`Root <pyUSIrest.client.Root>` object::

  root = Root(auth=auth)
  submission = root.get_submission_by_name(
      'c3a7e663-3a37-48d3-a041-8c18088e3185')

.. _get_samples_from_a_submission:

Get samples from a submission
-----------------------------

In order to get all samples for a submission, you can call the method
:py:meth:`get_samples <pyUSIrest.client.Submission.get_samples>`
on a :py:class:`Submission <pyUSIrest.client.Submission>` object::

  samples = submission.get_samples()

You can also filter out samples by validationResult or if the have errors or not.
For a list of validationResult, check the output of :py:meth:`get_status <pyUSIrest.client.Submission.get_status>`::

  # fetching pending samples
  samples_pending = submission.get_samples(validationResult='Pending')

  # get samples with errors
  samples_error = submission.get_samples(has_errors=True)
