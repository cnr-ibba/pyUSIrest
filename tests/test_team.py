#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 11:34:59 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import json
import types

from collections import defaultdict
from unittest.mock import patch, Mock
from unittest import TestCase

from pyUSIrest.auth import Auth
from pyUSIrest.usi import Team, User, Domain, Submission

from .common import DATA_PATH
from .test_auth import generate_token


class DomainTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_post_patcher = patch('requests.Session.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_post_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        # read domain data (a list of domains)
        with open(os.path.join(DATA_PATH, "myDomain.json")) as handle:
            data = json.load(handle)

        self.domain = Domain(self.auth, data=data[0])

    def test_str(self):
        test = self.domain.__str__()
        self.assertIsInstance(test, str)

    def test_create_profile(self):
        with open(os.path.join(DATA_PATH, "domainProfile.json")) as handle:
            data = json.load(handle)

        self.mock_post.return_value = Mock()
        self.mock_post.return_value.json.return_value = data
        self.mock_post.return_value.status_code = 201

        self.domain.domainReference = ("dom-b38d6175-61e8-4d40-98da-"
                                       "df9188d91c82")

        self.domain.create_profile(
            attributes={
                "cost_center": "ABC123",
                "address": "South Building, EMBL-EBI, Wellcome Genome Campus,"
                           "Hinxton, Cambridgeshire, CB10 1SD"
            })

    def read_myUsers(self):
        with open(os.path.join(DATA_PATH, "domainUsers.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

    def test_users(self):
        # initialize
        self.read_myUsers()

        # get my users
        users = self.domain.users

        self.assertIsInstance(users, list)
        self.assertEqual(len(users), 2)

        for user in users:
            self.assertIsInstance(user, User)


class TeamTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_post_patcher = patch('requests.Session.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_put_patcher = patch('requests.Session.put')
        cls.mock_put = cls.mock_put_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.mock_post_patcher.stop()
        cls.mock_put_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        with open(os.path.join(DATA_PATH, "team.json")) as handle:
            data = json.load(handle)

        self.team = Team(self.auth, data=data)

    def test_str(self):
        test = self.team.__str__()
        self.assertIsInstance(test, str)

    def mocked_create_submission(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "MockResponse not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        with open(os.path.join(DATA_PATH, "newSubmission.json")) as handle:
            data = json.load(handle)

        with open(os.path.join(DATA_PATH, "submissionStatus1.json")) as handle:
            status = json.load(handle)

        if args[0] == (
                "https://submission-test.ebi.ac.uk/api/teams/subs.test"
                "-team-1/submissions"):
            return MockResponse(data, 201)

        elif args[0] == (
                "https://submission-test.ebi.ac.uk/api/submissions/"
                "c8c86558-8d3a-4ac5-8638-7aa354291d61"):
            return MockResponse(data, 200)

        elif args[0] == (
                "https://submission-test.ebi.ac.uk/api/submissions/"
                "c8c86558-8d3a-4ac5-8638-7aa354291d61/submissionStatus"):
            return MockResponse(status, 200)

        return MockResponse(None, 404)

    @patch('requests.Session.get', side_effect=mocked_create_submission)
    @patch('requests.Session.post', side_effect=mocked_create_submission)
    def test_create_submission(self, mock_get, mock_post):
        submission = self.team.create_submission()
        self.assertIsInstance(submission, Submission)

    def mocked_get_submission(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "MockResponse not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        # this variable will collect all replies
        replies = defaultdict(lambda: MockResponse(None, 404))

        # a custom function to set up replies for link
        def set_reply(url, filename, status=200):
            # referring to the upper replies variable
            nonlocal replies

            # open data file
            with open(os.path.join(DATA_PATH, filename)) as handle:
                data = json.load(handle)

            # track reply to URL
            replies[url] = MockResponse(data, status)

        set_reply(
            "https://submission-test.ebi.ac.uk/api/submissions/search/"
            "by-team?teamName=subs.test-team-1",
            "teamSubmissions.json")

        # to reload status
        submission_prefix = "https://submission-test.ebi.ac.uk/api/submissions"
        status_suffix = "submissionStatus"

        status_link1 = "/".join([
            submission_prefix,
            "87e7abda-81a8-4b5e-a1c0-323f7f0a4e43",
            status_suffix])

        status_link2 = "/".join([
            submission_prefix,
            "8b05e7f2-92c1-4651-94cb-9101f351f000",
            status_suffix])

        set_reply(status_link1, "submissionStatus1.json")

        set_reply(status_link2, "submissionStatus2.json")

        return replies[args[0]]

    @patch('requests.Session.get', side_effect=mocked_get_submission)
    def test_get_submission(self, mock_get):
        submissions = self.team.get_submissions()

        # submissions is now a generator
        self.assertIsInstance(submissions, types.GeneratorType)

        # convert it into a list
        submissions = list(submissions)
        self.assertEqual(len(submissions), 2)

        # testing filtering
        draft = self.team.get_submissions(status="Draft")

        # submissions is now a generator
        self.assertIsInstance(draft, types.GeneratorType)

        # convert it into a list
        draft = list(draft)
        self.assertEqual(len(draft), 1)

        self.assertIsInstance(draft[0], Submission)
