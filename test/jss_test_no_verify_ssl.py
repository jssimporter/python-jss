#!/usr/bin/env python
"""Tests for jss wrapper.
These tests will FAIL! A few of the tests assert values local to my
institution. Edit them to work in your environment, or find a better way to do
it and send me an email!

For test to succeed, you need to set up a preferences file at:
~/Library/Preferences/com.github.sheagcraig.python-jss.plist

Create a plist file with the API username and password like so:
defaults write com.github.sheagcraig.python-jss jss_user <username>
defaults write com.github.sheagcraig.python-jss jss_pass <password>
defaults write com.github.sheagcraig.python-jss jss_url <URL to JSS>

The JSS itself does validation on any data passed to it, so for the most part
we are only concerned with testing for interactions between the wrapper
objects.

"""

import subprocess
import inspect
import os.path
from xml.etree import ElementTree

from nose.tools import *

from jss import *
from jss.jssobjectlist import JSSObjectList


# Setup a global JSS object for test usage.
global j_global
prefs = "com.github.sheagcraig.python-jss.test-server.plist"
if is_osx():
    pref_path = os.path.join("~/Library/Preferences", prefs)
elif is_linux():
    pref_path = os.path.join("~", "." + prefs)
else:
    raise Exception("Unknown/unsupported OS.")
jp = JSSPrefs(pref_path)
j_global = JSS(jp, ssl_verify=False)
j_global.ssl_verify = False


TESTPOLICY = 'python-jss Test Policy'
TESTGROUP = 'python-jss Test Group'


def setup():
    """Make sure failed tests that create policies don't hamper our ability
    to continue testing.

    """
    try:
        cleanup = j_global.Policy(TESTPOLICY)
        cleanup.delete()
    except JSSGetError:
        pass
    try:
        cleanup = j_global.ComputerGroup(TESTGROUP)
        cleanup.delete()
    except JSSGetError:
        pass


class TestJSSNoVerifySSL(object):

    def test_jss_get_no_verify(self):
        assert_is_instance(j_global.Policy(), JSSObjectList)

    @with_setup(setup)
    def test_JSS_post_no_verify(self):
        new_policy = Policy(j_global, TESTPOLICY)
        new_policy.save()
        # If successful, we'll get a new ID number
        assert_is_instance(new_policy.id, str)

    def test_JSS_put_no_verify(self):
        # setup() only gets run once if I use the decorator. You're not
        # supposed to use them with classes apparently.
        setup()
        new_policy = Policy(j_global, TESTPOLICY)
        new_policy.save()
        # Second save will do a PUT/update
        put_test = 'PUT test'
        new_policy.find('self_service/self_service_description').text = put_test
        new_policy.save()
        test_policy = j_global.Policy(TESTPOLICY)
        assert_equals(test_policy.find('self_service/self_service_description').text, put_test)
