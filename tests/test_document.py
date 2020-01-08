#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 14:56:39 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import json
import types

from unittest.mock import patch, Mock
from unittest import TestCase

from pyUSIrest.auth import Auth
from pyUSIrest.client import Document

from .common import DATA_PATH
from .test_auth import generate_token


class DocumentTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

        # define an auth object
        token = generate_token()
        cls.auth = Auth(token=token)

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()

    def test_create_document(self):
        # create a mock response
        with open(os.path.join(DATA_PATH, "root.json")) as handle:
            data = json.load(handle)

        # get a document instance
        document = Document(auth=self.auth, data=data)

        self.assertIsInstance(document, Document)

    def test_paginate(self):
        with open(os.path.join(
                DATA_PATH, "userSubmissionsPage1.json")) as handle:
            page1 = json.load(handle)

        with open(os.path.join(
                DATA_PATH, "userSubmissionsPage2.json")) as handle:
            page2 = json.load(handle)

        self.mock_get.return_value = Mock()

        # simulating two distinct replies with side_effect
        self.mock_get.return_value.json.side_effect = [page1, page2]
        self.mock_get.return_value.status_code = 200

        # getting a document instance
        document = Document(auth=self.auth)

        # getting a documehnt
        document.get("https://submission-test.ebi.ac.uk/api/user/submissions")

        # ok parsing the response
        responses = document.paginate()

        # assering instances
        self.assertIsInstance(responses, types.GeneratorType)

        # reading objects and asserting lengths
        test = list(responses)

        self.assertEqual(len(test), 2)
