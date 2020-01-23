#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 16:28:46 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import requests
import logging

from dateutil.parser import parse as parse_date

from . import __version__
from .auth import Auth
from .exceptions import USIConnectionError, USIDataError, TokenExpiredError

logger = logging.getLogger(__name__)


# https://stackoverflow.com/a/25341965/4385116
def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse_date(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


class Client():
    """A class to deal with EBI submission API. It perform request
    modelling user token in request headers. You need to call this class after
    instantiating an :py:class:`Auth <pyUSIrest.auth.Auth>` object::

        import getpass
        from pyUSIrest.auth import Auth
        from pyUSIrest.client import Client
        auth = Auth(user=<you_aap_user>, password=getpass.getpass())
        client = Client(auth)
        response = client.get("https://submission-test.ebi.ac.uk/api/")

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
            raise TokenExpiredError("Your token is expired")

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
            raise USIConnectionError(
                "Problems with API endpoints: %s" % response.text)

        if int(response.status_code / 100) == 4:
            raise USIDataError(
                "Error with request: %s" % response.text)

        # TODO: evaluate a list of expected status?
        if response.status_code != expected_status:
            raise USIConnectionError(
                "Got a status code different than expected: %s (%s)" % (
                    response.status_code, response.text))

    def get(self, url, headers={}, params={}):
        """Generic GET method

        Args:
            url (str): url to request
            headers (dict): custom headers for get request
            params (dict): custom params for get request

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

    def post(self, url, payload={}, headers={}, params={}):
        """Generic POST method

        Args:
            url (str): url to request
            payload (dict): data to send
            headers (dict): custom header for request
            params (dict): custom params for request

        Returns:
            requests.Response: a response object
        """

        logger.debug("Posting data to %s" % (url))
        headers = self.check_headers(headers)
        response = self.session.post(
            url, json=payload, headers=headers, params=params)

        # track last response
        self.last_response = response
        self.last_status_code = response.status_code

        # check response status code
        self.check_status(response, expected_status=201)

        return response

    def patch(self, url, payload={}, headers={}, params={}):
        """Generic PATCH method

        Args:
            url (str): url to request
            payload (dict): data to send
            headers (dict): custom header for request
            params (dict): custom params for request

        Returns:
            requests.Response: a response object
        """

        logger.debug("Patching data to %s" % (url))
        headers = self.check_headers(headers)
        response = self.session.patch(
            url, json=payload, headers=headers, params=params)

        # track last response
        self.last_response = response
        self.last_status_code = response.status_code

        # check response status code
        self.check_status(response)

        return response

    def delete(self, url, headers={}, params={}):
        """Generic DELETE method

        Args:
            url (str): url to request
            headers (dict): custom header for request
            params (dict): custom params for request

        Returns:
            requests.Response: a response object
        """

        logger.debug("Deleting %s" % (url))

        headers = self.check_headers(headers)
        response = self.session.delete(url, headers=headers, params=params)

        # track last response
        self.last_response = response
        self.last_status_code = response.status_code

        # check response status code
        self.check_status(response, expected_status=204)

        return response

    def put(self, url, payload={}, headers={}, params={}):
        """Generic PUT method

        Args:
            url (str): url to request
            payload (dict): data to send
            params (dict): custom params for request
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        logger.debug("Putting data to %s" % (url))
        headers = self.check_headers(headers)
        response = self.session.put(
            url, json=payload, headers=headers, params=params)

        # track last response
        self.last_response = response
        self.last_status_code = response.status_code

        # check response status code
        self.check_status(response)

        return response


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

    def get(self, url, force_keys=True):
        """Override the Client.get method and read data into object::

            document = Document(auth)
            document.get(settings.ROOT_URL + "/api/")

        Args:
            url (str): url to request
            force_keys (bool): If True, define a new class attribute from data
                keys

        Returns:
            requests.Response: a response object
        """

        # call the base method
        response = super().get(url)

        # read data
        self.read_data(response.json(), force_keys)

        # act like client object
        return response

    def read_data(self, data, force_keys=False):
        """Read data from a dictionary object and set class attributes

        Args:
            data (dict): a data dictionary object read with
                :py:meth:`response.json() <requests.Response.json>`
            force_keys (bool): If True, define a new class attribute from data
                keys
        """

        # dealing with this type of documents
        for key in data.keys():
            if "date" in key.lower() and is_date(data[key]):
                self.__update_key(key, parse_date(data[key]), force_keys)

            else:
                self.__update_key(key, data[key], force_keys)

        self.data = data

    def __update_key(self, key, value, force_keys=False):
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
            if force_keys is True:
                logger.debug("Forcing %s -> %s" % (key, value))
                setattr(self, key, value)

            else:
                logger.warning("key %s not implemented" % (key))

    @classmethod
    def clean_url(cls, url):
        """Remove stuff like ``{?projection}`` from url

        Args:
            url (str): a string url

        Returns:
            str: the cleaned url
        """

        # remove {?projection} from self url. This is unreachable
        if '{?projection}' in url:
            logger.debug("removing {?projection} from url")
            url = url.replace("{?projection}", "")

        return url

    @classmethod
    def read_url(cls, auth, url):
        """Read a url and returns a :py:class:`Document` object

        Args:
            auth (Auth): an Auth object to pass to result
            url (str): url to request

        Returns:
            Document: a document object
        """

        # clean url
        url = cls.clean_url(url)

        # create a new document
        document = cls(auth=auth)

        # get url and load data
        document.get(url)

        return document

    def paginate(self):
        """Follow all the pages. Return an iterator of document objects

        Args:
            response (requests.Response): a response object

        Yield:
            Document: a new Document instance
        """

        # return myself
        yield self

        # track the current document
        document = self

        while 'next' in document._links:
            url = document._links['next']['href']
            document = Document.read_url(self.auth, url)

            # return the last document
            yield document

    def follow_tag(self, tag, force_keys=True):
        """Pick a url from data attribute relying on tag, perform a request
        and returns a document object. For instance::

            document.follow_tag('userSubmissions')

        will return a document instance by requesting with
        :py:meth:`Client.get` using
        ``document._links['userSubmissions']['href']`` as url

        Args:
            tag (str): a key from USI response dictionary
            force_keys (bool): set a new class attribute if not present

        Returns:
            Document: a document object
        """

        logger.debug("Following %s url" % (tag))

        url = self._links[tag]['href']

        # create a new document
        document = Document(auth=self.auth)

        # read data
        document.get(url, force_keys)

        return document

    def follow_self_url(self):
        """Follow *self* url and update class attributes. For instance::

            document.follow_self_url()

        will reload document instance by requesting with
        :py:meth:`Client.get` using
        ``document.data['_links']['self']['href']`` as url"""

        logger.debug("Following self url")

        # get a url to follow
        url = self._links['self']['href']

        # clean url
        url = self.clean_url(url)

        logger.debug("Updating self")

        # now follow self url and load data to self
        self.get(url)
