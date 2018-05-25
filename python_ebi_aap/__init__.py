# -*- coding: utf-8 -*-

"""Top-level package for Python EBI AAP."""

__author__ = """Paolo Cozzi"""
__email__ = 'cozzi@ibba.cnr.it'
__version__ = '0.1.0'

from .auth import Auth
from .client import Client

__all__ = ["Auth", "Client"]
