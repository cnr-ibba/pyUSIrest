#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:41:31 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import copy
import requests
import logging

from .auth import Auth


logger = logging.getLogger(__name__)


class Client():
    """A class to deal with Biosample Submission server. You need to call this
    class after instantiating :class:`python_ebi_app.Auth`::

        import getpass
        from pyEBIrest import Auth, Client
        auth = Auth(user=<you_aap_user>, password=getpass.getpass())
        client = Client(auth)
    """

    headers = {'Accept': 'application/hal+json'}

    def __init__(self, auth):
        # my attributes
        self._auth = None
        self.last_response = None
        self.last_status_code = None

        # call proper method
        self.auth = auth

    @property
    def auth(self):
        return self._auth

    @auth.setter
    def auth(self, auth):
        logger.debug("Auth type is %s" % (type(auth)))

        # assign Auth object or create a new one
        if isinstance(auth, Auth):
            logger.debug("Assigning an Auth object")
            self._auth = auth

        else:
            logger.debug("Creating an Auth object")
            self._auth = Auth(token=auth)

        logger.debug("Updating headers with token")
        self.headers['Authorization'] = "Bearer {token}".format(
                token=self._auth.token)

    def __check(self, headers):
        """Checking headers and tocken"""

        if self.auth.is_expired():
            raise RuntimeError("Your token is expired")

        if not headers:
            logger.debug("Using default headers")
            headers = self.headers

        return headers

    def request(self, url, headers=None):
        """Generic GET method"""

        headers = self.__check(headers)

        return requests.get(url, headers=headers)

    def post(self, url, payload={}, headers=None):
        """Generic POST method"""

        headers = self.__check(headers)

        return requests.post(url, json=payload, headers=headers)

    def patch(self, url, payload={}, headers=None):
        """Generic PATCH method"""

        headers = self.__check(headers)

        return requests.patch(url, json=payload, headers=headers)

    def delete(self, url, headers=None):
        """Generic DELETE method"""

        headers = self.__check(headers)

        return requests.delete(url, headers=headers)

    def parse_response(self, response):
        """convert response in a dict"""

        return response.json()

    def follow_link(self, link):
        """Follow link. Calling request and setting attributes"""

        response = self.request(link, headers=self.headers)

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        return response


class Document(Client):
    def __init__(self, auth=None):
        if auth:
            Client.__init__(self, auth)

        # my class attributes
        self._links = {}
        self._embedded = {}
        self.page = {}
        self.name = None
        self.data = {}

    def parse_response(self, response, force=False):
        # get data
        data = super().parse_response(response)

        # read data and setting self.data
        self.read_data(data, force)

    def follow_link(self, tag, auth=None, force=True):
        logger.debug("Following %s link" % (tag))

        link = self._links[tag]['href']
        response = super().follow_link(link)

        # create a new document
        document = Document(auth=auth)
        document.parse_response(response, force)

        # copying last responsponse in order to improve data assignment
        logger.debug("Assigning %s to document" % (response))

        document.last_response = response
        document.last_status_code = response.status_code

        return document

    def follow_self_link(self, auth=None):
        """Follow self link and update class attributes"""

        logger.debug("Following self link")

        link = self._links['self']['href']
        response = super().follow_link(link)

        logger.debug("Updating self")

        # create a new document
        self.parse_response(response)

        # copying last responsponse in order to improve data assignment
        logger.debug("Assigning %s to self" % (response))

        self.last_response = response
        self.last_status_code = response.status_code

    @classmethod
    def read_link(cls, auth, link):
        """Read a link a returns an object"""

        # define a new client object
        client = Client(auth=auth)

        # get a response
        response = client.follow_link(link)

        # create a new document and read data
        instance = cls(auth=auth)
        instance.parse_response(response)

        # return data
        return instance

    def read_data(self, data, force=False):
        """Read data from dictionary object"""

        # dealing with this type of documents
        for key in data.keys():
            self.__update_key(key, data[key], force)

        self.data = data

    def __update_key(self, key, value, force=False):
        """Helper function to update keys"""

        if hasattr(self, key):
            if getattr(self, key) and getattr(self, key) != '':
                logger.debug("Found %s -> %s" % (key, getattr(self, key)))
                logger.debug("Updating %s -> %s" % (key, value))

            else:
                logger.debug("Setting %s -> %s" % (key, value))

            setattr(self, key, value)

        else:
            logger.error("key %s not implemented" % (key))

            if force is True:
                logger.info("Forcing %s -> %s" % (key, value))
                setattr(self, key, value)


class Root(Document):
    # define the default url
    api_root = "https://submission-test.ebi.ac.uk/api/"

    def __init__(self, auth):
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # defining my attributes. Headers are inherited
        self.last_response = self.request(self.api_root, headers=self.headers)
        self.last_status_code = self.last_response.status_code

        # parsing response and setting self.data
        self.parse_response(self.last_response)

    def __str__(self):
        return "Biosample API root at %s" % (self.api_root)

    def get_user_teams(self):
        """follow userTeams link"""

        # follow link
        document = self.follow_link('userTeams', auth=self.auth)

        # TODO: deal with pages and results

        # a list ob objects to return
        teams = []

        # now iterate over teams and create new objects
        for i, team_data in enumerate(document._embedded['teams']):
            teams.append(Team(self.auth, team_data))
            logger.debug("Found %s team" % (teams[i].name))

        logger.info("Got %s teams" % len(teams))

        return teams

    def get_team_by_name(self, team_name):
        logger.debug("Searching for %s" % (team_name))

        # get all teams
        teams = self.get_user_teams()

        for team in teams:
            if team.name == team_name:
                return team

        # if I arrive here, no team is found
        raise NameError("team: {team} not found".format(team=team_name))

    def get_user_submissions(self):
        """Follow the userSubmission link"""

        # follow link
        document = self.follow_link('userSubmissions', auth=self.auth)

        # a list ob objects to return
        submissions = []

        # now iterate over teams and create new objects
        for i, submission_data in enumerate(document._embedded['submissions']):
            submissions.append(Submission(self.auth, submission_data))
            logger.debug("Found %s submission" % (submissions[i].name))

        logger.info("Got %s submissions" % len(submissions))

        return submissions


class Team(Document):
    def __init__(self, auth, data=None):
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.name = None
        self.data = None

        # dealing with this type of documents.
        if data:
            logger.debug("Reading data for team")
            self.read_data(data)

    def __str__(self):
        return self.name

    def get_submissions(self):
        """Follows submission link"""

        # follow link
        document = self.follow_link('submissions', auth=self.auth)

        # a list ob objects to return
        submissions = []

        # now iterate over teams and create new objects
        for i, submission_data in enumerate(document._embedded['submissions']):
            submissions.append(Submission(self.auth, submission_data))
            logger.debug("Found %s submission" % (submissions[i].name))

        return submissions

    def create_submission(self):
        """Create a submission"""

        # get the link for submission:create. I don't want a document using
        # get method, I need instead a POST request
        link = self._links['submissions:create']['href']

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        # call a post method a deal with response
        response = self.post(link, payload={}, headers=headers)

        if response.status_code != 201:
            raise ConnectionError(response.text)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        # create a new document
        submission = Submission(auth=self.auth)
        submission.parse_response(response)

        return submission


class Submission(Document):
    def __init__(self, auth, data=None):
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.name = None
        self.team = None
        self.createdDate = None
        self.lastModifiedDate = None
        self.lastModifiedBy = None
        self.submissionStatus = None
        self.submitter = None
        self.createdBy = None

        # when this attribute appears? maybe when submission take place
        self.submissionDate = None

        # each document need to parse data as dictionary, since there could be
        # more submission read from the same page. I cant read data from
        # self.last_response itself, cause I can't have a last response
        if data:
            self.read_data(data)

    def __str__(self):
        return self.name

    def read_data(self, data, force=False):
        """Custom read_data method"""

        logger.debug("Reading data for submission")
        super().read_data(data, force)

        # check for name
        if 'self' in self._links:
            self.name = self._links['self']['href'].split("/")[-1]
            logger.debug("Using %s as submission name" % (self.name))

    def create_sample(self, sample_data):
        """Create a sample"""

        # get the link for sample create
        document = self.follow_link("contents", auth=self.auth)

        # get the link for submission:create. I don't want a document using
        # get method, I need instead a POST request
        link = document._links['samples:create']['href']

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        # call a post method a deal with response
        response = self.post(link, payload=sample_data, headers=headers)

        if response.status_code != 201:
            raise ConnectionError(response.text)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        # create a new sample
        sample = Sample(auth=self.auth)
        sample.parse_response(response)

        # returning sample as and object
        return sample

    def get_samples(self):
        """returning all samples as a list"""

        document = self.follow_link(
            'contents', auth=self.auth
            ).follow_link('samples', auth=self.auth)

        # a list ob objects to return
        samples = []

        for i, sample_data in enumerate(document.data['_embedded']['samples']):
            samples.append(Sample(self.auth, sample_data))
            logger.debug("Found %s sample" % (str(samples[i])))

        logger.info("Got %s samples" % len(samples))

        return samples

    def delete(self):
        """Delete this instance from a submission"""

        link = self._links['self:delete']['href']
        logger.info("Removing submission %s" % self.name)

        response = Client.delete(self, link)

        if response.status_code != 204:
            raise ConnectionError(response.text)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        # don't return anything


class Sample(Document):
    def __init__(self, auth, data=None):
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.alias = None
        self.team = None
        self.title = None
        self.description = None
        self.attributes = None
        self.sampleRelationships = None
        self.taxonId = None
        self.taxon = None
        self.releaseDate = None
        self.createdDate = None
        self.lastModifiedDate = None
        self.createdBy = None
        self.lastModifiedBy = None

        # when this attribute appears? maybe when submission take place
        self.accession = None

        if data:
            self.read_data(data)

    def __str__(self):
        # get accession or alias
        if self.accession:
            return "%s (%s)" % (self.accession, self.title)
        else:
            return "%s (%s)" % (self.alias, self.title)

    def read_data(self, data, force=False):
        """Custom read_data method"""

        logger.debug("Reading data for Sample")
        super().read_data(data, force)

        # check for name
        if 'self' in self._links:
            self.name = self._links['self']['href'].split("/")[-1]
            logger.debug("Using %s as sample name" % (self.name))

    def delete(self):
        """Delete this instance from a submission"""

        link = self._links['self:delete']['href']
        logger.info("Removing sample %s from submission" % self.name)

        response = Client.delete(self, link)

        if response.status_code != 204:
            raise ConnectionError(response.text)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        # don't return anything

    def reload(self):
        """refreshing data"""

        logger.info("Refreshing data data for sample")
        self.follow_self_link(auth=self.auth)

    def patch(self, sample_data):
        """Patch a sample"""

        link = self._links['self']['href']
        logger.info("patching sample %s with %s" % (self.name, sample_data))

        response = Client.patch(self, link, payload=sample_data)

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        # reloading data
        self.reload()