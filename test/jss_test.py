#!/usr/bin/env python
"""Tests for jss wrapper.
For test to succeed, you need to set up a preferences file at:
~/Library/Preferences/org.da.jss_helper.plist

Create a plist file with the API username and password like so:
defaults write org.da.jss_helper jss_user <username>
defaults write org.da.jss_helper jss_pass <password>
defaults write org.da.jss_helper jss_url <URL to JSS>

"""

import subprocess
import base64
from xml.etree import ElementTree

from nose.tools import *

from jss import *


def setup():
    global j_global
    jp = JSSPrefs()
    j_global = JSS(jss_prefs=jp)


def test_jssprefs():
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


#@with_setup(setup)
#def test_jss_auth_error():
#    j_global.password = 'DonkeyTacos'
#    assert_raises(JSSAuthenticationError, j_global.raw_get, '/policies')


@with_setup(setup)
def test_jss_raw_get_error():
    assert_raises(JSSGetError, j_global.raw_get, '/donkey-tacos')


@with_setup(setup)
def test_jss_post():
    with open('doc/policy_template.xml') as f:
        data  = f.read()

    xml = ElementTree.fromstring(data)
    new_policy = j_global.Policy(xml)
    # If successful, we'll get a new ID number
    assert_is_instance(new_policy.id(), int)
    id_ = new_policy.id()

    new_policy.delete()


@with_setup(setup)
def test_jss_put():
    with open('doc/policy_template.xml') as f:
        data = f.read()

    xml = ElementTree.fromstring(data)
    new_policy = j_global.Policy(xml)
    id_ = new_policy.id()

    # Change the policy.
    recon = new_policy.xml.find('maintenance/recon')
    # This is str, not bool...
    recon.text = 'false'
    new_policy.update()

    test_policy = j_global.Policy(id_)
    assert_equal(test_policy.xml.find('maintenance/recon').text, 'false')

    new_policy.delete()


@with_setup(setup)
def test_jss_delete():
    with open('doc/policy_template.xml') as f:
        data = f.read()
    xml = ElementTree.fromstring(data)
    new_policy = j_global.Policy(xml)
    id_ = new_policy.id()

    # Test delete. This is of course successful if the previous two tests
    # pass.
    new_policy.delete()
    assert_raises(JSSGetError, j_global.Policy, id_)


#JSSObject Tests###############################################################


@with_setup(setup)
def jss_object_runner(object_cls):
    """ Helper function to test individual object classes. Does not test the
    JSS methods for creating these objects.

    """
    obj_list = j_global.list(object_cls)
    print(obj_list)
    assert_is_instance(obj_list, list)
    # There should be objects in the JSS to test for.
    assert_greater(len(obj_list), 0)
    id_ = int(obj_list[0]['id'])
    obj = object_cls(j_global, id_)
    # This kind_of tests for success, in that it creates an object. The test
    # would fail without the assertion if there was just an exception, but I
    # don't know how to better test this, yet.
    assert_is_instance(obj, object_cls)
    print(type(obj.xml))
    assert_is_instance(obj.xml, ElementTree.Element)
    obj.pprint()


def jss_object_tests():
    # This is a list of all of the JSSObject classes we want to test.
    objs = [Category, Computer, ComputerGroup, Policy, MobileDevice,
            MobileDeviceConfigurationProfile, MobileDeviceGroup]
    for obj in objs:
        jss_object_runner(obj)

@with_setup(setup)
def jss_method_not_allowed_tests():
    class NoGetObject(JSSObject):
        can_get = False

    assert_raises(JSSMethodNotAllowedError, j_global._get_list_or_object,
                  NoGetObject, None)

    class NoPostObject(JSSObject):
        can_post = False

    bad_xml = ElementTree.fromstring("<xml>No workie.</xml>")
    assert_raises(JSSMethodNotAllowedError, j_global._get_list_or_object,
                  NoPostObject, bad_xml)

    # Need to create an existing object first, and it's not implemented yet.
    #class NoPutObject(JSSObject):
    #    can_put = False

    #assert_raises(JSSMethodNotAllowedError, j_global._get_list_or_object,
    #NoPutObject, "<xml>No workie.</xml>")

    class NoDeleteObject(JSSObject):
        can_delete = False
        def __init__(self):
            pass
    nd = NoDeleteObject()

    assert_raises(JSSMethodNotAllowedError, nd.delete)

    ac = ActivationCode(j_global, None)
    assert_raises(JSSMethodNotAllowedError, ac.delete)
