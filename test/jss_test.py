#!/usr/bin/python
"""Tests for jss wrapper."""

from nose.tools import *
from jss import *


def setup():
    #j = JSS(repoUrl, authUser, authPass)
    pass


def test_jss_auth_error():
    j = JSS(repoUrl, authUser, 'badPassword')
    assert_raises(JSSAuthenticationError, j.get, '/policies')

#@with_setup(setup)
def test_jss_get_error():
    j = JSS(repoUrl, authUser, authPass)
    assert_raises(JSSGetError, j.get, '/donkey-tacos')
