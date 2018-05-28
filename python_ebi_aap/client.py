#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:41:31 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import copy
import requests
import logging


logger = logging.getLogger(__name__)


class Client():
    """A class to deal with Biosample Submission server. You need to call this
    class after instantiating :class:`python_ebi_app.Auth`::

        import getpass
        from python_ebi_aap import Auth, Client
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
        self.headers['Authorization'] = "Bearer {token}".format(
                token=auth.token)
        self._auth = auth

    def request(self, url, headers=None):
        """Generic GET method"""

        if self.auth.is_expired():
            raise RuntimeError("Your token is expired")

        if not headers:
            logger.debug("Using default headers")
            headers = self.headers

        return requests.get(url, headers=headers)

    def post(self, url, payload={}, headers=None):
        """Generic POST method"""

        if self.auth.is_expired():
            raise RuntimeError("Your token is expired")

        if not headers:
            logger.debug("Using default headers")
            headers = self.headers

        return requests.post(url, json=payload, headers=headers)

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

    def parse_response(self, response):
        data = response.json()

        # test response type
        for key in data.keys():
            if hasattr(self, key):
                logger.debug("Setting %s -> %s" % (key, data[key]))
                setattr(self, key, data[key])

            else:
                logger.error("key %s not implemented" % (key))

        # return data as json object
        return data

    def follow_link(self, tag, auth=None):
        logger.debug("Following %s link" % (tag))

        link = self._links[tag]['href']
        response = super().follow_link(link)

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # create a new document
        document = Document(auth=auth)
        document.data = document.parse_response(response)

        # copying last responsponse in order to improve data assignment
        logger.debug("Assigning %s to document" % (response))

        document.last_response = response
        document.last_status_code = response.status_code

        return document

    def read_data(self, data):
        """Read data from dictionary object"""

        # dealing with this type of documents
        for key in data.keys():
            self.__update_key(key, data[key])

        self.data = data

    def __update_key(self, key, value):
        """Helper function to update keys"""

        if hasattr(self, key):
            if getattr(self, key) and len(getattr(self, key)) > 0:
                logger.warn("Found %s -> %s" % (key, getattr(self, key)))
                logger.warn("Updating %s -> %s" % (key, value))
                getattr(self, key).update(value)

            else:
                logger.debug("Setting %s -> %s" % (key, value))
                setattr(self, key, value)

        else:
            logger.error("key %s not implemented" % (key))


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
        self.data = self.parse_response(self.last_response)

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
        document = Document(auth=self.auth)
        document.data = document.parse_response(response)

        # get a submission object
        submission_data = document._links["submission"]
        return Submission(self.auth, submission_data)


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

        # each document need to parse data as dictionary, since there could be
        # more submission read from the same page. I cant read data from
        # self.last_response itself, cause I can't have a last response
        if data:
            logger.debug("Reading data for submission")
            self.read_data(data)

        # check for name
        if 'self' in self._links:
            self.name = self._links['self']['href'].split("/")[-1]
            logger.debug("Using %s as submission name" % (self.name))

    def __str__(self):
        return self.name
