#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:41:31 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

import copy
import requests
import logging
import datetime
import collections

from url_normalize import url_normalize

from . import settings
from .client import Client, Document
from .exceptions import USIConnectionError, NotReadyError, USIDataError


logger = logging.getLogger(__name__)


class Root(Document):
    """Models the USI API Root_ endpoint

    Attributes:
        api_root (str): The base URL for API endpoints

    .. _Root: https://submission-test.ebi.ac.uk/api/docs/ref_root_endpoint.html
    """

    # define the default url
    api_root = None

    def __init__(self, auth):
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # setting api_root
        self.api_root = settings.ROOT_URL + "/api/"

        # setting things. All stuff is inherithed
        self.get(self.api_root)

    def __str__(self):
        return "Biosample API root at %s" % (self.api_root)

    def get_user_teams(self):
        """Follow userTeams url and returns all teams belonging to user

        Yield:
            Team: a team object
        """

        # follow url
        document = self.follow_tag('userTeams')

        # check if I have submission
        if 'teams' not in document._embedded:
            logger.warning("You haven't any team yet!")
            return

        # now iterate over teams and create new objects
        for document in document.paginate():
            for team_data in document._embedded['teams']:
                team = Team(self.auth, team_data)

                logger.debug("Found %s team" % (team.name))

                # returning teams as generator
                yield team

    def get_team_by_name(self, team_name):
        """Get a :py:class:`Team` object by name

        Args:
            team_name (str): the name of the team

        Returns:
            Team: a team object

        """
        logger.debug("Searching for %s" % (team_name))

        for team in self.get_user_teams():
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
        document = self.follow_tag('userSubmissions')

        # check if I have submission
        if 'submissions' not in document._embedded:
            logger.warning("You haven't any submission yet!")
            return

        # now iterate over submissions and create new objects
        for document in document.paginate():
            for submission_data in document._embedded['submissions']:
                submission = Submission(self.auth, submission_data)

                if status and submission.status != status:
                    logger.debug("Filtering %s submission" % (submission.name))
                    continue

                if team and submission.team != team:
                    logger.debug("Filtering %s submission" % (submission.name))
                    continue

                logger.debug("Found %s submission" % (submission.name))

                yield submission

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

        # create a new submission object
        submission = Submission(self.auth)

        # doing a request
        try:
            submission.get(url)

        except USIDataError as exc:
            if submission.last_status_code == 404:
                # if I arrive here, no submission is found
                raise NameError(
                    "submission: '{name}' not found".format(
                        name=submission_name))

            else:
                raise exc

        return submission


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

    user_url = None

    def __init__(self, auth, data=None):
        """Instantiate the class

        Args:
            auth (Auth): a valid :py:class:`Auth <pyUSIrest.auth.Auth>` object
            data (dict): instantiate the class from a dictionary of user data
        """
        # calling the base class method client
        Client.__init__(self, auth)
        Document.__init__(self)

        # define the base user url
        self.user_url = settings.AUTH_URL + "/users"

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
        url = "%s/%s" % (self.user_url, self.name)

        logger.debug("Getting info from %s" % (url))

        # read url and get my attributes
        self.get(url)

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
        url = "%s/%s" % (self.user_url, user_id)

        logger.debug("Getting info from %s" % (url))

        # create a new user obj
        user = User(self.auth)

        # read url and get data
        user.get(url)

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
            organisation (str): organisation name

        Returns:
            str: the new user_id as a string
        """

        # check that passwords are the same
        if password != confirmPwd:
            raise ValueError("passwords don't match!!!")

        # the AAP url
        url = settings.AUTH_URL + "/auth"

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

        # call a post method a deal with response. I don't need a client
        # object to create a new user
        session = requests.Session()
        response = session.post(url, json=data, headers=headers)

        if response.status_code != 200:
            raise USIConnectionError(response.text)

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

        url = settings.ROOT_URL + "/api/user/teams"

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

        url = settings.ROOT_URL + "/api/user/teams"

        # create a new document
        document = Document(auth=self.auth)
        document.get(url)

        # now iterate over teams and create new objects
        for document in document.paginate():
            for team_data in document._embedded['teams']:
                team = Team(self.auth, team_data)
                logger.debug("Found %s team" % (team.name))

                # returning teams as generator
                yield team

    def get_team_by_name(self, team_name):
        """Get a team by name

        Args:
            team_name (str): the required team

        Returns:
            Team: the desidered :py:class:`Team` instance
        """

        logger.debug("Searching for %s" % (team_name))

        for team in self.get_teams():
            if team.name == team_name:
                return team

        # if I arrive here, no team is found
        raise NameError("team: {team} not found".format(team=team_name))

    def get_domains(self):
        """Get domains belonging to this instance

        Returns:
            list: a list of :py:class:`Domain` objects
        """

        url = settings.AUTH_URL + "/my/domains"

        # make a request with a client object
        response = Client.get(self, url)

        # iterate over domains (they are a list of objects)
        for domain_data in response.json():
            domain = Domain(self.auth, domain_data)
            logger.debug("Found %s domain" % (domain.name))

            # returning domain as a generator
            yield domain

    def get_domain_by_name(self, domain_name):
        """Get a domain by name

        Args:
            domain_name (str): the required team

        Returns:
            Domain: the desidered :py:class:`Domain` instance
        """

        logger.debug("Searching for %s" % (domain_name))

        # get all domains
        for domain in self.get_domains():
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
            "{auth_url}/domains/{domain_id}/"
            "{user_id}/user".format(
                domain_id=domain_id,
                user_id=user_id,
                auth_url=settings.AUTH_URL)
        )

        response = self.put(url)
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
                    # using the base get method
                    response = Client.get(self, url['href'])
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
        url = settings.AUTH_URL + "/profiles"

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

        # create a new domain object
        domain = Domain(self.auth, response.json())

        return domain


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
        return "{0} ({1})".format(self.name, self.description)

    def get_submissions(self, status=None):
        """Follows submission url and get submissions from this team

        Args:
            status (str): filter submission using status

        Returns:
            list: A list of :py:class:`Submission` objects"""

        # follow url
        document = self.follow_tag('submissions')

        # check if I have submission
        if 'submissions' not in document._embedded:
            logger.warning("You haven't any submission yet!")
            return

        # now iterate over submissions and create new objects
        for document in document.paginate():
            for submission_data in document._embedded['submissions']:
                submission = Submission(self.auth, submission_data)

                if status and submission.status != status:
                    logger.debug("Filtering %s submission" % (submission.name))
                    continue

                logger.debug("Found %s submission" % (submission.name))

                yield submission

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

        # create a new Submission object
        submission = Submission(auth=self.auth, data=response.json())

        # there are some difference between a new submission and
        # an already defined submission
        logger.debug("reload submission to fix issues")

        # calling this method will reload submission and its status
        submission.reload()

        return submission


# helper functions
def check_relationship(sample_data, team):
    """Check relationship and add additional fields if missing"""

    # create a copy of sample_data
    sample_data = copy.copy(sample_data)

    # check relationship if exists
    if 'sampleRelationships' not in sample_data:
        return sample_data

    for relationship in sample_data['sampleRelationships']:
        if 'team' not in relationship:
            logger.debug("Adding %s to relationship" % (team))
            # setting the referenced object
            relationship['team'] = team

    # this is the copied sample_data, not the original one!!!
    return sample_data


def check_releasedate(sample_data):
    """Add release date to sample data if missing"""

    # create a copy of sample_data
    sample_data = copy.copy(sample_data)

    # add a default release date if missing
    if 'releaseDate' not in sample_data:
        today = datetime.date.today()
        logger.warning("Adding %s as releasedate")
        sample_data['releaseDate'] = str(today)

    # this is the copied sample_data, not the original one!!!
    return sample_data


class TeamMixin(object):

    def __init__(self):
        """Instantiate the class"""

        # my class attributes
        self._team = None

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


class Submission(TeamMixin, Document):
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
        super().__init__()

        # now setting up Client and document class attributes
        Client.__init__(self, auth)
        Document.__init__(self)

        # my class attributes
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

        return "%s %s %s %s" % (
            self.name,
            self.team,
            self.lastModifiedDate.date(),
            self.status,)

    # for compatibility
    @property
    def name(self):
        """Get/Set Submission :py:attr:`~id`"""

        return self.id

    @name.setter
    def name(self, submission_id):
        if submission_id != self.id:
            logger.debug(
                    "Overriding id (%s > %s)" % (self.id, submission_id))

        self.id = submission_id

    def read_data(self, data, force_keys=False):
        """Read data from a dictionary object and set class attributes

        Args:
            data (dict): a data dictionary object read with
                :py:meth:`response.json() <requests.Response.json>`
            force_keys (bool): If True, define a new class attribute from data
                keys
        """

        logger.debug("Reading data for submission")
        super().read_data(data, force_keys)

        # check for name
        if 'self' in self._links:
            name = self._links['self']['href'].split("/")[-1]

            # remove {?projection} name
            if '{?projection}' in name:
                logger.debug("removing {?projection} from name")
                name = name.replace("{?projection}", "")

            logger.debug("Using %s as submission name" % (name))
            self.name = name

    def check_ready(self):
        """Test if a submission can be submitted or not (Must have completed
        validation processes)

        Returns:
            bool: True if ready for submission
        """

        # Try to determine url manually
        url = (
            "{api_root}/api/submissions/"
            "{submission_name}/availableSubmissionStatuses".format(
                submission_name=self.name,
                api_root=settings.ROOT_URL)
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

        document = self.follow_tag('submissionStatus')
        self.submissionStatus = document.status

    def create_sample(self, sample_data):
        """Create a sample from a dictionary

        Args:
            sample_data (dict): a dictionary of data

        Returns:
            Sample: a :py:class:`Sample` object"""

        # check sample_data for required attributes
        fixed_data = check_relationship(sample_data, self.team)
        fixed_data = check_releasedate(fixed_data)

        # debug
        logger.debug(fixed_data)

        # check if submission has the contents key
        if 'contents' not in self._links:
            # reload submission object in order to add items to it
            self.reload()

        # get the url for sample create
        document = self.follow_tag("contents")

        # get the url for submission:create. I don't want a document using
        # get method, I need instead a POST request
        url = document._links['samples:create']['href']

        # define a new header. Copy the dictionary, don't use the same object
        headers = copy.copy(self.headers)

        # add new element to headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'

        # call a post method a deal with response
        response = self.post(url, payload=fixed_data, headers=headers)

        # create a new sample
        sample = Sample(auth=self.auth, data=response.json())

        # returning sample as and object
        return sample

    def get_samples(self, status=None, has_errors=None,
                    ignorelist=[]):
        """Returning all samples as a list. Can filter by errors and error
        types::

            # returning samples with errors in other checks than Ena
            submission.get_samples(has_errors=True, ignorelist=['Ena'])

            # returning samples which validation is still in progress
            submission.get_samples(status='Pending')

        Get all sample with errors in other fields than *Ena* databank

        Args:
            status (str): filter samples by validation status
                (Pending, Complete)
            has_errors (bool): filter samples with errors or none
            ingnore_list (list): a list of errors to ignore

        Yield:
            Sample: a :py:class:`Sample` object
        """

        # get sample url in one step
        self_url = self._links['self']['href']
        samples_url = "/".join([self_url, "contents/samples"])

        # read a new document
        document = Document.read_url(self.auth, samples_url)

        # empty submission hasn't '_embedded' key
        if '_embedded' not in document.data:
            logger.warning("You haven't any samples yet!")
            return

        # now iterate over samples and create new objects
        for document in document.paginate():
            for sample_data in document._embedded['samples']:
                sample = Sample(self.auth, sample_data)

                if (status and
                        sample.get_validation_result().validationStatus
                        != status):
                    logger.debug("Filtering %s sample" % (sample))
                    continue

                if has_errors and has_errors != sample.has_errors(ignorelist):
                    logger.debug("Filtering %s sample" % (sample))
                    continue

                logger.debug("Found %s sample" % (sample))

                yield sample

    def get_validation_results(self):
        """Return validation results for submission

        Yield:
            ValidationResult: a :py:class:`ValidationResult` object"""

        # deal with different subission instances
        if 'validationResults' not in self._links:
            logger.warning("reloading submission")
            self.reload()

        document = self.follow_tag('validationResults')

        # now iterate over validationresults and create new objects
        for document in document.paginate():
            for validation_data in document._embedded['validationResults']:
                validation_result = ValidationResult(
                    self.auth, validation_data)

                logger.debug("Found %s sample" % (validation_result))

                yield validation_result

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
            raise NotReadyError(
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

        # don't return anything
        Client.delete(self, url)

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
            raise NotReadyError("Submission not ready for finalization")

        # raise exception if submission has errors
        if True in self.has_errors(ignorelist):
            raise USIDataError("Submission has errors, fix them")

        # refresh my data
        self.reload()

        document = self.follow_tag('submissionStatus')

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

        # create a new document
        document = Document(auth=self.auth, data=response.json())

        # copying last responsponse in order to improve data assignment
        logger.debug("Assigning %s to document" % (response))

        document.last_response = response
        document.last_status_code = response.status_code

        # update submission status
        self.update_status()

        return document


class Sample(TeamMixin, Document):
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
        super().__init__()

        # now setting up Client and document class attributes
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

    def read_data(self, data, force_keys=False):
        """Read data from a dictionary object and set class attributes

        Args:
            data (dict): a data dictionary object read with
                :py:meth:`response.json() <requests.Response.json>`
            force_keys (bool): If True, define a new class attribute from data
                keys
        """

        logger.debug("Reading data for Sample")
        super().read_data(data, force_keys)

        # check for name
        if 'self' in self._links:
            self.name = self._links['self']['href'].split("/")[-1]
            logger.debug("Using %s as sample name" % (self.name))

    def delete(self):
        """Delete this instance from a submission"""

        url = self._links['self:delete']['href']
        logger.info("Removing sample %s from submission" % self.name)

        # don't return anything
        Client.delete(self, url)

    def reload(self):
        """call :py:meth:`Document.follow_self_url` and reload class
        attributes"""

        logger.info("Refreshing data data for sample")
        self.follow_self_url()

    def patch(self, sample_data):
        """Update sample by patching data with :py:meth:`Client.patch`

        Args:
            sample_data (dict): sample data to update"""

        # check sample_data for required attributes
        fixed_data = check_relationship(sample_data, self.team)
        fixed_data = check_releasedate(fixed_data)

        url = self._links['self']['href']
        logger.info("patching sample %s with %s" % (self.name, fixed_data))

        super().patch(url, payload=fixed_data)

        # reloading data
        self.reload()

    def get_validation_result(self):
        """Return validation results for submission

        Returns:
            ValidationResult: the :py:class:`ValidationResult` of this sample
        """

        document = self.follow_tag('validationResult', force_keys=True)

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
        self.version = None
        self.expectedResults = None
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
