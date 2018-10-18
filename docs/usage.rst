=====
Usage
=====

To use Python USI submission REST API in a project::

  import pyUSIrest

Creating an Auth object
-----------------------

You can create a new ``Auth`` object using ``Auth`` class, providing you USI
username and password::

  from pyUSIrest.auth import Auth
  auth = Auth(user=<usi_username>, password=<usi_password>)

Alternatively you can create an ``Auth`` object starting from a token::

  auth = Auth(token=<token_string>)

Creating an USI user
--------------------

In order to create a new USI user, with ``pyUSIrest`` you can user ``User`` class::

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

To create a team, you will need to authenticate to USI biosample system. You could
provide the credentials already created::

  from pyUSIrest.auth import Auth
  from pyUSIrest.client import User
  auth = Auth(user=<usi_username>, password=<usi_password>)
  user = User(auth)
  team = user.create_team(description="Your description")

.. warning::

  remember to ri-generate to token in order to see the new generated team using pyUSIrest
  objects

Add proile to domain
++++++++++++++++++++

To create a profile for a team::

  domain = user.get_domain_by_name(<team name>)
  domain.create_profile()

Adding user to team
-------------------

To add a user to a team, you need to provide a ``user_id`` object, like the one
obtained by creating a user, or by calling ``get_my_id`` for a User instance::

  from pyUSIrest.auth import Auth
  from pyUSIrest.client import User
  auth = Auth(user=<usi_username>, password=<usi_password>)
  user = User(auth)
  user_id = user.get_my_id()

Next, you need to find out the domain reference of a team using a team name, for example::

  domain = user.get_domain_by_name(team.name)
  domain_id = domain.domainReference

To add user to a team call finally::

  user.add_user_to_team(user_id=user_id, domain_id=domain_id)

Create a submission
-------------------

Create a new ``Auth`` instance, then instantiate a new ``Root`` object and follow
links using class methods::

  from pyUSIrest.auth import Auth
  form pyUSIrest.client import Root
  auth = Auth(user=<usi_username>, password=<usi_password>)
  root = Root(auth=auth)
  team = root.get_team_by_name(<your team name>)
  submission = team.create_submission()

If you got a ``ConnectionError`` exception during last command, you need to add
a profile to your domain.

Add samples to a submission
+++++++++++++++++++++++++++

In order to add sample to a submission::

  animal_data = {'alias': 'animal_1',
    'title': 'ANIMAL:::ID:::WF60/B0811',
    'releaseDate': '2018-06-19',
    'taxonId': 9940,
    'attributes': {'material': [{'value': 'organism',
      'terms': [{'url': 'http://purl.obolibrary.org/obo/OBI_0100026'}]}],
    'project': [{'value': 'IMAGE'}]},
    'sampleRelationships': []}
  sample = submission.create_sample(animal_data)
  sample_data = {'alias': 'sample_1',
    'title': 'MA_052_KR_S_Snh_S03_Mariensee_WF001265_OMS_13.01.04',
    'releaseDate': '2018-06-19',
    'taxonId': 9940,
    'description': 'Qualitätsrate (Mot) 87,5 %',
    'attributes': {'material': [{'value': 'specimen from organism',
       'terms': [{'url': 'http://purl.obolibrary.org/obo/OBI_0001479'}]}],
     'project': [{'value': 'IMAGE'}]},
    'sampleRelationships': [{'alias': 'animal_1',
      'relationshipNature': 'derived from'}]}
  sample = submission.create_sample(sample_data)

Finalize a submission
+++++++++++++++++++++

After managing sample and validation statuses, if everything is ok you can finalize
your submission with::

  submission.finalize()
