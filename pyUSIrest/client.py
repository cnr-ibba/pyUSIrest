#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:41:31 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import copy
import requests
import logging
import collections

from url_normalize import url_normalize

from . import __version__
from .auth import Auth


logger = logging.getLogger(__name__)


class Client():
    """A class to deal with Biosample Submission server. It perform request
    modelling user token in request headers. You need to call this class after
    instantiating an :py:class:`Auth <pyUSIrest.auth.Auth>` object::

        import getpass
        from pyUSIrest import Auth, Client
        auth = Auth(user=<you_aap_user>, password=getpass.getpass())
        client = Client(auth)
        response = client.request("https://submission-test.ebi.ac.uk/api/")

    Attributes:
        headers (dict): default headers for requests
        last_response (requests.Response): last response object read by this
            class
        last_satus_code (int): last status code read by this class

    """

    headers = {
        'Accept': 'application/hal+json',
        'User-Agent': 'pyUSIrest %s' % (__version__)
    }

    def __init__(self, auth):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object

        """

        # my attributes
        self._auth = None
        self.last_response = None
        self.last_status_code = None

        # call proper method
        self.auth = auth

    @property
    def auth(self):
        """Get/Set :py:class:`Auth <pyUSIrest.auth.Auth>` object"""

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
        """Generic GET method

        Args:
            url (str): url to request
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.get(url, headers=headers)

    def post(self, url, payload={}, headers=None):
        """Generic POST method

        Args:
            url (str): url to request
            payload (dict): data to send
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.post(url, json=payload, headers=headers)

    def patch(self, url, payload={}, headers=None):
        """Generic PATCH method

        Args:
            url (str): url to request
            payload (dict): data to send
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.patch(url, json=payload, headers=headers)

    def delete(self, url, headers=None):
        """Generic DELETE method

        Args:
            url (str): url to request
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.delete(url, headers=headers)

    def put(self, url, payload={}, headers=None):
        """Generic PUT method

        Args:
            url (str): url to request
            payload (dict): data to send
            headers (dict): custom header for request

        Returns:
            requests.Response: a response object
        """

        headers = self.__check(headers)

        return requests.put(url, json=payload, headers=headers)

    def parse_response(self, response):
        """Convert a response in a dict

        Args:
            response (requests.Response): a response object

        Returns:
            dict: the output of
            :py:meth:`response.json() <requests.Response.json>`
        """

        return response.json()

    def follow_url(self, url):
        """Calling request and setting class attributes

        Args:
            url (str): url to request

        Returns:
            requests.Response: a response object
        """

        response = self.request(url, headers=self.headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

        return response


class Document(Client):
    """Base class for pyUSIrest classes. It models common methods and
    attributes by calling :py:class:`Client` and reading json response from
    biosample API

    Attributes:
        _link (dict): ``_links`` data read from USI response
        _embeddedd (dict): ``_embedded`` data read from USI response
        page (dict): ``page`` data read from USI response
        name (str): name of this object
        data (dict): data from USI read with
            :py:meth:`response.json() <requests.Response.json>`

    """

    def __init__(self, auth=None):
        if auth:
            Client.__init__(self, auth)

        # my class attributes
        self._links = {}
        self._embedded = {}
        self.page = {}
        self.name = None
        self.data = {}

    def __paginate(self, data):
        """Follow pages and join data"""

        # create a new dictionary
        new_data = copy.copy(data)

        while 'next' in data['_links']:
            url = data['_links']['next']['href']
            logger.debug("Paginating %s" % (url))
            response = super().follow_url(url)
            data = super().parse_response(response)

            for key, value in data['_embedded'].items():
                new_data['_embedded'][key] += value

        return new_data

    def parse_response(self, response, force=False):
        """Parse a :py:class:`requests.Response` object and instantiate
        class attributes.

        Args:
            response (requests.Response): a response object
            force (bool): set a new class attribute if not present
        """

        # get data as dictionary
        data = super().parse_response(response)

        # do data has pages?
        if 'page' in data and data['page']['totalPages'] > 1:
            logger.debug("Found %s pages" % (data['page']['totalPages']))
            data = self.__paginate(data)

        # read data and setting self.data
        self.read_data(data, force)

    def follow_url(self, tag, auth=None, force=True):
        """Pick a url from data attribute, perform a request and returns
        a document object. For instance::

            document.follow_url('userSubmissions')

        will return a document instance by requesting with
        :py:meth:`Client.follow_url` using
        ``document.data['_links']['userSubmissions']['href']`` as url

        Args:
            tag (str): a key from USI response dictionary
            auth (Auth): an Auth object to pass to result
            force (bool): set a new class attribute if not present

        Returns:
            Document: a document object
        """

        logger.debug("Following %s url" % (tag))

        url = self._links[tag]['href']
        response = super().follow_url(url)

        # create a new document
        document = Document(auth=auth)
        document.parse_response(response, force)

        # copying last responsponse in order to improve data assignment
        logger.debug("Assigning %s to document" % (response))

        document.last_response = response
        document.last_status_code = response.status_code

        return document

    @classmethod
    def clean_url(cls, url):
        """Remove stuff like ``{?projection}`` from url

        Args:
            url (str): a string url

        Returns:
            str: the cleaned url
        """

        # remove {?projection} from self url. This is unreachable
        if '{?projection}' in url:
            logger.debug("removing {?projection} from url")
            url = url.replace("{?projection}", "")

        return url

    def follow_self_url(self):
        """Follow *self* url and update class attributes. For instance::

            document.follow_self_url()

        will reload document instance by requesting with
        :py:meth:`Client.follow_url` using
        ``document.data['_links']['self']['href']`` as url"""

        logger.debug("Following self url")

        # get a url to follow
        url = self._links['self']['href']

        # clean url
        url = self.clean_url(url)

        # now follow url
        response = super().follow_url(url)

        logger.debug("Updating self")

        # create a new document
        self.parse_response(response)

        # copying last responsponse in order to improve data assignment
        logger.debug("Assigning %s to self" % (response))

        self.last_response = response
        self.last_status_code = response.status_code

    @classmethod
    def read_url(cls, auth, url):
        """Read a url and returns a :py:class:`Document` object

        Args:
            auth (Auth): an Auth object to pass to result
            url (str): url to request

        Returns:
            Document: a document object
        """

        # define a new client object
        client = Client(auth=auth)

        # clean url
        url = cls.clean_url(url)

        # get a response
        response = client.follow_url(url)

        # create a new document and read data
        instance = cls(auth=auth)
        instance.parse_response(response)

        # return data
        return instance

    def read_data(self, data, force=False):
        """Read data from a dictionary object and set class attributes

        Args:
            data (dict): a data dictionary object read with
                :py:meth:`response.json() <requests.Response.json>`
            force (bool): If True, define a new class attribute from data keys
        """

        # dealing with this type of documents
        for key in data.keys():
            self.__update_key(key, data[key], force)

        self.data = data

    def __update_key(self, key, value, force=False):
        """Helper function to update keys"""

        if hasattr(self, key):
            if getattr(self, key) and getattr(self, key) != '':
                # when I reload data, I do a substitution
                logger.debug("Found %s -> %s" % (key, getattr(self, key)))
                logger.debug("Updating %s -> %s" % (key, value))

            else:
                # don't have this attribute set
                logger.debug("Setting %s -> %s" % (key, value))

            setattr(self, key, value)

        else:
            if force is True:
                logger.info("Forcing %s -> %s" % (key, value))
                setattr(self, key, value)

            else:
                logger.warning("key %s not implemented" % (key))


class Root(Document):
    """Models the USI API Root_ endpoint

    Attributes:
        api_root (str): The base URL for API endpoints

    .. _Root: https://submission-test.ebi.ac.uk/api/docs/ref_root_endpoint.html
    """

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
        """Follow userTeams url and returns all teams belonging to user

        Returns:
            list: A list of :py:class:`Team` objects
        """

        # follow url
        document = self.follow_url('userTeams', auth=self.auth)

        # a list ob objects to return
        teams = []

        # now iterate over teams and create new objects
        for i, team_data in enumerate(document._embedded['teams']):
            teams.append(Team(self.auth, team_data))
            logger.debug("Found %s team" % (teams[i].name))

        logger.info("Got %s teams" % len(teams))

        return teams

    def get_team_by_name(self, team_name):
        """Get a :py:class:`Team` object by name

        Args:
            team_name (str): the name of the team

        Returns:
            Team: a team object

        """
        logger.debug("Searching for %s" % (team_name))

        # get all teams
        teams = self.get_user_teams()

        for team in teams:
            if team.name == team_name:
                return team

        # if I arrive here, no team is found
        raise NameError("team: {team} not found".format(team=team_name))

    def get_user_submissions(self, status=None, team=None):
        """Follow the userSubmission url and returns all submission owned by
        the user

        Args:
            status (str): filter user submissions using this status
            team (str): filter user submissions belonging to this team

        Returns:
            list: A list of :py:class:`Submission` objects
        """

        # follow url
        document = self.follow_url('userSubmissions', auth=self.auth)

        # a list of objects to return
        submissions = []

        # check if I have submission
        if 'submissions' not in document._embedded:
            logger.warning("You haven't any submission yet!")
            return submissions

        # now iterate over teams and create new objects
        for i, submission_data in enumerate(document._embedded['submissions']):
            submission = Submission(self.auth, submission_data)

            if status and submission.status != status:
                logger.debug("Filtering %s submission" % (submission.name))
                continue

            if team and submission.team != team:
                logger.debug("Filtering %s submission" % (submission.name))
                continue

            submissions.append(submission)
            logger.debug("Found %s submission" % (submission.name))

        logger.info("Got %s submissions" % len(submissions))

        return submissions

    def get_submission_by_name(self, submission_name):
        """Got a specific submission object by providing its name

        Args:
            submission_name (str): input submission name

        Returns:
            Submission: The desidered submission as instance
        """

        # define submission url
        url = "/".join([self.api_root, 'submissions', submission_name])

        # fixing url (normalizing)
        url = url_normalize(url)

        # doing a request
        self.last_response = self.request(url, headers=self.headers)
        self.last_status_code = self.last_response.status_code

        if self.last_status_code == 200:
            # read submission data
            submission_data = self.last_response.json()
            submission = Submission(self.auth, submission_data)

            # update status
            submission.update_status()

            return submission

        elif self.last_status_code == 404:
            # if I arrive here, no submission is found
            raise NameError(
                "submission: {name} not found".format(name=submission_name))

        else:
            raise ConnectionError(self.last_response.text)


class User(Document):
    """Deal with EBI AAP endpoint to get user information

    Attributes:
        name (str): Output of ``Auth.claims['nickname']``
        data (dict): data (dict): data from AAP read with
            :py:meth:`response.json() <requests.Response.json>`
        userName (str): AAP username
        email (str): AAP email
        userReference (str): AAP userReference
    """

    def __init__(self, auth, data=None):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object
            data (dict): instantiate the class from a dictionary of user data
        """
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.name = self.auth.claims["nickname"]
        self.data = None

        # other attributes
        self.userName = None
        self.email = None
        self.userReference = None
        self.links = None

        # dealing with this type of documents.
        if data:
            logger.debug("Reading data for user")
            self.read_data(data)

    def get_my_id(self):
        """Get user id using own credentials, and set userReference attribute

        Returns:
            str: the user AAP reference as a string
        """

        # defining URL
        url = "https://explore.api.aai.ebi.ac.uk/users/%s" % (self.name)

        logger.debug("Getting info from %s" % (url))

        # defining my attributes. Headers are inherited
        self.last_response = self.request(url, headers=self.headers)
        self.last_status_code = self.last_response.status_code

        # parsing response and setting self.data
        self.parse_response(self.last_response)

        # returning user id
        return self.userReference

    def get_user_by_id(self, user_id):
        """Get a :py:class:`User` object by user_id

        Args:
            user_id (str): the required user_id

        Returns:
            User: a user object
        """

        # defining URL
        url = "https://explore.api.aai.ebi.ac.uk/users/%s" % (user_id)

        logger.debug("Getting info from %s" % (url))

        # defining my attributes. Headers are inherited
        self.last_response = self.request(url, headers=self.headers)
        self.last_status_code = self.last_response.status_code

        # create a new user obj
        user = User(self.auth, self.last_response.json())

        # returning user
        return user

    @classmethod
    def create_user(cls, user, password, confirmPwd, email, full_name,
                    organisation):
        """Create another user into biosample AAP and return its ID

        Args:
            user (str): the new username
            password (str): the user password
            confirmPwd (str): the user confirm password
            email (str): the user email
            full_name (str): Full name of the user
            organization (str): organization name

        Returns:
            str: the new user_id as a string
        """

        # check that passwords are the same
        if password != confirmPwd:
            raise RuntimeError("passwords don't match!!!")

        # the AAP url
        url = "https://explore.api.aai.ebi.ac.uk/auth"

        # define a new header
        headers = {}

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        # TODO: use more informative parameters
        data = {
            "username": user,
            "password": password,
            "confirmPwd": confirmPwd,
            "email": email,
            "name": full_name,
            "organisation": organisation
        }

        # call a post method a deal with response
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # returning user id
        return response.text

    def create_team(self, description, centreName):
        """Create a new team

        Args:
            description (str): team description
            centreName (str): team center name

        Returns:
            Team: the new team as a :py:class:`Team` instance
        """

        url = "https://submission-test.ebi.ac.uk/api/user/teams"

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        data = {
            "description": description,
            "centreName": centreName
        }

        # call a post method a deal with response
        response = self.post(url, payload=data, headers=headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 201:
            raise ConnectionError(response.text)

        # If I create a new team, the Auth object need to be updated
        logger.warning(
            "You need to generate a new token in order to see the new "
            "generated team")

        # create a new team object
        team = Team(self.auth, response.json())

        return team

    def get_teams(self):
        """Get teams belonging to this instance

        Returns:
            list: a list of :py:class:`Team` objects
        """

        url = "https://submission-test.ebi.ac.uk/api/user/teams"

        response = self.request(url, headers=self.headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # create a new document
        document = Document(auth=self.auth)
        document.parse_response(response, force=True)

        # a list ob objects to return
        teams = []

        # now iterate over teams and create new objects
        for i, team_data in enumerate(document._embedded['teams']):
            teams.append(Team(self.auth, team_data))
            logger.debug("Found %s team" % (teams[i].name))

        return teams

    def get_team_by_name(self, team_name):
        """Get a team by name

        Args:
            team_name (str): the required team

        Returns:
            Team: the desidered :py:class:`Team` instance
        """
        logger.debug("Searching for %s" % (team_name))

        # get all teams
        teams = self.get_teams()

        for team in teams:
            if team.name == team_name:
                return team

        # if I arrive here, no team is found
        raise NameError("team: {team} not found".format(team=team_name))

    def get_domains(self):
        """Get domains belonging to this instance

        Returns:
            list: a list of :py:class:`Domain` objects
        """

        url = "https://explore.api.aai.ebi.ac.uk/my/domains"

        response = self.request(url, headers=self.headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # a list of objects to return
        domains = []

        # iterate over domains
        for i, domain_data in enumerate(response.json()):
            domains.append(Domain(self.auth, domain_data))
            logger.debug("Found %s domain" % (domains[i].name))

        return domains

    def get_domain_by_name(self, domain_name):
        """Get a domain by name

        Args:
            domain_name (str): the required team

        Returns:
            Domain: the desidered :py:class:`Domain` instance
        """

        logger.debug("Searching for %s" % (domain_name))

        # get all domains
        domains = self.get_domains()

        for domain in domains:
            if domain.domainName == domain_name:
                return domain

        # if I arrive here, no team is found
        raise NameError("domain: {domain} not found".format(
            domain=domain_name))

    def add_user_to_team(self, user_id, domain_id):
        """Add a user to a team

        Args:
            user_id (str): the required user_id
            domain_id (str) the required domain_id

        Returns:
            Domain: the updated :py:class:`Domain` object"""

        url = (
            "https://explore.api.aai.ebi.ac.uk/domains/{domain_id}/"
            "{user_id}/user".format(
                domain_id=domain_id,
                user_id=user_id)
        )

        response = self.put(url, headers=self.headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

        domain_data = response.json()
        return Domain(self.auth, domain_data)


class Domain(Document):
    """
    A class to deal with AAP domain objects

    Attributes:
        name (str): domain name
        data (dict): data (dict): data from AAP read with
            :py:meth:`response.json() <requests.Response.json>`
        domainName (str): AAP domainName
        domainDesc (str): AAP domainDesc
        domainReference (str): AAP domainReference
        link (dict): ``links`` data read from AAP response
    """

    def __init__(self, auth, data=None):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object
            data (dict): instantiate the class from a dictionary of user data
        """

        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.data = None

        # other attributes
        self.domainName = None
        self.domainDesc = None
        self.domainReference = None
        self.links = None
        self._users = None

        # dealing with this type of documents.
        if data:
            logger.debug("Reading data for team")
            self.read_data(data)

            # this class lacks of a name attribute, so
            self.name = self.domainName

    def __str__(self):
        if not self.domainReference:
            return "domain not yet initialized"

        reference = self.domainReference.split("-")[1]
        return "%s %s %s" % (reference, self.name, self.domainDesc)

    @property
    def users(self):
        """Get users belonging to this domain"""

        if not self._users and isinstance(self.links, list):
            for url in self.links:
                if 'user' in url['href']:
                    response = self.request(url['href'])
                    break

            tmp_data = response.json()

            # parse users as User objects
            self._users = []

            for user_data in tmp_data:
                self._users.append(User(self.auth, data=user_data))

        return self._users

    @users.setter
    def users(self, value):
        self._users = value

    def create_profile(self, attributes={}):
        """Create a profile for this domain

        Args:
            attributes (dict): a dictionary of attributes
        """

        # see this url for more information
        # https://explore.api.aai.ebi.ac.uk/docs/profile/index.html#resource-create_domain_profile
        url = "https://explore.api.aai.ebi.ac.uk/profiles"

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        # define data
        data = {
            "domain": {
                "domainReference": self.domainReference
            },
            "attributes": attributes
        }

        # call a post method a deal with response
        response = self.post(url, payload=data, headers=headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 201:
            raise ConnectionError(response.text)


class Team(Document):
    """A class to deal with USI Team_ objects

    Attributes:
        name (str): team name
        data (dict): data (dict): data from USI read with
            :py:meth:`response.json() <requests.Response.json>`

    .. _Team: https://submission-test.ebi.ac.uk/api/docs/ref_teams.html
    """
    def __init__(self, auth, data=None):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object
            data (dict): instantiate the class from a dictionary of user data
        """

        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.name = None
        self.data = None
        self.description = None
        self.profile = None

        # dealing with this type of documents.
        if data:
            logger.debug("Reading data for team")
            self.read_data(data)

    def __str__(self):
        return self.name

    def get_submissions(self, status=None):
        """Follows submission url and get submissions from this team

        Args:
            status (str): filter submission using status

        Returns:
            list: A list of :py:class:`Submission` objects"""

        # follow url
        document = self.follow_url('submissions', auth=self.auth)

        # a list ob objects to return
        submissions = []

        # now iterate over teams and create new objects
        for i, submission_data in enumerate(document._embedded['submissions']):
            submission = Submission(self.auth, submission_data)

            if status and submission.status != status:
                logger.debug("Filtering %s submission" % (submission.name))
                continue

            submissions.append(submission)
            logger.debug("Found %s submission" % (submission.name))

        # check if I have submission
        if len(submissions) == 0:
            logger.warning("You haven't any submission yet!")

        return submissions

    def create_submission(self):
        """Create a new submission

        Returns:
            Submission: the new submission as an instance"""

        # get the url for submission:create. I don't want a document using
        # get method, I need instead a POST request
        url = self._links['submissions:create']['href']

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        # call a post method a deal with response
        response = self.post(url, payload={}, headers=headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 201:
            raise ConnectionError(response.text)

        # create a new document
        submission = Submission(auth=self.auth)
        submission.parse_response(response)

        # there are some difference between a new submission and
        # an already defined submission
        logger.debug("reload submission to fix issues")

        # calling this method will reload submission and its status
        submission.reload()

        return submission


class Submission(Document):
    """A class to deal with USI Submissions_

    Attributes:
        id (str): submission id (:py:meth:`~name` for compatibility)
        createdDate (str): created date
        lastModifiedDate (str): last modified date
        lastModifiedBy (str): last user_id who modified this submission
        submissionStatus (str): submission status
        submitter (dict): submitter data
        createdBy (str):  user_id who create this submission
        submissionDate (str): date when this submission is submitted to
            biosample

    .. _Submissions: https://submission-test.ebi.ac.uk/api/docs/ref_submissions.html
    """  # noqa

    def __init__(self, auth, data=None):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object
            data (dict): instantiate the class from a dictionary of user data
        """

        # this will track submission name
        self.id = None

        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self._team = None
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
        if not self.name:
            return "Submission not yet initialized"

        return "%s %s %s" % (self.name, self.team, self.status)

    # for compatibility
    @property
    def name(self):
        """Get/Set Submission :py:attr:`~id`"""

        return self.id

    @name.setter
    def name(self, submission_id):
        if submission_id != self.id:
            logger.warning(
                    "Overriding id (%s > %s)" % (self.id, submission_id))

        self.id = submission_id

    @property
    def team(self):
        """Get/Set team name"""

        # get team name
        if isinstance(self._team, str):
            team_name = self._team

        elif isinstance(self._team, dict):
            team_name = self._team['name']

        elif self._team is None:
            team_name = ""

        else:
            raise NotImplementedError(
                "Unknown type: %s" % type(self._team)
            )

        return team_name

    @team.setter
    def team(self, value):
        self._team = value

    def read_data(self, data, force=False):
        """Read data from a dictionary object and set class attributes

        Args:
            data (dict): a data dictionary object read with
                :py:meth:`response.json() <requests.Response.json>`
            force (bool): If True, define a new class attribute from data keys
        """

        logger.debug("Reading data for submission")
        super().read_data(data, force)

        # check for name
        if 'self' in self._links:
            name = self._links['self']['href'].split("/")[-1]

            # remove {?projection} name
            if '{?projection}' in name:
                logger.debug("removing {?projection} from name")
                name = name.replace("{?projection}", "")

            logger.debug("Using %s as submission name" % (name))
            self.name = name

    def __check_relationship(self, sample_data):
        """Check relationship and add additional fields"""

        # create a copy of sample_data
        sample_data = copy.copy(sample_data)

        # check relationship if exists
        if 'sampleRelationships' not in sample_data:
            return sample_data

        for relationship in sample_data['sampleRelationships']:
            if 'team' not in relationship:
                logger.debug("Adding %s to relationship" % (self.team))
                # setting the referenced object
                relationship['team'] = self.team

        # this is the copied sample_data, not the original one!!!
        return sample_data

    def check_ready(self):
        """Test if a submission can be submitted or not (Must have completed
        validation processes)

        Returns:
            bool: True if ready for submission
        """

        # Try to determine url manually
        url = (
            "https://submission-test.ebi.ac.uk/api/submissions/"
            "{submission_name}/availableSubmissionStatuses".format(
                submission_name=self.name)
        )

        # read a url in a new docume nt
        document = Document.read_url(self.auth, url)

        if hasattr(document, "_embedded"):
            if 'statusDescriptions' in document._embedded:
                return True

        # default response
        return False

    @property
    def status(self):
        """Return :py:attr:`~submissionStatus` attribute. Follow
        ``submissionStatus`` link and update attribute is such attribute is
        None

        Returns:
            str: submission status as a string"""

        if self.submissionStatus is None:
            self.update_status()

        return self.submissionStatus

    def update_status(self):
        """Update :py:attr:`~submissionStatus` attribute by following
        ``submissionStatus`` link"""

        document = self.follow_url('submissionStatus', auth=self.auth)
        self.submissionStatus = document.status

    def create_sample(self, sample_data):
        """Create a sample from a dictionary

        Args:
            sample_data (dict): a dictionary of data

        Returns:
            Sample: a :py:class:`Sample` object"""

        # check sample_data for required attributes
        sample_data = self.__check_relationship(sample_data)

        # debug
        logger.debug(sample_data)

        # get the url for sample create
        document = self.follow_url("contents", auth=self.auth)

        # get the url for submission:create. I don't want a document using
        # get method, I need instead a POST request
        url = document._links['samples:create']['href']

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        # call a post method a deal with response
        response = self.post(url, payload=sample_data, headers=headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 201:
            raise ConnectionError(response.text)

        # create a new sample
        sample = Sample(auth=self.auth)
        sample.parse_response(response)

        # returning sample as and object
        return sample

    def get_samples(self, validationResult=None, has_errors=None,
                    ignorelist=[]):
        """Returning all samples as a list. Can filter by errors and error
        types::

            submission.get_samples(has_errors=True, ignorelist=['Ena'])

        Get all sample with errors in other fields than *Ena* databank

        Args:
            validationResult (str): filter samples by this key
            has_errors (bool): filter samples with errors or none
            ingnore_list (list): a list of errors to ignore
        """

        # get sample url in one step
        self_url = self._links['self']['href']
        samples_url = "/".join([self_url, "contents/samples"])

        # read a new documen
        document = Document.read_url(self.auth, samples_url)

        # a list ob objects to return
        samples = []

        # empty submission hasn't '_embedded' key
        if '_embedded' not in document.data:
            return samples

        for i, sample_data in enumerate(document.data['_embedded']['samples']):
            sample = Sample(self.auth, sample_data)

            if (validationResult and
                    sample.get_validation_result().validationStatus
                    != validationResult):
                logger.debug("Filtering %s sample" % (sample))
                continue

            if has_errors and has_errors != sample.has_errors(ignorelist):
                logger.debug("Filtering %s sample" % (sample))
                continue

            samples.append(sample)
            logger.debug("Found %s sample" % (sample))

        logger.info("Got %s samples" % len(samples))

        return samples

    def get_validation_results(self):
        """Return validation results for submission

        Returns:
            list: a list of :py:class:`ValidationResult` objects"""

        # deal with different subission instances
        if 'validationResults' not in self._links:
            logger.warning("reloading submission")
            self.reload()

        document = self.follow_url('validationResults', auth=self.auth)

        # a list ob objects to return
        validation_results = []

        for i, validation_data in enumerate(
                document.data['_embedded']['validationResults']):
            validation_results.append(
                ValidationResult(self.auth, validation_data))
            logger.debug("Found %s sample" % (str(validation_results[i])))

        logger.debug("Got %s validation results" % len(validation_results))

        return validation_results

    def get_status(self):
        """Count validation statues for submission

        Returns:
            collections.Counter: A counter object for different validation
            status"""

        # get validation results
        validations = self.get_validation_results()

        # get statuses
        statuses = [validation.validationStatus for validation in validations]

        return collections.Counter(statuses)

    # there are errors that could be ignored
    def has_errors(self, ignorelist=[]):
        """Count sample errors for a submission

        Args:
            ignorelist (list): ignore samples with errors in these databanks

        Returns:
            collections.Counter: A counter object for samples with errors and
            with no errors"""

        # check errors only if validation is completed
        if 'Pending' in self.get_status():
            raise RuntimeError(
                "You can check errors after validation is completed")

        # get validation results
        validations = self.get_validation_results()

        # get errors
        errors = [
            validation.has_errors(ignorelist) for validation in validations]

        return collections.Counter(errors)

    def delete(self):
        """Delete this submission instance from USI"""

        url = self._links['self:delete']['href']
        logger.info("Removing submission %s" % self.name)

        response = Client.delete(self, url)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 204:
            raise ConnectionError(response.text)

        # don't return anything

    def reload(self):
        """call :py:meth:`Document.follow_self_url` and reload class
        attributes"""

        logger.info("Refreshing data data for submission")
        self.follow_self_url()

        # reload submission status
        self.update_status()

    def finalize(self, ignorelist=[]):
        """Finalize a submission to insert data into biosample

        Args:
            ignorelist (list): ignore samples with errors in these databanks

        Returns:
            Document: output of finalize submission as a :py:class:`Document`
            object
        """

        if not self.check_ready():
            raise Exception("Submission not ready for finalization")

        # raise exception if submission has errors
        if True in self.has_errors(ignorelist):
            raise Exception("Submission has errors, fix them")

        # refresh my data
        self.reload()

        document = self.follow_url('submissionStatus', self.auth)

        # get the url to change
        url = document._links['submissionStatus']['href']

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        response = self.put(
            url,
            payload={'status': 'Submitted'},
            headers=headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # create a new document
        document = Document(auth=self.auth)
        document.parse_response(response, force=True)

        # copying last responsponse in order to improve data assignment
        logger.debug("Assigning %s to document" % (response))

        document.last_response = response
        document.last_status_code = response.status_code

        # update submission status
        self.update_status()

        return document


class Sample(Document):
    """A class to deal with USI Samples_

    Attributes:
        alias (str): The sample alias (used to reference the same object)
        team (dict): team data
        title (str): sample title
        description (str): sample description
        attributes (dict): sample attributes
        sampleRelationships (list): relationship between samples
        taxonId (int): taxon id
        taxon (str): taxon name
        releaseDate (str): when this sample will be relased to public
        createdDate (str): created date
        lastModifiedDate (str): last modified date
        createdBy (str):  user_id who create this sample
        lastModifiedBy (str): last user_id who modified this sample
        accession (str): the biosample_id after submission to USI

    .. _Samples: https://submission-test.ebi.ac.uk/api/docs/ref_samples.html
    """

    def __init__(self, auth, data=None):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object
            data (dict): instantiate the class from a dictionary of user data
        """

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
        """Read data from a dictionary object and set class attributes

        Args:
            data (dict): a data dictionary object read with
                :py:meth:`response.json() <requests.Response.json>`
            force (bool): If True, define a new class attribute from data keys
        """

        logger.debug("Reading data for Sample")
        super().read_data(data, force)

        # check for name
        if 'self' in self._links:
            self.name = self._links['self']['href'].split("/")[-1]
            logger.debug("Using %s as sample name" % (self.name))

    def delete(self):
        """Delete this instance from a submission"""

        url = self._links['self:delete']['href']
        logger.info("Removing sample %s from submission" % self.name)

        response = Client.delete(self, url)

        if response.status_code != 204:
            raise ConnectionError(response.text)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        # don't return anything

    def reload(self):
        """call :py:meth:`Document.follow_self_url` and reload class
        attributes"""

        logger.info("Refreshing data data for sample")
        self.follow_self_url()

    def patch(self, sample_data):
        """Update sample by patching data with :py:meth:`Client.patch`

        Args:
            sample_data (dict): sample data to update"""

        url = self._links['self']['href']
        logger.info("patching sample %s with %s" % (self.name, sample_data))

        response = Client.patch(self, url, payload=sample_data)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # reloading data
        self.reload()

    def get_validation_result(self):
        """Return validation results for submission

        Returns:
            ValidationResult: the :py:class:`ValidationResult` of this sample
        """

        document = self.follow_url(
            'validationResult',
            auth=self.auth,
            force=True)

        return ValidationResult(self.auth, document.data)

    # there are errors that could be ignored
    def has_errors(self, ignorelist=[]):
        """Return True if validation results throw an error

        Args:
            ignorelist (list): ignore errors in these databanks

        Returns:
            bool: True if sample has an errors in one or more databank"""

        validation = self.get_validation_result().has_errors(ignorelist)

        if validation:
            logger.error("Got error(s) for %s" % (self))

        return validation


class ValidationResult(Document):
    def __init__(self, auth, data=None):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object
            data (dict): instantiate the class from a dictionary of user data
        """

        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
        self.errorMessages = None
        self.overallValidationOutcomeByAuthor = None
        self.validationStatus = None

        if data:
            self.read_data(data)

    def __str__(self):
        message = self.validationStatus

        if self.overallValidationOutcomeByAuthor:
            message += " %s" % (str(self.overallValidationOutcomeByAuthor))

        return message

    # there are errors that could be ignored
    def has_errors(self, ignorelist=[]):
        """Return True if validation has errors

        Args:
            ignorelist (list): ignore errors in these databanks

        Returns:
            bool: True if sample has errors for at least one databank"""

        has_errors = False

        for key, value in self.overallValidationOutcomeByAuthor.items():
            if value == 'Error' and key not in ignorelist:
                message = ", ".join(self.errorMessages[key])
                logger.error(message)
                has_errors = True

        return has_errors
