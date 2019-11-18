# -*- coding: utf-8 -*-

"""Top-level package for Python EBI submission REST API."""

__author__ = """Paolo Cozzi"""
__email__ = 'cozzi@ibba.cnr.it'
__version__ = '0.3.0.dev0'

from . import auth
from . import client
from . import settings

__all__ = ["auth", "client", "settings"]
