#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:41:31 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import requests


class Client():
    """A class to deal with Biosample Submission server. You need to call this
    class after instantiating :class:`python_ebi_app.Auth`::

        import getpass
        from python_ebi_aap import Auth, Client
        auth = Auth(user=<you_aap_user>, password=getpass.getpass())
        client = Client(auth)
    """
    api_root = "https://submission-test.ebi.ac.uk/api"
    headers = {'Accept': 'application/hal+json'}

    def __init__(self, auth):
        # my attributes
        self._auth = None
        self.last_response = None

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

    def __parse_response(self, response):
        return response.json()

    def __get_links(self, response):
        return self.__parse_response(response)['_links']

    def request(self, url, headers=None):
        """Generic request method"""

        if self.auth.is_expired():
            raise RuntimeError("Your token is expired")

        if not headers:
            headers = self.headers

        return requests.get(url, headers=headers)

    def get_root(self):
        """This gets the foobar

        This really should have a full function definition, but I am too lazy.

        >>> print get_foobar(10, 20)
        30
        >>> print get_foobar('a', 'b')
        ab

        Isn't that what you want?
        """

        self.last_response = self.request(self.api_root, headers=self.headers)
        return self.last_response

    def get_user_teams(self):
        """get user teams"""

        # get teams urls
        response = self.get_root()
        link = self.__get_links(response)['userTeams']['href']

        # follow link
        self.last_response = self.request(link, headers=self.headers)
        return self.last_response


class Team(Client):
    def __init__(self, auth):
        super().__init__(auth)

    def get_team_names(self):
        response = self.get_user_teams()

        data = response.json()
        teams = []

        for team in data['_embedded']['teams']:
            teams.append(team['name'])

        return teams

    def get_subission(self, team_name):
        """Return a submission object for a team"""

        team_data = None

        # get user teams
        response = self.get_user_teams()
        data = response.json()

        for team in data['_embedded']['teams']:
            if team['name'] == team_name:
                team_data = team
                break

        return Submission(self.auth, team_data)


class Submission(Client):
    def __init__(self, auth, team_data):
        super().__init__(auth)
        self.team = team_data
