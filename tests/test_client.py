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

from pyUSIrest.auth import Auth
from pyUSIrest.client import (
    Root, Team, User, Domain, Submission, Client, Sample, Document)

from .test_auth import generate_token


# get my path
dir_path = os.path.dirname(os.path.realpath(__file__))

# define data path
data_path = os.path.join(dir_path, "data")


class ClientTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyUSIrest.client.requests.get')
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
            client.follow_url,
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

        self.assertRaisesRegex(
            ConnectionError,
            "Problems with API endpoints",
            client.parse_response,
            response
        )

    def test_follow_url_with_errors(self):
        """Deal with problems with following URL (no 200 status code)"""

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
            ConnectionError,
            "Not Found",
            client.follow_url,
            Root.api_root + "/meow"
        )


class RootTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyUSIrest.client.requests.get')
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

        self.assertIsInstance(test, str)
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

    def mocked_get_submission(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "MockResponse not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        with open(os.path.join(data_path, "userSubmissions.json")) as handle:
            submissions = json.load(handle)

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

        with open(os.path.join(data_path, "submissionStatus1.json")) as handle:
            status_data1 = json.load(handle)

        with open(os.path.join(data_path, "submissionStatus2.json")) as handle:
            status_data2 = json.load(handle)

        # --- to test get_submission_by_name
        byname_link = "/".join([
            submission_prefix, "c8c86558-8d3a-4ac5-8638-7aa354291d61"])

        with open(os.path.join(data_path, "newSubmission.json")) as handle:
            new_submission = json.load(handle)

        status_link3 = "/".join([
            submission_prefix,
            "c8c86558-8d3a-4ac5-8638-7aa354291d61",
            status_suffix])

        # --- for each url, return a different response
        if args[0] == (
                'https://submission-test.ebi.ac.uk/api/user/submissions'):
            return MockResponse(submissions, 200)

        elif args[0] == status_link1:
            return MockResponse(status_data1, 200)

        elif args[0] == status_link2:
            return MockResponse(status_data2, 200)

        # --- links for get_submission_by_name
        elif args[0] == byname_link:
            return MockResponse(new_submission, 200)

        elif args[0] == status_link3:
            return MockResponse(status_data2, 200)

        return MockResponse(None, 404)

    @patch('requests.get', side_effect=mocked_get_submission)
    def test_get_user_submissions(self, mock_get):
        # get userSubmissions
        submissions = self.root.get_user_submissions()

        self.assertIsInstance(submissions, list)
        self.assertEqual(len(submissions), 2)

        for submission in submissions:
            self.assertIsInstance(submission, Submission)

        # testing filtering
        draft = self.root.get_user_submissions(status="Draft")

        self.assertIsInstance(draft, list)
        self.assertEqual(len(draft), 1)

        team1 = self.root.get_user_submissions(team="subs.test-team-1")
        self.assertIsInstance(team1, list)
        self.assertEqual(len(team1), 1)

        completed1 = self.root.get_user_submissions(
            team="subs.dev-team-1", status="Completed")
        self.assertIsInstance(completed1, list)
        self.assertEqual(len(completed1), 0)

    def test_get_user_submission_pagination(self):
        """Testing get user submission with pagination"""

        with open(os.path.join(
                data_path, "userSubmissionsPage1.json")) as handle:
            page1 = json.load(handle)

        with open(os.path.join(
                data_path, "userSubmissionsPage2.json")) as handle:
            page2 = json.load(handle)

        self.mock_get.return_value = Mock()

        # simulating two distinct replies with side_effect
        self.mock_get.return_value.json.side_effect = [page1, page2]
        self.mock_get.return_value.status_code = 200

        submissions = self.root.get_user_submissions()

        self.assertIsInstance(submissions, list)
        self.assertEqual(len(submissions), 2)

    @patch('requests.get', side_effect=mocked_get_submission)
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

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.status_code = 500

        self.assertRaises(
            ConnectionError,
            self.root.get_submission_by_name,
            submission_name='c8c86558-8d3a-4ac5-8638-7aa354291d61')


class UserTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyUSIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_post_patcher = patch('pyUSIrest.client.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_put_patcher = patch('pyUSIrest.client.requests.put')
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
        with open(os.path.join(data_path, "newTeam.json")) as handle:
            data = json.load(handle)

        self.mock_post.return_value = Mock()
        self.mock_post.return_value.json.return_value = data
        self.mock_post.return_value.status_code = 201

        team = self.user.create_team(
            description="test description",
            centreName="test Center")

        self.assertIsInstance(team, Team)

    def read_teams(self):
        with open(os.path.join(data_path, "userTeams.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

    def test_get_teams(self):
        # initialize
        self.read_teams()

        # get user teams
        teams = self.user.get_teams()

        self.assertIsInstance(teams, list)
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


class DomainTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_post_patcher = patch('pyUSIrest.client.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_get_patcher = patch('pyUSIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_post_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        # read domain data (a list of domains)
        with open(os.path.join(data_path, "myDomain.json")) as handle:
            data = json.load(handle)

        self.domain = Domain(self.auth, data=data[0])

    def test_str(self):
        test = self.domain.__str__()
        self.assertIsInstance(test, str)

    def test_create_profile(self):
        with open(os.path.join(data_path, "domainProfile.json")) as handle:
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
        with open(os.path.join(data_path, "domainUsers.json")) as handle:
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
        cls.mock_get_patcher = patch('pyUSIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_post_patcher = patch('pyUSIrest.client.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_put_patcher = patch('pyUSIrest.client.requests.put')
        cls.mock_put = cls.mock_put_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.mock_post_patcher.stop()
        cls.mock_put_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        with open(os.path.join(data_path, "team.json")) as handle:
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

        with open(os.path.join(data_path, "newSubmission.json")) as handle:
            data = json.load(handle)

        with open(os.path.join(data_path, "submissionStatus1.json")) as handle:
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

    @patch('requests.get', side_effect=mocked_create_submission)
    @patch('requests.post', side_effect=mocked_create_submission)
    def test_create_submission(self, mock_get, mock_post):
        submission = self.team.create_submission()
        self.assertIsInstance(submission, Submission)

    def test_get_submission(self):
        with open(os.path.join(data_path, "teamSubmissions.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        submissions = self.team.get_submissions()

        self.assertIsInstance(submissions, list)
        self.assertEqual(len(submissions), 2)

        # testing filtering
        draft = self.team.get_submissions(status="Draft")

        self.assertIsInstance(draft, list)
        self.assertEqual(len(draft), 1)
        self.assertIsInstance(draft[0], Submission)


class SubmissionTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyUSIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_post_patcher = patch('pyUSIrest.client.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_put_patcher = patch('pyUSIrest.client.requests.put')
        cls.mock_put = cls.mock_put_patcher.start()

        cls.mock_patch_patcher = patch('pyUSIrest.client.requests.patch')
        cls.mock_patch = cls.mock_patch_patcher.start()

        cls.mock_delete_patcher = patch('pyUSIrest.client.requests.delete')
        cls.mock_delete = cls.mock_delete_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.mock_post_patcher.stop()
        cls.mock_put_patcher.stop()
        cls.mock_patch_patcher.stop()
        cls.mock_delete_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        with open(os.path.join(data_path, "newSubmission.json")) as handle:
            data = json.load(handle)

        self.submission = Submission(self.auth, data=data)

        with open(os.path.join(data_path, "contents.json")) as handle:
            self.content = json.load(handle)

        # defining samples
        self.sample1 = {
            'alias': 'animal_1',
            'title': 'animal_title',
            'releaseDate': '2018-07-13',
            'taxonId': 9940,
            'attributes': {
                'material': [
                    {'value': 'organism',
                     'terms': [
                        {'url': 'http://purl.obolibrary.org/obo/OBI_0100026'}
                     ]}
                ],
                'project': [{'value': 'test'}]
            },
            'sampleRelationships': []}

        self.sample2 = {
            'alias': 'sample_1',
            'title': 'sample_title',
            'releaseDate': '2018-07-13',
            'taxonId': 9940,
            'description': 'a description',
            'attributes': {
                'material': [
                    {'value': 'specimen from organism',
                     'terms': [
                        {'url': 'http://purl.obolibrary.org/obo/OBI_0001479'}
                     ]}
                ],
                'project': [{'value': 'test'}]
            },
            'sampleRelationships': [{
                'alias': 'animal_1',
                'relationshipNature': 'derived from'}]
            }

    def test_str(self):
        with open(os.path.join(data_path, "submissionStatus1.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        test = self.submission.__str__()
        self.assertIsInstance(test, str)

    def create_sample(self, sample):
        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = self.content
        self.mock_get.return_value.status_code = 200

        with open(os.path.join(data_path, "%s.json" % (sample))) as handle:
            data = json.load(handle)

        self.mock_post.return_value = Mock()
        self.mock_post.return_value.json.return_value = data
        self.mock_post.return_value.status_code = 201

        return self.submission.create_sample(getattr(self, sample))

    def test_create_sample(self):
        sample1 = self.create_sample("sample1")
        self.assertIsInstance(sample1, Sample)

        sample2 = self.create_sample("sample2")
        self.assertIsInstance(sample2, Sample)

    def mocked_get_samples(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "MockResponse not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        get_samples_link = (
            "https://submission-test.ebi.ac.uk/api/submissions/"
            "c8c86558-8d3a-4ac5-8638-7aa354291d61/contents/samples")

        with open(os.path.join(data_path, "samples.json")) as handle:
            samples = json.load(handle)

        with open(os.path.join(data_path, "validation1.json")) as handle:
            validation1 = json.load(handle)

        with open(os.path.join(data_path, "validation2.json")) as handle:
            validation2 = json.load(handle)

        # followin content -> samples
        if args[0] == get_samples_link:
            return MockResponse(samples, 200)

        # sample1 validation result
        elif args[0] == (
                'https://submission-test.ebi.ac.uk/api/samples/90c8f449-'
                'b3c2-4238-a22b-fd03bc02a5d2/validationResult'):
            return MockResponse(validation1, 200)

        # sample1 validtation result
        elif args[0] == (
                'https://submission-test.ebi.ac.uk/api/samples/58cb010a-'
                '3a89-42b7-8ccd-67b6f8b6dd4c/validationResult'):
            return MockResponse(validation2, 200)

        return MockResponse(None, 404)

    # We patch 'requests.get' with our own method. The mock object is passed
    # in to our test case method.
    @patch('requests.get', side_effect=mocked_get_samples)
    def test_get_samples(self, mock_get):
        samples = self.submission.get_samples(validationResult='Complete')

        self.assertIsInstance(samples, list)
        self.assertEqual(len(samples), 2)

    def mocked_get_empty_samples(*args, **kwargs):
        """Simulate a submission with no samples at all"""

        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "MockResponse not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        get_samples_link = (
            "https://submission-test.ebi.ac.uk/api/submissions/"
            "c8c86558-8d3a-4ac5-8638-7aa354291d61/contents/samples")

        with open(os.path.join(data_path, "empty_samples.json")) as handle:
            samples = json.load(handle)

        # followin content -> samples
        if args[0] == get_samples_link:
            return MockResponse(samples, 200)

        # default response
        return MockResponse(None, 404)

    # patch a request.get to return 0 samples for a submission
    @patch('requests.get', side_effect=mocked_get_empty_samples)
    def test_get_empty_samples(self, mock_get):
        samples = self.submission.get_samples(validationResult='Complete')

        self.assertIsInstance(samples, list)
        self.assertEqual(len(samples), 0)

    def test_get_status(self):
        with open(os.path.join(data_path, "validationResults.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        statuses = self.submission.get_status()
        self.assertEqual(statuses['Complete'], 2)

    def test_check_ready(self):
        with open(os.path.join(
                data_path, "availableSubmissionStatuses.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        check = self.submission.check_ready()
        self.assertTrue(check)

    def mocked_finalize(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = "MockResponse not implemented: %s" % (args[0])

            def json(self):
                return self.json_data

        check_ready_link = (
            "https://submission-test.ebi.ac.uk/api/submissions/c8c86558-"
            "8d3a-4ac5-8638-7aa354291d61/availableSubmissionStatuses")

        with open(os.path.join(
                data_path, "availableSubmissionStatuses.json")) as handle:
            check_ready_data = json.load(handle)

        validation_link = (
            "https://submission-test.ebi.ac.uk/api/validationResults/search/"
            "by-submission?submissionId=c8c86558-8d3a-4ac5-8638-7aa354291d61")

        with open(os.path.join(data_path, "validationResults.json")) as handle:
            validation_data = json.load(handle)

        self_link = (
            "https://submission-test.ebi.ac.uk/api/submissions/"
            "c8c86558-8d3a-4ac5-8638-7aa354291d61")

        with open(os.path.join(data_path, "newSubmission.json")) as handle:
            self_data = json.load(handle)

        status_link = (
            "https://submission-test.ebi.ac.uk/api/submissions/c8c86558-"
            "8d3a-4ac5-8638-7aa354291d61/submissionStatus")

        with open(os.path.join(data_path, "submissionStatus2.json")) as handle:
            status_data = json.load(handle)

        if args[0] == check_ready_link:
            return MockResponse(check_ready_data, 200)

        elif args[0] == validation_link:
            return MockResponse(validation_data, 200)

        elif args[0] == self_link:
            return MockResponse(self_data, 200)

        elif args[0] == status_link:
            return MockResponse(status_data, 200)

        return MockResponse(None, 404)

    @patch('requests.get', side_effect=mocked_finalize)
    def test_finalize(self, mock_get):
        self.mock_put.return_value = Mock()
        self.mock_put.return_value.json.return_value = {}
        self.mock_put.return_value.status_code = 200

        document = self.submission.finalize()
        self.assertIsInstance(document, Document)

    def test_delete(self):
        self.mock_delete.return_value = Mock()
        self.mock_delete.return_value.last_response = ''
        self.mock_delete.return_value.status_code = 204

        self.submission.delete()


class SampleTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('pyUSIrest.client.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_patch_patcher = patch('pyUSIrest.client.requests.patch')
        cls.mock_patch = cls.mock_patch_patcher.start()

        cls.mock_delete_patcher = patch('pyUSIrest.client.requests.delete')
        cls.mock_delete = cls.mock_delete_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.mock_patch_patcher.stop()
        cls.mock_delete_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        with open(os.path.join(data_path, "sample2.json")) as handle:
            self.data = json.load(handle)

        self.sample = Sample(self.auth, data=self.data)

    def test_str(self):
        test = self.sample.__str__()
        self.assertIsInstance(test, str)

    def test_patch(self):
        self.mock_patch.return_value = Mock()
        self.mock_patch.return_value.json.return_value = self.data
        self.mock_patch.return_value.status_code = 200

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = self.data
        self.mock_get.return_value.status_code = 200

        self.sample.patch(sample_data={'title': 'new title'})

    def test_delete(self):
        self.mock_delete.return_value = Mock()
        self.mock_delete.return_value.last_response = ''
        self.mock_delete.return_value.status_code = 204

        self.sample.delete()
