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
        jssPrefs = jss.JSSPrefs(
            os.path.expanduser('~/Library/Preferences/com.github.sheagcraig.python-jss-no-repos.plist'))
        assert_is_instance(jssPrefs, jss.JSSPrefs)


class TestDistributionPoints(object):

    def test_creation(self):
        # There's a distribution point included in the JSS object.
        assert_is_instance(j_global.distribution_points, jss.DistributionPoints)

    def test_copying(self):
        # Whoa... Deep.
        filename = 'test/distribution_points_test.py'
        copied_filenames = [
            os.path.join(d.connection['mount_point'], 'Scripts',
                         os.path.basename(filename))
            for d in j_global.distribution_points._children]
        j_global.distribution_points.copy(filename)
        # Cleanup
        for f in copied_filenames:
            assert_true(os.path.exists(f))
            os.remove(f)

class TestMountedRepository(object):

    def test_mounting(self):
        # Of course this only tests the distribution points I have configured.
        test_repo = j_global.distribution_points._children[0]
        mount_point = test_repo.connection['mount_point']
        if os.path.ismount(mount_point):
            test_repo.umount()

        test_repo.mount()
        assert_true(os.path.ismount(mount_point))

    def test_umounting(self):
        # Of course this only tests the distribution points I have configured.
        test_repo = j_global.distribution_points._children[0]
        mount_point = test_repo.connection['mount_point']
        if not os.path.ismount(mount_point):
            mount_point.mount()

        test_repo.umount()
        assert_false(os.path.ismount(mount_point))
