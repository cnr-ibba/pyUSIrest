# -*- coding: utf-8 -*-

"""Top-level package for Python EBI submission REST API."""

__author__ = """Paolo Cozzi"""
__email__ = 'cozzi@ibba.cnr.it'
__version__ = '0.2.0-dev'

from . import auth
from . import client

__all__ = ["auth", "client"]
