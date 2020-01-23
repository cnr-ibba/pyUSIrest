#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 11:28:10 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import json
import types

from collections import defaultdict
from unittest.mock import patch, Mock
from unittest import TestCase

from pyUSIrest.auth import Auth
from pyUSIrest.usi import Root, Team, Submission
from pyUSIrest.settings import ROOT_URL
from pyUSIrest.exceptions import USIConnectionError, USIDataError

from .common import DATA_PATH
from .test_auth import generate_token


class RootTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        with open(os.path.join(DATA_PATH, "root.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        # get a root object
        self.root = Root(self.auth)

    def test_str(self):
        test = self.root.__str__()
        reference = "Biosample API root at %s" % (ROOT_URL + "/api/")

        self.assertIsInstance(test, str)
        self.assertEqual(reference, test)

    def read_userTeams(self, filename="userTeams.json"):
        with open(os.path.join(DATA_PATH, filename)) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

    def test_get_user_teams(self):
        # initialize
        self.read_userTeams()

        # get user teams
        teams = self.root.get_user_teams()

        # teams is now a generator
        self.assertIsInstance(teams, types.GeneratorType)
        teams = list(teams)

        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertIsInstance(team, Team)

    def test_get_user_no_teams(self):
        """Test for a user having no teams"""

        # initialize
        self.read_userTeams(filename="userNoTeams.json")

        # get user teams (is an empty iterator)
        teams = self.root.get_user_teams()

        self.assertRaises(StopIteration, next, teams)

    def test_get_team_by_name(self):
        # initialize
        self.read_userTeams()

        # get a specific team
        team = self.root.get_team_by_name("subs.dev-team-1")
        self.assertIsInstance(team, Team)

        # get a team I dont't belong to
        self.assertRaisesRegex(
            NameError,
            "team: .* not found",
            self.root.get_team_by_name,
            "subs.dev-team-2")

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

        # --- to test get_submission_by_name
        byname_link = "/".join([
            submission_prefix, "c8c86558-8d3a-4ac5-8638-7aa354291d61"])

        status_link3 = "/".join([
            submission_prefix,
            "c8c86558-8d3a-4ac5-8638-7aa354291d61",
            status_suffix])

        # --- for each url, return a different response
        set_reply(
            'https://submission-test.ebi.ac.uk/api/user/submissions',
            "userSubmissionsPage1.json")

        set_reply(
            'https://submission-test.ebi.ac.uk/api/user/submissions'
            '?page=1&size=1',
            "userSubmissionsPage2.json")

        set_reply(status_link1, "submissionStatus1.json")

        set_reply(status_link2, "submissionStatus2.json")

        set_reply(byname_link, "newSubmission.json")

        set_reply(byname_link, "newSubmission.json")

        set_reply(status_link3, "submissionStatus2.json")

        return replies[args[0]]

    @patch('requests.Session.get', side_effect=mocked_get_submission)
    def test_get_user_submissions(self, mock_get):
        # get userSubmissions
        submissions = self.root.get_user_submissions()

        # submissions is now a generator
        self.assertIsInstance(submissions, types.GeneratorType)

        # convert it into a list
        submissions = list(submissions)
        self.assertEqual(len(submissions), 2)

        for submission in submissions:
            self.assertIsInstance(submission, Submission)

        # testing filtering
        draft = self.root.get_user_submissions(status="Draft")

        # submissions is now a generator
        self.assertIsInstance(draft, types.GeneratorType)

        # convert it into a list
        draft = list(draft)
        self.assertEqual(len(draft), 1)

        team1 = self.root.get_user_submissions(team="subs.test-team-1")

        # submissions is now a generator
        self.assertIsInstance(team1, types.GeneratorType)

        # convert it into a list
        team1 = list(team1)
        self.assertEqual(len(team1), 1)

        completed1 = self.root.get_user_submissions(
            team="subs.dev-team-1", status="Completed")

        # submissions is now a generator
        self.assertIsInstance(completed1, types.GeneratorType)

        # convert it into a list
        completed1 = list(completed1)
        self.assertEqual(len(completed1), 0)

    @patch('requests.Session.get', side_effect=mocked_get_submission)
    def test_get_submission_by_name(self, mock_get):
        submission = self.root.get_submission_by_name(
            submission_name='c8c86558-8d3a-4ac5-8638-7aa354291d61')

        self.assertIsInstance(submission, Submission)

    def test_get_submission_not_found(self):
        """Test get a submission with a wrong name"""

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = ''
        self.mock_get.return_value.status_code = 404

        self.assertRaisesRegex(
            NameError,
            "submission: .* not found",
            self.root.get_submission_by_name,
            submission_name='c8c86558-8d3a-4ac5-8638-7aa354291d61')

        # a different 40x error type
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.text = (
            "The request did not include an Authorization header")
        self.mock_get.return_value.status_code = 401

        self.assertRaisesRegex(
            USIDataError,
            "Error with request",
            self.root.get_submission_by_name,
            submission_name='c8c86558-8d3a-4ac5-8638-7aa354291d61')

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.status_code = 500

        self.assertRaises(
            USIConnectionError,
            self.root.get_submission_by_name,
            submission_name='c8c86558-8d3a-4ac5-8638-7aa354291d61')
