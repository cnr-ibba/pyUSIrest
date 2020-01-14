#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 11:53:11 2019

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import json
import datetime

from unittest.mock import patch, Mock
from unittest import TestCase

from pyUSIrest.auth import Auth
from pyUSIrest.client import Client
from pyUSIrest.settings import ROOT_URL
from pyUSIrest.exceptions import USIConnectionError, TokenExpiredError

from .common import DATA_PATH
from .test_auth import generate_token


class ClientTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()

    def test_with_tocken_str(self):
        token = generate_token()
        client = Client(token)
        self.assertFalse(client.auth.is_expired())

    def test_with_auth_object(self):
        token = generate_token()
        auth = Auth(token=token)
        client = Client(auth)
        self.assertFalse(client.auth.is_expired())

    def test_expired_tocken(self):
        now = int(datetime.datetime.now().timestamp())

        token = generate_token(now=now-10000)
        client = Client(token)

        # do a generic request and get error
        self.assertRaisesRegex(
            TokenExpiredError,
            "Your token is expired",
            client.get,
            "https://submission-test.ebi.ac.uk/api/"
        )

    def test_server_error(self):
        """Deal with the generic 50x states"""

        token = generate_token()
        client = Client(token)

        # create a mock response
        response = Mock()
        response.status_code = 500
        response.text = (
            '<!DOCTYPE html>\n<html>\n<body>\n<meta http-equiv="refresh" '
            'content=\'0;URL=http://www.ebi.ac.uk/errors/failure.html\'>\n'
            '</body>\n</html>\n')

        self.mock_get.return_value = response

        self.assertRaisesRegex(
            USIConnectionError,
            "Problems with API endpoints",
            client.get,
            ROOT_URL
        )

    def test_get(self):
        """Testing a get method"""

        # create a mock response
        with open(os.path.join(DATA_PATH, "root.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        token = generate_token()
        client = Client(token)

        response = client.get(ROOT_URL, headers={'new_key': 'new_value'})

        self.assertIsInstance(response.json(), dict)

    def test_get_with_errors(self):
        """Deal with problems with getting URL (no 200 status code)"""

        # create a mock response
        response = Mock()
        response.status_code = 404
        response.text = (
            '<h1>Not Found</h1><p>The requested resource was not found on '
            'this server.</p>')

        token = generate_token()
        client = Client(token)

        self.mock_get.return_value = response

        self.assertRaisesRegex(
            USIConnectionError,
            "Not Found",
            client.get,
            ROOT_URL + "/meow"
        )
