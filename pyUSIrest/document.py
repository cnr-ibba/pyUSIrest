#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 11:14:44 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import logging

from .client import Client

logger = logging.getLogger(__name__)


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
