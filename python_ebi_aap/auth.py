#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 15:46:37 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>

.. module:: auth
   :platform: Unix,
   :synopsis: Deal with EBI AAP service

"""

import requests
import datetime

import python_jwt


class Auth():
    auth_url = "https://explore.api.aai.ebi.ac.uk/auth"

    def __init__(self, user=None, password=None, token=None):
        """Instantiate a python EBI AAP Object

        Kwargs:
            user (str): your aap username
            password (str): your password
            token (str): a valid EBI AAP jwt token

        Generate a new auth object

        """

        self.expire = None
        self.issued = None
        self.header = None
        self.claims = None
        self._token = None

        # get a response
        if password and user:
            self.response = requests.get(
                self.auth_url, auth=requests.auth.HTTPBasicAuth(
                    user, password))

            # Set token with token.setter
            self.token = self.response.text
            self.status_code = self.response.status_code

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

        # record useful values
        self.issued = datetime.datetime.fromtimestamp(self.claims['iat'])
        self.expire = datetime.datetime.fromtimestamp(self.claims['exp'])

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._decode(token)
        self._token = None

    def get_duration(self):
        now = datetime.datetime.now()
        return (self.expire - now)

    def is_expired(self):
        return self.get_duration().days > 0
