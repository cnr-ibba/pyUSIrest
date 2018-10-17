#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 11:54:50 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import datetime
import python_jwt

from unittest.mock import patch, Mock
from unittest import TestCase


from pyUSIrest.auth import Auth


def generate_token(now=None):
    """A function to generate a 'fake' token"""

    if not now:
        now = int(datetime.datetime.now().timestamp())

    claims = {
        'iss': 'https://explore.aai.ebi.ac.uk/sp',
        'iat': now,
        'exp': now+3600,
        'sub': 'usr-f1801430-51e1-4718-8fca-778887087bad',
        'email': 'foo.bar@email.com',
        'nickname': 'foo',
        'name': 'Foo Bar',
        'domains': ['subs.test-team-1']
    }

    return python_jwt.generate_jwt(
        claims,
        algorithm='RS256')


class TestAuth(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyUSIrest.auth.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()

    def setUp(self):
        # Configure the mock to return a response with an OK status code.
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token()
        self.mock_get.return_value.status_code = 200
        self.now = int(datetime.datetime.now().timestamp())

    def test_login(self):
        # Call the service, which will send a request to the server.
        auth = Auth(user='foo', password='bar')

        # If the request is sent successfully, then I expect a response to
        # be returned.
        self.assertIsInstance(auth.__str__(), str)
        self.assertFalse(auth.is_expired())

    def test_with_tocken(self):
        auth = Auth(token=generate_token())

        # If the request is sent successfully, then I expect a response to
        # be returned.
        self.assertIsInstance(auth.__str__(), str)
        self.assertFalse(auth.is_expired())

    def test_get_tocken(self):
        # Call the service, which will send a request to the server.
        auth = Auth(user='foo', password='bar')
        token = auth.token

        self.assertIsInstance(token, str)

    def test_invalid_status(self):
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token()
        self.mock_get.return_value.status_code = 400

        self.assertRaisesRegex(
            ConnectionError, "Got status", Auth, user='foo', password='bar')

    def test_expired(self):
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token(
            now=self.now-10000)
        self.mock_get.return_value.status_code = 200

        # Call the service, which will send a request to the server.
        auth = Auth(user='foo', password='bar')

        self.assertIsInstance(auth.__str__(), str)
        self.assertTrue(auth.is_expired())

    def test_no_parameters(self):
        self.assertRaisesRegex(
            ValueError,
            "You need to provide user/password or a valid token",
            Auth)

    def test_get_durations(self):
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = generate_token(
            now=self.now-3300)
        self.mock_get.return_value.status_code = 200

        # Call the service, which will send a request to the server.
        auth = Auth(user='foo', password='bar')

        # get duration
        duration = auth.get_duration()

        # get remaining seconds
        seconds = int(duration.total_seconds())

        self.assertAlmostEqual(seconds, 300, delta=10)
