#!/usr/bin/python
"""Tests for jss wrapper."""

from nose.tools import *
from jss import *
import subprocess
import base64


def setup():
    #j = JSS(repoUrl, authUser, authPass)
    pass


def std_jss():
    jp = JSSPrefs()
    j = JSS(jss_prefs=jp)
    return j


def test_jssprefs():
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


def test_jssprefs_missing_key_error():
    assert_raises(JSSPrefsMissingKeyError, JSSPrefs, '/nonexistent_path')


def test_jss_with_jss_prefs():
    jp = JSSPrefs()
    j = JSS(jss_prefs=jp)
    assert_is_instance(j, JSS)


def test_jss_with_args():
    authUser = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_user'])
    authPass = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_pass'])
    repoUrl = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_url'])
    j = JSS(url=repoUrl, user=authUser, password=authPass)
    assert_is_instance(j, JSS)


def test_jss_password_user_change():
    j = std_jss()
    password = 'DonkeyTacos'
    user = 'Muleboy'
    j.password(password)
    assert(j._password == password)
    j.user(user)
    assert(j._user == user)
    auth = base64.encodestring('%s:%s' %
                              (user, password)).replace('\n', '')
    assert(j.auth == auth)


def test_jss_auth_error():
    j = std_jss()
    j.password('DonkeyTacos')
    assert_raises(JSSAuthenticationError, j.raw_get, '/policies')


def test_jss_raw_get_error():
    j = std_jss()
    assert_raises(JSSGetError, j.raw_get, '/donkey-tacos')


def test_jss_policy():
    j = std_jss()
    ps = j.Policy()
    print(ps)
    assert_is_instance(ps, list)
    idn = ps[0].__dict__['data'].find('id').text
    p = j.Policy(idn)
    assert_is_instance(p, Policy)
    p.pprint()
