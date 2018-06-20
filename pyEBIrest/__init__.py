# -*- coding: utf-8 -*-

"""Top-level package for Python EBI submission REST API."""

__author__ = """Paolo Cozzi"""
__email__ = 'cozzi@ibba.cnr.it'
__version__ = '0.1.0'

from .auth import Auth
from .client import (
    Client, Team, Submission, Document, Root, User, Domain, Sample,
    ValidationResult)

__all__ = [
    "Auth", "Client", "Team", "Submission", "Document", "Root", "User",
    "Domain", "Sample", "ValidationResult"]
