#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 14:23:09 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import os
import json
import types

from collections import defaultdict
from unittest.mock import patch, Mock
from unittest import TestCase

from pyUSIrest.auth import Auth
from pyUSIrest.client import Document
from pyUSIrest.exceptions import NotReadyError, USIDataError
from pyUSIrest.usi import Submission, Sample

from .common import DATA_PATH
from .test_auth import generate_token


class SubmissionTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_post_patcher = patch('requests.Session.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.mock_put_patcher = patch('requests.Session.put')
        cls.mock_put = cls.mock_put_patcher.start()

        cls.mock_patch_patcher = patch('requests.Session.patch')
        cls.mock_patch = cls.mock_patch_patcher.start()

        cls.mock_delete_patcher = patch('requests.Session.delete')
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

        with open(os.path.join(DATA_PATH, "newSubmission.json")) as handle:
            data = json.load(handle)

        self.submission = Submission(self.auth, data=data)

        with open(os.path.join(DATA_PATH, "contents.json")) as handle:
            self.content = json.load(handle)

        # defining samples
        self.sample1 = {
            'alias': 'animal_1',
            'title': 'animal_title',
            'releaseDate': '2018-07-13',
            'taxonId': 9940,
            'taxon': 'Ovis aries',
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
            'taxonId': 9940,
            'taxon': 'Ovis aries',
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
        with open(os.path.join(DATA_PATH, "submissionStatus1.json")) as handle:
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

        with open(os.path.join(DATA_PATH, "%s.json" % (sample))) as handle:
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

        with open(os.path.join(DATA_PATH, "samples.json")) as handle:
            samples = json.load(handle)

        with open(os.path.join(DATA_PATH, "validation1.json")) as handle:
            validation1 = json.load(handle)

        with open(os.path.join(DATA_PATH, "validation2.json")) as handle:
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

    # We patch 'requests.Session.get' with our own method. The mock object is
    # passed in to our test case method.
    @patch('requests.Session.get', side_effect=mocked_get_samples)
    def test_get_samples(self, mock_get):
        samples = self.submission.get_samples(status='Complete')

        # samples is now a generator
        self.assertIsInstance(samples, types.GeneratorType)

        # convert it into a list
        samples = list(samples)
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

        with open(os.path.join(DATA_PATH, "empty_samples.json")) as handle:
            samples = json.load(handle)

        # followin content -> samples
        if args[0] == get_samples_link:
            return MockResponse(samples, 200)

        # default response
        return MockResponse(None, 404)

    # patch a request.get to return 0 samples for a submission
    @patch('requests.Session.get', side_effect=mocked_get_empty_samples)
    def test_get_empty_samples(self, mock_get):
        samples = self.submission.get_samples(status='Complete')

        self.assertRaises(StopIteration, next, samples)

    def test_get_status(self):
        with open(os.path.join(DATA_PATH, "validationResults.json")) as handle:
            data = json.load(handle)

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        statuses = self.submission.get_status()
        self.assertEqual(statuses['Complete'], 2)

    def test_check_ready(self):
        with open(os.path.join(
                DATA_PATH, "availableSubmissionStatuses.json")) as handle:
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
                DATA_PATH, "availableSubmissionStatuses.json")) as handle:
            check_ready_data = json.load(handle)

        validation_link = (
            "https://submission-test.ebi.ac.uk/api/validationResults/search/"
            "by-submission?submissionId=c8c86558-8d3a-4ac5-8638-7aa354291d61")

        with open(os.path.join(DATA_PATH, "validationResults.json")) as handle:
            validation_data = json.load(handle)

        self_link = (
            "https://submission-test.ebi.ac.uk/api/submissions/"
            "c8c86558-8d3a-4ac5-8638-7aa354291d61")

        with open(os.path.join(DATA_PATH, "newSubmission.json")) as handle:
            self_data = json.load(handle)

        status_link = (
            "https://submission-test.ebi.ac.uk/api/submissions/c8c86558-"
            "8d3a-4ac5-8638-7aa354291d61/submissionStatus")

        with open(os.path.join(DATA_PATH, "submissionStatus2.json")) as handle:
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

    @patch('requests.Session.get', side_effect=mocked_finalize)
    def test_finalize(self, mock_get):
        self.mock_put.return_value = Mock()
        self.mock_put.return_value.json.return_value = {}
        self.mock_put.return_value.status_code = 200

        document = self.submission.finalize()
        self.assertIsInstance(document, Document)

    def test_finalize_not_ready(self):
        with open(os.path.join(
                DATA_PATH, "availableSubmissionStatuses.json")) as handle:
            data = json.load(handle)

        # remove a key from data
        del data['_embedded']

        self.mock_get.return_value = Mock()
        self.mock_get.return_value.json.return_value = data
        self.mock_get.return_value.status_code = 200

        self.assertRaises(
            NotReadyError,
            self.submission.finalize)

    def mocked_finalize_errors(*args, **kwargs):
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

        set_reply("https://submission-test.ebi.ac.uk/api/submissions/"
                  "c8c86558-8d3a-4ac5-8638-7aa354291d61/"
                  "availableSubmissionStatuses",
                  "availableSubmissionStatuses.json")

        set_reply("https://submission-test.ebi.ac.uk/api/"
                  "validationResults/search/by-submission?"
                  "submissionId=c8c86558-8d3a-4ac5-8638-7aa354291d61",
                  "validationResultsError.json")

        return replies[args[0]]

    @patch('requests.Session.get', side_effect=mocked_finalize_errors)
    def test_finalize_has_errors(self, my_get):
        self.assertRaises(
            USIDataError,
            self.submission.finalize)

    def test_delete(self):
        self.mock_delete.return_value = Mock()
        self.mock_delete.return_value.last_response = ''
        self.mock_delete.return_value.status_code = 204

        self.submission.delete()


class SampleTest(TestCase):
    @classmethod
    def setup_class(cls):
        cls.mock_get_patcher = patch('requests.Session.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_patch_patcher = patch('requests.Session.patch')
        cls.mock_patch = cls.mock_patch_patcher.start()

        cls.mock_delete_patcher = patch('requests.Session.delete')
        cls.mock_delete = cls.mock_delete_patcher.start()

    @classmethod
    def teardown_class(cls):
        cls.mock_get_patcher.stop()
        cls.mock_patch_patcher.stop()
        cls.mock_delete_patcher.stop()

    def setUp(self):
        self.auth = Auth(token=generate_token())

        with open(os.path.join(DATA_PATH, "sample2.json")) as handle:
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
