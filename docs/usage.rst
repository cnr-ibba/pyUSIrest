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

In order to create a new USI user, with ``pyEBIrest`` API you need to have already
a valid registered user. First create an ``Auth`` object, then a ``User`` object::

  from pyEBIrest.auth import Auth
  from pyEBIrest.client import User
  auth = Auth(user=<usi_username>, password=<usi_password>)
  superuser = User(auth=auth)
  user = superuser.create_user(
      user=<new_usi_username>,
      password=<new_password>,
      confirmPwd=<new_password>,
      email=<your_email>,
      full_name=<your full name>,
      organization=<your_organization
  )
