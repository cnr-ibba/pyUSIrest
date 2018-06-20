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

    def put(self, url, payload={}, headers=None):
        """Generic PUT method"""

        headers = self.__check(headers)

        return requests.put(url, json=payload, headers=headers)

    def parse_response(self, response):
        """convert response in a dict"""

        return response.json()

    def follow_link(self, link):
        """Follow link. Calling request and setting attributes"""

        response = self.request(link, headers=self.headers)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

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

    def follow_self_link(self):
        """Follow self link and update class attributes"""

        logger.debug("Following self link")

        # get a link to follow
        link = self._links['self']['href']

        # remove {?projection} from self link. This is unreachible
        if '{?projection}' in link:
            logger.warn("removing {?projection} for link")
            link = link.replace("{?projection}", "")

        # now follow link
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

    def get_user_submissions(self, status=None, team=None):
        """Follow the userSubmission link"""

        # follow link
        document = self.follow_link('userSubmissions', auth=self.auth)

        # a list ob objects to return
        submissions = []

        # now iterate over teams and create new objects
        for i, submission_data in enumerate(document._embedded['submissions']):
            submission = Submission(self.auth, submission_data)

            if status and submission.submissionStatus != status:
                logger.debug("Filtering %s submission" % (submission.name))
                continue

            if team and submission.team != team:
                logger.debug("Filtering %s submission" % (submission.name))
                continue

            submissions.append(submission)
            logger.debug("Found %s submission" % (submission.name))

        logger.info("Got %s submissions" % len(submissions))

        return submissions


# TODO: need this class be placed in auth module?
class User(Document):
    def __init__(self, auth, data=None):
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

        # dealing with this type of documents.
        # TODO: can a user have data?
        if data:
            raise NotImplementedError("Not yet implemented")

    def get_my_id(self):
        """Get user id using own credentials"""

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

    @classmethod
    def create_user(cls, user, password, confirmPwd, email, full_name,
                    organization="IMAGE"):
        """Create another user into biosample AAP and return its ID"""

        # check that passwords are the same
        if password != confirmPwd:
            raise RuntimeError("passwords don't match!!!")

        # TODO: set url as a class attribute
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
            "organisation": organization
        }

        # call a post method a deal with response
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # returning user id
        return response.text

    def create_team(self, description, centreName="IMAGE Inject"):
        """Create a team"""

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

        # TODO: If I create a new team, the Auth object need to be updated
        logger.warn(
            "You need to generate a new token in order to see the new "
            "generated team")

        # create a new team object
        team = Team(self.auth, response.json())

        return team

    def get_teams(self):
        """Get teams of which I'm a member"""

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

    def get_domains(self):
        """Get my domains"""

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
        logger.debug("Searching for %s" % (domain_name))

        # get all domains
        domains = self.get_domains()

        for domain in domains:
            if domain.domainName == domain_name:
                return domain

        # if I arrive here, no team is found
        raise NameError("domain: {domain} not found".format(
            domain=domain_name))

    # TODO: starts from a user instance and from a domain instance
    def add_user_to_team(self, user_id, domain_id):
        """Add a user to a team"""

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
    def __init__(self, auth, data=None):
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
        self.users = None

        # dealing with this type of documents.
        if data:
            logger.debug("Reading data for team")
            self.read_data(data)

            # this class lacks of a name attribute, so
            self.name = self.domainName

    def create_profile(self, attributes={"centre name": "IMAGE Inject team"}):
        """Create profile for this domain"""

        # see this link for more information
        # (https://explore.api.aai.ebi.ac.uk/docs/profile/index.html#resource-create_domain_profile"""
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

    # TODO: filter submission using Status
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

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 201:
            raise ConnectionError(response.text)

        # create a new document
        submission = Submission(auth=self.auth)
        submission.parse_response(response)

        # reload self link to fix issues
        submission.follow_self_link()

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

    def __check_relationship(self, sample_data):
        """Check relationship and add additional fields"""

        # create a copy of sample_data
        sample_data = copy.copy(sample_data)

        # check relationship if exists
        if 'sampleRelationships' not in sample_data:
            return sample_data

        # get team name
        if isinstance(self.team, str):
            team_name = self.team

        elif isinstance(self.team, dict):
            team_name = self.team['name']

        else:
            raise NotImplementedError(
                "Unknown type: %s" % type(self.team)
            )

        for relationship in sample_data['sampleRelationships']:
            if 'team' not in relationship:
                logger.debug("Adding %s to relationship" % (team_name))
                # setting the referenced object
                relationship['team'] = team_name

        # this is the copied sample_data, not the original one!!!
        return sample_data

    def create_sample(self, sample_data):
        """Create a sample"""

        # check sample_data for required attributes
        sample_data = self.__check_relationship(sample_data)

        # debug
        logger.debug(sample_data)

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

    # TODO: filter samples by status
    def get_samples(self):
        """returning all samples as a list"""

        # deal with different subission instances
        if 'contents' not in self._links:
            logger.warn("reloading submission")
            self.reload()

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

    def get_validation_results(self):
        """Return validation results for submission"""

        # deal with different subission instances
        if 'validationResults' not in self._links:
            logger.warn("reloading submission")
            self.reload()

        document = self.follow_link('validationResults', auth=self.auth)

        # a list ob objects to return
        validation_results = []

        for i, validation_data in enumerate(
                document.data['_embedded']['validationResults']):
            validation_results.append(
                ValidationResult(self.auth, validation_data))
            logger.debug("Found %s sample" % (str(validation_results[i])))

        logger.info("Got %s validation results" % len(validation_results))

        return validation_results

    def delete(self):
        """Delete this instance from a submission"""

        link = self._links['self:delete']['href']
        logger.info("Removing submission %s" % self.name)

        response = Client.delete(self, link)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 204:
            raise ConnectionError(response.text)

        # don't return anything

    def reload(self):
        """refreshing data"""

        logger.info("Refreshing data data for submission")
        self.follow_self_link()

    def finalize(self):
        """Finalize a submission to insert data into biosample"""

        # follow self link to reload my data
        self.follow_self_link()

        document = self.follow_link('submissionStatus', self.auth)

        # get the link to change
        link = document._links['submissionStatus']['href']

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        response = self.patch(
            link,
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

        return document


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
        self.follow_self_link()

    def patch(self, sample_data):
        """Patch a sample"""

        link = self._links['self']['href']
        logger.info("patching sample %s with %s" % (self.name, sample_data))

        response = Client.patch(self, link, payload=sample_data)

        # assign attributes
        self.last_response = response
        self.last_status_code = response.status_code

        if response.status_code != 200:
            raise ConnectionError(response.text)

        # reloading data
        self.reload()


class ValidationResult(Document):
    def __init__(self, auth, data=None):
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
        return self.validationStatus
