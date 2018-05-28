#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 15:46:37 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

"""

import requests
import datetime
import logging

import python_jwt


logger = logging.getLogger(__name__)


class Auth():
    """
    Instantiate a python EBI AAP Object

    Kwargs:
        user (str): your aap username
        password (str): your password
        token (str): a valid EBI AAP jwt token

    Generate a new auth object
    """

    auth_url = "https://explore.api.aai.ebi.ac.uk/auth"

    def __init__(self, user=None, password=None, token=None):
        self.expire = None
        self.issued = None
        self.header = None
        self.claims = None
        self._token = None

        # get a response
        if password and user:
            logger.debug("Authenticating user {user}".format(user=user))
            self.response = requests.get(
                self.auth_url, auth=requests.auth.HTTPBasicAuth(
                    user, password))

            # set status code
            self.status_code = self.response.status_code

            if self.status_code != 200:
                raise ConnectionError(self.response.text)

            logger.debug("Got status %s" % (self.status_code))

            # Set token with token.setter
            self.token = self.response.text

        elif token:
            # Set token with token.setter
            self.token = token

        else:
            raise ValueError(
                "You need to provide user/password or a valid token")

    def _decode(self, token=None):
        """Decode JWT token using python_jwt"""

        # process token
        self.header, self.claims = python_jwt.process_jwt(token)

        # debug
        logger.debug("Decoded tocken with %s" % (self.header['alg']))

        # record useful values
        self.issued = datetime.datetime.fromtimestamp(self.claims['iat'])
        self.expire = datetime.datetime.fromtimestamp(self.claims['exp'])

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._decode(token)
        self._token = token

    def get_duration(self):
        now = datetime.datetime.now()
        duration = (self.expire - now)

        # debug
        if duration.total_seconds() < 300:
            logger.warn("Your token will expire in {seconds} seconds".format(
                seconds=duration.total_seconds()))
        else:
            logger.info("Your token will expire in {seconds} seconds".format(
                seconds=duration.total_seconds()))

        return duration

    def is_expired(self):
        return self.get_duration().days < 0

    def __str__(self):
        if self.claims:
            return "token for {user} will last {seconds} seconds".format(
                user=self.claims['name'],
                seconds=self.get_duration().total_seconds())

        else:
            return "Not initialized token"
