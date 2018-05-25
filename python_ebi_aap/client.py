#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:41:31 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import requests


class Client():
    api_root = "https://submission-test.ebi.ac.uk/api"
    headers = {'Accept': 'application/hal+json'}

    def __init__(self, auth):
        """Instantiate the object from a valid Auth object"""

        self.auth = auth
        self.headers['Authorization'] = "Bearer {token}".format(
                token=self.auth.token)

    def __parse_response(self, response):
        return response.json()

    def __get_links(self, response):
        return self.__parse_response(response)['_links']

    def get_root(self):
        """Start from EBI root"""

        self.last_response = requests.get(self.api_root, headers=self.headers)
        return self.last_response

    def get_user_teams(self):
        """get user teams"""

        # get teams urls
        response = self.get_root()
        link = self.__get_links(response)['userTeams']['href']

        # follow link
        self.last_response = requests.get(link, headers=self.headers)
        return self.last_response
