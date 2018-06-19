=====
Usage
=====

To use Python EBI submission REST API in a project::

  import pyEBIrest

Creating an Auth object
-----------------------

You can create a new ``Auth`` object using ``Auth`` class, providing you USI
username and password::

  from pyEBIrest.auth import Auth
  auth = Auth(user=<usi_username>, password=<usi_password>)

Alternatively you can create an ``Auth`` object starting from a token::

  auth = Auth(token=<token_string>)

Creating an USI user
--------------------

In order to create a new USI user, with ``pyEBIrest`` you can user ``User`` class::

  from pyEBIrest.client import User

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

  from pyEBIrest.auth import Auth
  from pyEBIrest.client import User
  auth = Auth(user=<usi_username>, password=<usi_password>)
  user = User(auth)
  team = user.create_team(description="Your description")

.. warning::

  remember to ri-generate to token in order to see the new generated team using pyEBIrest
  objects

Adding user to team
-------------------

To add a user to a team, you need to provide a ``user_id`` object, like the one
obtained by creating a user, or by calling ``get_my_id`` for a User instance::

  from pyEBIrest.auth import Auth
  from pyEBIrest.client import User
  auth = Auth(user=<usi_username>, password=<usi_password>)
  user = User(auth)
  user_id = user.get_my_id()

Next, you need to find out the domain reference of a team using a team name, for example::

  domain = user.get_domain_by_name(team.name)
  domain_id = domain_id = domain.domainReference

To add user to a team call finally::

  user.add_user_to_team(user_id=user_id, domain_id=domain_id)
