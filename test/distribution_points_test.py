#!/usr/bin/env python
"""Tests for distribution points.
These tests will FAIL! A few of the tests assert values local to my
institution. Edit them to work in your environment, or find a better way to do
it and send me an email!

"""


from nose.tools import *
import os.path

import jss


global j_global
jp = jss.JSSPrefs()
j_global = jss.JSS(jss_prefs=jp)


class TestJSSPrefs(object):

    def test_jssprefs_no_repos(self):
        # Make sure that if you don't specify any repository information in
        # your preference file, everything still works correctly (just no
        # repos)
        jssPrefs = jss.JSSPrefs(
            os.path.expanduser('~/Library/Preferences/com.github.sheagcraig.python-jss-no-repos.plist'))
        assert_is_instance(jssPrefs, jss.JSSPrefs)
