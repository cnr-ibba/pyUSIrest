#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 16:28:46 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import requests
import logging

from . import __version__
from .auth import Auth

logger = logging.getLogger(__name__)


class Client():
    """A class to deal with EBI submission API. It perform request
    modelling user token in request headers. You need to call this class after
    instantiating an :py:class:`Auth <pyUSIrest.auth.Auth>` object::

        import getpass
        from pyUSIrest.auth import Auth
        from pyUSIrest.client import Client
        auth = Auth(user=<you_aap_user>, password=getpass.getpass())
        client = Client(auth)
        response = client.request("https://submission-test.ebi.ac.uk/api/")

    Attributes:
        headers (dict): default headers for requests
        last_response (requests.Response): last response object read by this
            class
        last_satus_code (int): last status code read by this class
        session (request.Session): a session object
        auth (Auth): a pyUSIrest Auth object
    """

    headers = {
        'Accept': 'application/hal+json',
        'User-Agent': 'pyUSIrest %s' % (__version__)
    }

    def __init__(self, auth):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object

        """

        # my attributes
        self._auth = None
        self.last_response = None
        self.last_status_code = None
        self.session = requests.Session()

        # setting auth object
        self.auth = auth

    @property
    def auth(self):
        """Get/Set :py:class:`Auth <pyUSIrest.auth.Auth>` object"""

        return self._auth

    @auth.setter
    def auth(self, auth):
        logger.debug("Auth type is %s" % (type(auth)))

        # assign Auth object or create a new one
        if isinstance(auth, Auth):
            logger.debug("Assigning an Auth object")
            self._auth = auth

        else:
            logger.debug("Creating an Auth object")
            self._auth = Auth(token=auth)

        logger.debug("Updating headers with token")
        self.headers['Authorization'] = "Bearer {token}".format(
            token=self._auth.token)

    def check_headers(self, headers=None):
        """Checking headers and token

        Args:
            headers (dict): custom header for request

        Returns:
            headers (dict): an update headers tocken"""

        if self.auth.is_expired():
            raise RuntimeError("Your token is expired")

        if not headers:
            logger.debug("Using default headers")
            new_headers = self.headers

        else:
            new_headers = self.headers.copy()
            new_headers.update(headers)

        return new_headers

    def check_status(self, response, expected_status=200):
        """Check response status

        Args:
            response (requests.Reponse): the reponse returned by requests
            method
        """

        # check with status code. deal with 50X statuses (internal error)
        if int(response.status_code / 100) == 5:
            raise ConnectionError(
                "Problems with API endpoints: %s" % response.text)

        if response.status_code != expected_status:
            raise ConnectionError(response.text)

    def get(self, url, params={}, headers={}):
        """Generic GET method

        Args:
            url (str): url to request
            params (dict): custom params for get request
            headers (dict): custom headers for get request

        Returns:
            requests.Response: a response object
        """

        logger.debug("Getting %s" % (url))
        headers = self.check_headers(headers)
        response = self.session.get(url, headers=headers, params=params)

        # track last response
        self.last_response = response
        self.last_status_code = response.status_code

        # check response status code
        self.check_status(response)

        return response
