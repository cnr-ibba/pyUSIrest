#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 16:44:49 2020

@author: Paolo Cozzi <paolo.cozzi@ibba.cnr.it>
"""


class TokenExpiredError(RuntimeError):
    """Raised when token expires while using pyUSIrest"""


class NotReadyError(RuntimeError):
    """Raised when doing stuff on not ready data (ex finalizing a Submission
    after validation)"""


class USIConnectionError(ConnectionError):
    """Deal with connection issues with API"""


class USIDataError(Exception):
    """Deal with issues in USI data format"""
