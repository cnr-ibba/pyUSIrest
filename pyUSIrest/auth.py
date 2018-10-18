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

    auth_url = "https://explore.api.aai.ebi.ac.uk/auth"

    def __init__(self, user=None, password=None, token=None):
        """
        Instantiate a python EBI AAP Object. You can generate a new object
        providing both user and password, or by passing a valid token
        string

        Args:
            user (str): your aap username
            password (str): your password
            token (str): a valid EBI AAP jwt token

        Returns:
            Auth instance
        """

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
                logger.error("Got status %s" % (self.status_code))
                raise ConnectionError(
                    "Got status %s: '%s'" % (
                        self.status_code, self.response.text))

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
        """Get/Set token as a string"""

        return self._token

    @token.setter
    def token(self, token):
        self._decode(token)
        self._token = token

    def get_duration(self):
        """Get token remaining time before expiration

        Returns:
            datetime.timedelta: remaining time as
            :py:class:`datetime.timedelta` object
        """
        now = datetime.datetime.now()
        duration = (self.expire - now)

        # debug
        if 0 < duration.total_seconds() < 300:
            logger.warning(
                "Token for {user} will expire in {seconds} seconds".format(
                    user=self.claims['name'],
                    seconds=duration.total_seconds()
                )
            )
        elif duration.total_seconds() < 0:
            logger.error(
                "Token for {user} is expired".format(
                    user=self.claims['name']
                )
            )
        else:
            logger.debug(
                "Token for {user} will expire in {seconds} seconds".format(
                    user=self.claims['name'],
                    seconds=duration.total_seconds()
                )
            )

        return duration

    def is_expired(self):
        """Return True if token is exipired, False otherwise"""

        return self.get_duration().days < 0

    def __str__(self):
        total_time = self.get_duration().total_seconds()

        if total_time < 0:
            return "Token for {user} is expired".format(
                user=self.claims['name'])
        else:
            return "Token for {user} will last {seconds} seconds".format(
                user=self.claims['name'],
                seconds=total_time)
