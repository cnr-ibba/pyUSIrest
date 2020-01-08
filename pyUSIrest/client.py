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
        """Check response status. See `HTTP status codes <https://submission.
        ebi.ac.uk/api/docs/ref_overview.html#_http_status_codes>`_

        Args:
            response (requests.Reponse): the reponse returned by requests
            method
        """

        # check with status code. deal with 50X statuses (internal error)
        if int(response.status_code / 100) == 5:
            raise ConnectionError(
                "Problems with API endpoints: %s" % response.text)

        # TODO: evaluate a list of expected status?
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

    def post(self, url, payload={}, params={}, headers={}):
        """Generic POST method

        Args:
            url (str): url to request
            payload (dict): data to send
            params (dict): custom params for request
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        logger.debug("Sending data to %s" % (url))
        headers = self.check_headers(headers)
        response = self.session.post(
            url, json=payload, headers=headers, params=params)

        # track last response
        self.last_response = response
        self.last_status_code = response.status_code

        # check response status code
        self.check_status(response, expected_status=201)

        return response

    def patch(self, url, payload={}, headers=None):
        """Generic PATCH method

        Args:
            url (str): url to request
            payload (dict): data to send
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.patch(url, json=payload, headers=headers)

    def delete(self, url, headers=None):
        """Generic DELETE method

        Args:
            url (str): url to request
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.delete(url, headers=headers)

    def put(self, url, payload={}, headers=None):
        """Generic PUT method

        Args:
            url (str): url to request
            payload (dict): data to send
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.put(url, json=payload, headers=headers)


class Document(Client):
    """Base class for pyUSIrest classes. It models common methods and
    attributes by calling :py:class:`Client` and reading json response from
    biosample API

    Attributes:
        _link (dict): ``_links`` data read from USI response
        _embeddedd (dict): ``_embedded`` data read from USI response
        page (dict): ``page`` data read from USI response
        name (str): name of this object
        data (dict): data from USI read with
            :py:meth:`response.json() <requests.Response.json>`

    """

    def __init__(self, auth=None, data=None):
        # if I get auth, setting appropriate method
        if auth:
            Client.__init__(self, auth)

        # my class attributes
        self._links = {}
        self._embedded = {}
        self.page = {}
        self.name = None
        self.data = {}

        # if I get data, read data into myself
        if data:
            self.read_data(data)

    def read_data(self, data, force=False):
        """Read data from a dictionary object and set class attributes

        Args:
            data (dict): a data dictionary object read with
                :py:meth:`response.json() <requests.Response.json>`
            force (bool): If True, define a new class attribute from data keys
        """

        # dealing with this type of documents
        for key in data.keys():
            self.__update_key(key, data[key], force)

        self.data = data

    def __update_key(self, key, value, force=False):
        """Helper function to update keys"""

        if hasattr(self, key):
            if getattr(self, key) and getattr(self, key) != '':
                # when I reload data, I do a substitution
                logger.debug("Found %s -> %s" % (key, getattr(self, key)))
                logger.debug("Updating %s -> %s" % (key, value))

            else:
                # don't have this attribute set
                logger.debug("Setting %s -> %s" % (key, value))

            setattr(self, key, value)

        else:
            if force is True:
                logger.info("Forcing %s -> %s" % (key, value))
                setattr(self, key, value)

            else:
                logger.warning("key %s not implemented" % (key))

    def parse_response(self, response):
        """Convert a response in a dict object. Returns an iterator

        Args:
            response (requests.Response): a response object

        Yield:
            dict: the output of
            :py:meth:`response.json() <requests.Response.json>`
        """

        data = response.json()

        logger.debug("Reading %s" % (data['_links']['self']['href']))

        yield data

        while 'next' in data['_links']:
            url = data['_links']['next']['href']
            response = self.get(url)
            data = response.json()

            logger.debug("Reading %s" % (data['_links']['self']['href']))

            yield data
