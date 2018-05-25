#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:41:31 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

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
        """Generic request method"""

        if self.auth.is_expired():
            raise RuntimeError("Your token is expired")

        if not headers:
            logger.debug("Using default headers")
            headers = self.headers

        return requests.get(url, headers=headers)

    def post(self):
        raise NotImplementedError("POST method not implemented")

    def parse_response(self, response):
        """convert response in a dict"""

        return response.json()

    def follow_link(self, link):
        """Follow link"""

        self.last_response = self.request(link, headers=self.headers)
        self.last_status_code = self.last_response.status_code

        return self.last_response


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
                setattr(self, key, data[key])

            else:
                logger.error("key %s not implemented" % (key))

        # return data as json object
        return data

    def follow_link(self, tag, auth=None):
        link = link = self._links[tag]['href']
        response = super().follow_link(link)

        if self.last_status_code != 200:
            raise ConnectionError(response.text)

        # create a new document
        document = Document(auth=auth)
        document.data = document.parse_response(response)

        return document


class Root(Document):
    # define the default url
    api_root = "https://submission-test.ebi.ac.uk/api"

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
        document = self.follow_link('userTeams')

        # TODO: deal with pages and results

        # a list ob objects to return
        teams = []

        # now iterate over teams and create new objects
        for team_data in document._embedded['teams']:
            teams.append(Team(self.auth, team_data))

        return teams

    def get_team_by_name(self, team_name):
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
        document = self.follow_link('userSubmissions')

        # a list ob objects to return
        submissions = []

        # now iterate over teams and create new objects
        for submission_data in document._embedded['submissions']:
            submissions.append(Submission(self.auth, submission_data))

        return submissions


class Team(Document):
    def __init__(self, auth, data=None):
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.name = None
        self.data = None

        if data:
            for key in data.keys():
                if hasattr(self, key):
                    if key == '_links':
                        self._links.update(data[key])

                    else:
                        setattr(self, key, data[key])

                else:
                    logger.error("key %s not implemented" % (key))

        self.data = data

    def __str__(self):
        return self.name

    def get_submissions(self):
        """Follows submission link"""

        # follow link
        document = self.follow_link('submissions')

        # a list ob objects to return
        submissions = []

        # now iterate over teams and create new objects
        for submission_data in document._embedded['submissions']:
            submissions.append(Submission(self.auth, submission_data))

        return submissions


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

        if data:
            for key in data.keys():
                if hasattr(self, key):
                    setattr(self, key, data[key])

                else:
                    logger.error("key %s not implemented" % (key))

        self.data = data

        # check for name
        if 'self' in self._links:
            self.name = self._links['self']['href'].split("/")[-1]

    def __str__(self):
        return self.name
