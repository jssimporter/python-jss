#!/usr/bin/python
"""Tests for jss wrapper."""

from nose.tools import *
from jss import *
import subprocess


def setup():
    #j = JSS(repoUrl, authUser, authPass)
    pass


def std_jss():
    jp = JSSPrefs()
    j = JSS(jss_prefs=jp)
    return j


def test_jss_prefs():
    # For test to succeed, you need to set up a preferences file.
    # Create a plist file with the API username and password like so:
    # defaults write org.da.jss_helper jss_user <username>
    # defaults write org.da.jss_helper jss_pass <password>
    # defaults write org.da.jss_helper jss_url <URL to JSS>
    jp = JSSPrefs()
    result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_user'])
    assert_in(jp.user, result)
    result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_pass'])
    assert_in(jp.password, result)
    result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_url'])
    assert_in(jp.url, result)


def test_jss_with_jss_prefs():
    jp = JSSPrefs()
    j = JSS(jss_prefs=jp)
    assert_is_instance(j, JSS)


def test_jss_with_args():
    j = JSS(url=repoUrl, user=authUser, password=authPass)
    assert_is_instance(j, JSS)


def test_jss_auth_error():
    j = JSS(url=repoUrl, user=authUser, password='badPassword')
    assert_raises(JSSAuthenticationError, j.get, '/policies')


def test_jss_get_error():
    j = std_jss()
    assert_raises(JSSGetError, j.get, '/donkey-tacos')
