#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 14:23:09 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import json
import datetime

from unittest.mock import patch, Mock
from unittest import TestCase

from pyEBIrest.auth import Auth
from pyEBIrest.client import Root, Team, User, Domain, Submission, Client

from .test_auth import generate_token


# get my path
dir_path = os.path.dirname(os.path.realpath(__file__))

# define data path
data_path = os.path.join(dir_path, "data")


class ClientTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyEBIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()

    def test_with_tocken_str(self):
        token = generate_token()
        client = Client(token)
        self.assertFalse(client.auth.is_expired())

    def test_expired_tocken(self):
        now = int(datetime.datetime.now().timestamp())

        token = generate_token(now=now-10000)
        client = Client(token)

        # do a generic request and get error
        self.assertRaisesRegex(
            RuntimeError,
            "Your token is expired",
            client.follow_link,
            "https://submission-dev.ebi.ac.uk/api/"
        )


class RootTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyEBIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        with open(os.path.join(data_path, "root.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        # get a root object
        self.root = Root(self.auth)

    def test_str(self):
        test = self.root.__str__()
        reference = "Biosample API root at %s" % (Root.api_root)

        self.assertEqual(reference, test)

    def read_userTeams(self):
        with open(os.path.join(data_path, "userTeams.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

    def test_get_user_teams(self):
        # initialize
        self.read_userTeams()

        # get user teams
        teams = self.root.get_user_teams()

        self.assertIsInstance(teams, list)
        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertIsInstance(team, Team)

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

    def test_get_user_submissions(self):
        with open(os.path.join(data_path, "userSubmissions.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        submissions = self.root.get_user_submissions()

        self.assertIsInstance(submissions, list)
        self.assertEqual(len(submissions), 2)

        for submission in submissions:
            self.assertIsInstance(submission, Submission)

        # testing filtering
        draft = self.root.get_user_submissions(status="Draft")

        self.assertIsInstance(draft, list)
        self.assertEqual(len(draft), 1)

        team1 = self.root.get_user_submissions(team="subs.dev-team-1")
        self.assertIsInstance(team1, list)
        self.assertEqual(len(team1), 1)

        completed1 = self.root.get_user_submissions(
            team="subs.dev-team-1", status="Completed")
        self.assertIsInstance(completed1, list)
        self.assertEqual(len(completed1), 0)


class UserTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyEBIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_post_patcher = patch('pyEBIrest.client.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_put_patcher = patch('pyEBIrest.client.requests.put')
        cls.mock_put = cls.mock_put_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.mock_post_patcher.stop()
        cls.mock_put_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())
        self.user = User(self.auth)

        self.data = {
            "userName": "foo",
            "email": "foo.bar@email.com",
            "userReference": "usr-f1801430-51e1-4718-8fca-778887087bad",
            "_links": {
                "self": {
                    "href" : "https://explore.api.aai.ebi.ac.uk/users/usr-f1801430-51e1-4718-8fca-778887087bad"
                }
            }
        }

    def test_get_my_id(self):
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = self.data
        self.mock_get.return_value.status_code = 200

        test = self.user.get_my_id()
        reference = "usr-f1801430-51e1-4718-8fca-778887087bad"

        self.assertEqual(reference, test)

    def test_user_has_nodata(self):
        self.assertRaisesRegex(
            NotImplementedError,
            "Not yet implemented",
            User,
            self.auth,
            self.data)

    def test_create_user(self):
        reference = "usr-2a28ca65-2c2f-41e7-9aa5-e829830c6c71"
        self.mock_post.return_value = Mock()
        self.mock_post.return_value.text = reference
        self.mock_post.return_value.status_code = 200

        test = self.user.create_user(
            user="newuser",
            password="changeme",
            confirmPwd="changeme",
            email="newuser@email.com",
            full_name="New User",
            organization="Test"
        )

        self.assertEqual(reference, test)

    def test_create_team(self):
        with open(os.path.join(data_path, "newTeam.json")) as handle:
            data = json.load(handle)

        self.mock_post.return_value = Mock()
        self.mock_post.return_value.json.return_value = data
        self.mock_post.return_value.status_code = 201

        team = self.user.create_team(
            description="test description",
            centreName="test Center")

        self.assertIsInstance(team, Team)

    def test_get_teams(self):
        with open(os.path.join(data_path, "userTeams.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        # get user teams
        teams = self.user.get_teams()

        self.assertIsInstance(teams, list)
        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertIsInstance(team, Team)

    def test_add_user2team(self):
        with open(os.path.join(data_path, "user2team.json")) as handle:
            data = json.load(handle)

        self.mock_put.return_value = Mock()
        self.mock_put.return_value.json.return_value = data
        self.mock_put.return_value.status_code = 200

        domain = self.user.add_user_to_team(
            user_id='dom-36ccaae5-1ce1-41f9-b65c-d349994e9c80',
            domain_id='usr-d8749acf-6a22-4438-accc-cc8d1877ba36')

        self.assertIsInstance(domain, Domain)

    def read_myDomain(self):
        with open(os.path.join(data_path, "myDomain.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

    def test_get_domains(self):
        # initialize
        self.read_myDomain()

        # get user teams
        domains = self.user.get_domains()

        self.assertIsInstance(domains, list)
        self.assertEqual(len(domains), 2)

        for domain in domains:
            self.assertIsInstance(domain, Domain)

    def test_get_domain_by_name(self):
        # initialize
        self.read_myDomain()

        # get a specific team
        domain = self.user.get_domain_by_name("subs.test-team-1")
        self.assertIsInstance(domain, Domain)

        # get a team I dont't belong to
        self.assertRaisesRegex(
            NameError,
            "domain: .* not found",
            self.user.get_domain_by_name,
            "subs.dev-team-2")
