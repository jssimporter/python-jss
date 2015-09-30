#!/usr/bin/env python
"""Tests for distribution points.
These tests will FAIL! A few of the tests assert values local to my
institution. Edit them to work in your environment, or find a better way to do
it and send me an email!

"""


from nose.tools import *
import os

import jss


global j_global
jp = jss.JSSPrefs()
j_global = jss.JSS(jss_prefs=jp)


class TestJSSPrefs(object):

    def test_jssprefs_no_repos(self):
        # Make sure that if you don't specify any repository information in
        # your preference file, everything still works correctly (just no
        # repos). Of course, needs a preferences file with no repos in it.
        no_repos_prefs = "com.github.sheagcraig.python-jss-no-repos.plist"
        if jss.is_osx():
            pref_path = os.path.join("~/Library/Preferences", no_repos_prefs)
        elif jss.is_linux():
            pref_path = os.path.join("~", "." + no_repos_prefs)
        else:
            raise Exception("Unknown/unsupported OS.")
        jssPrefs = jss.JSSPrefs(pref_path)
        assert_is_instance(jssPrefs, jss.JSSPrefs)


class TestDistributionPoints(object):

    def test_creation(self):
        # There's a distribution point included in the JSS object.
        assert_is_instance(j_global.distribution_points, jss.DistributionPoints)

    def test_copying_script(self):
        # Whoa... Deep.
        filename = 'test/distribution_points_test.py'
        j_global.distribution_points.copy(filename)
        assert_true(j_global.distribution_points.exists(os.path.basename(filename)))
        j_global.distribution_points.delete(os.path.basename(filename))
        j_global.distribution_points.umount()

    def test_copying_pkg(self):
        filename = 'test/distribution_points_test.py.zip'
        j_global.distribution_points.delete(os.path.basename(filename))
        j_global.distribution_points.copy(filename)
        assert_true(j_global.distribution_points.exists(os.path.basename(filename)))
        # This test leaves packages cluttering up the repo.
        # Need to add a delete method...
        j_global.distribution_points.delete(os.path.basename(filename))
        j_global.distribution_points.umount()


class TestMountedRepository(object):

    def test_mounting(self):
        # Of course this only tests the distribution points I have configured.
        test_repo = j_global.distribution_points._children[0]
        if test_repo.is_mounted():
            test_repo.umount()

        test_repo.mount()
        assert_true(test_repo.is_mounted())
        test_repo.umount()

    def test_umounting(self):
        # Of course this only tests the distribution points I have configured.
        test_repo = j_global.distribution_points._children[0]
        # Updates connection information.
        test_repo.is_mounted()
        mount_point = test_repo.connection['mount_point']
        if not os.path.ismount(mount_point):
            test_repo.mount()

        test_repo.umount()
        assert_false(os.path.ismount(mount_point))
