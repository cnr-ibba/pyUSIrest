#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 11:31:25 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""

import os
import json
import types

from unittest.mock import patch, Mock
from unittest import TestCase

from pyUSIrest.auth import Auth
from pyUSIrest.usi import Team, User, Domain

from .common import DATA_PATH
from .test_auth import generate_token


class UserTest(TestCase):
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
        self.user = User(self.auth)

        self.data = {
            "userName": "foo",
            "email": "foo.bar@email.com",
            "userReference": "usr-f1801430-51e1-4718-8fca-778887087bad",
            "_links": {
                "self": {
                    "href": "https://explore.api.aai.ebi.ac.uk/users/usr-"
                             "f1801430-51e1-4718-8fca-778887087bad"
                }
            }
        }

    def test_get_user_by_id(self):
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = self.data
        self.mock_get.return_value.status_code = 200

        user = self.user.get_user_by_id(
            "usr-f1801430-51e1-4718-8fca-778887087bad")

        self.assertIsInstance(user, User)

    def test_get_my_id(self):
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = self.data
        self.mock_get.return_value.status_code = 200

        test = self.user.get_my_id()
        reference = "usr-f1801430-51e1-4718-8fca-778887087bad"

        self.assertEqual(reference, test)

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
            organisation="Test"
        )

        self.assertEqual(reference, test)

    def test_create_team(self):
        with open(os.path.join(DATA_PATH, "newTeam.json")) as handle:
            data = json.load(handle)

        self.mock_post.return_value = Mock()
        self.mock_post.return_value.json.return_value = data
        self.mock_post.return_value.status_code = 201

        team = self.user.create_team(
            description="test description",
            centreName="test Center")

        self.assertIsInstance(team, Team)

    def read_teams(self):
        with open(os.path.join(DATA_PATH, "userTeams.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

    def test_get_teams(self):
        # initialize
        self.read_teams()

        # get user teams
        teams = self.user.get_teams()

        # teams is now a generator
        self.assertIsInstance(teams, types.GeneratorType)
        teams = list(teams)

        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertIsInstance(team, Team)

    def test_get_team_by_name(self):
        # initialize
        self.read_teams()

        # get a specific team
        team = self.user.get_team_by_name("subs.dev-team-1")
        self.assertIsInstance(team, Team)

        # get a team I dont't belong to
        self.assertRaisesRegex(
            NameError,
            "team: .* not found",
            self.user.get_team_by_name,
            "subs.dev-team-2")

    def test_add_user2team(self):
        with open(os.path.join(DATA_PATH, "user2team.json")) as handle:
            data = json.load(handle)

        self.mock_put.return_value = Mock()
        self.mock_put.return_value.json.return_value = data
        self.mock_put.return_value.status_code = 200

        domain = self.user.add_user_to_team(
            user_id='dom-36ccaae5-1ce1-41f9-b65c-d349994e9c80',
            domain_id='usr-d8749acf-6a22-4438-accc-cc8d1877ba36')

        self.assertIsInstance(domain, Domain)

    def read_myDomain(self):
        with open(os.path.join(DATA_PATH, "myDomain.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

    def test_get_domains(self):
        # initialize
        self.read_myDomain()

        # get user teams
        domains = self.user.get_domains()

        # domains is now a generator
        self.assertIsInstance(domains, types.GeneratorType)
        domains = list(domains)

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
