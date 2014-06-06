#!/usr/bin/env python
"""Tests for jss wrapper.
For test to succeed, you need to set up a preferences file at:
~/Library/Preferences/org.da.jss_helper.plist

Create a plist file with the API username and password like so:
defaults write org.da.jss_helper jss_user <username>
defaults write org.da.jss_helper jss_pass <password>
defaults write org.da.jss_helper jss_url <URL to JSS>

The JSS itself does validation on any data passed to it, so for the most part
we are only concerned with testing for interactions between the wrapper
objects.

"""

import subprocess
import base64
import inspect
from xml.etree import ElementTree

from nose.tools import *

from jss import *


def setup():
    global j_global
    jp = JSSPrefs()
    j_global = JSS(jss_prefs=jp)
    try:
        cleanup = j_global.Policy('jss python wrapper API test policy')
        cleanup.delete()
    except JSSGetError:
        pass


#JSSPrefs Tests################################################################


def test_jssprefs():
    jp = JSSPrefs()
    result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_user'])
    assert_in(jp.user, result)
    result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_pass'])
    assert_in(jp.password, result)
    result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_url'])
    assert_in(jp.url, result)


def test_jssprefs_missing_file_error():
    assert_raises(JSSPrefsMissingFileError, JSSPrefs, '/nonexistent_path')


def test_jssprefs_missing_key_error():
    assert_raises(JSSPrefsMissingKeyError, JSSPrefs, 'test/incomplete_preferences.plist')


#JSS Tests#####################################################################


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


@with_setup(setup)
def test_jss_get_error():
    assert_raises(JSSGetError, j_global.get, '/donkey-tacos')


@with_setup(setup)
def test_jss_get():
    policy = j_global.get(Policy.get_url(None))
    assert_is_instance(policy, ElementTree.Element)


@with_setup(setup)
def test_jss_post():
    pt = JSSPolicyTemplate()
    new_policy = j_global.Policy(pt)
    # If successful, we'll get a new ID number
    assert_is_instance(new_policy.id(), int)
    new_policy.delete()


@with_setup(setup)
def test_jss_method_constructors():
    skip_these_methods = ['__init__', 'get', 'delete', 'put', 'post', '_error_handler']
    method_constructors = [ m[1] for m in inspect.getmembers(j_global) if inspect.ismethod(m[1]) and m[0] not in skip_these_methods]
    for cls in method_constructors:
        instance = cls()
        assert_true(isinstance(instance, JSSObject) or isinstance(instance, JSSObjectList), msg='The %s was not expected as a type.' % cls)


# These test both JSS methods and JSSObject methods. I don't feel the need to
# write more to cover both.


@with_setup(setup)
def test_jss_put():
    pt = JSSPolicyTemplate()
    new_policy = j_global.Policy(pt)
    id_ = new_policy.id()

    # Change the policy.
    recon = new_policy.find('maintenance/recon')
    # This is str, not bool...
    recon.text = 'false'
    new_policy.update()

    test_policy = j_global.Policy(id_)
    assert_equal(test_policy.find('maintenance/recon').text, 'false')

    new_policy.delete()


@with_setup(setup)
def test_jss_delete():
    pt = JSSPolicyTemplate()
    new_policy = j_global.Policy(pt)
    # If successful, we'll get a new ID number
    assert_is_instance(new_policy.id(), int)
    id_ = new_policy.id()

    # Test delete. This is of course successful if the previous two tests
    # pass.
    new_policy.delete()
    assert_raises(JSSGetError, j_global.Policy, id_)


#JSSObject Tests###############################################################
#TODO: Test methods of JSSObject


#TODO: Move to JSSObject subclasses section
@with_setup(setup)
def jss_object_runner(object_cls):
    """ Helper function to test individual object classes."""
    obj_list = j_global.factory.get_object(object_cls)
    assert_is_instance(obj_list, JSSObjectList)
    # There should be objects in the JSS to test for.
    assert_greater(len(obj_list), 0)
    id_ = obj_list[0].id()
    obj = j_global.factory.get_object(object_cls, id_)
    assert_is_instance(obj, object_cls, msg='The object of type %s was not '
                      'expected.' % type(obj))


def test_container_JSSObject_subclasses():
    """Test for factory to return objects of each of our JSSObject
    subclasses that are containers.

    """
    objs = [Category, Computer, ComputerGroup, Policy, MobileDevice,
            MobileDeviceConfigurationProfile, MobileDeviceGroup]
    for obj in objs:
        jss_object_runner(obj)


@with_setup(setup)
def jss_method_not_allowed_tests():
    # This type of object probably doesn't exist in the wild.
    class NoListObject(JSSObject):
        can_list = False
        can_get = False

    class NoGetObject(JSSObject):
        can_get = False

    class NoPostObject(JSSObject):
        can_post = False

    class NoPutObject(JSSObject):
        can_put = False
        def __init__(self):
            pass

    class NoDeleteObject(JSSObject):
        can_delete = False
        def __init__(self):
            pass

    assert_raises(JSSMethodNotAllowedError, j_global.factory.get_object,
                  NoListObject, None)
    assert_raises(JSSMethodNotAllowedError, j_global.factory.get_object,
                  NoGetObject, None)
    bad_element = ElementTree.fromstring("<xml>No workie.</xml>")
    bad_policy = JSSObjectTemplate(element=bad_element)
    assert_raises(JSSMethodNotAllowedError, j_global.factory.get_object,
                  NoPostObject, bad_policy)

    np = NoPutObject()
    assert_raises(JSSMethodNotAllowedError, np.update)

    nd = NoDeleteObject()
    assert_raises(JSSMethodNotAllowedError, nd.delete)


#JSSObjectFactory Tests########################################################
@with_setup(setup)
def test_JSSObjectFactory_list():
    obj_list = j_global.factory.get_object(Policy)
    assert_is_instance(obj_list, JSSObjectList)


@with_setup(setup)
def test_JSSObjectFactory_JSSObject():
    obj_list = j_global.factory.get_object(Policy, 242)
    assert_is_instance(obj_list, Policy)


#JSSDeviceObject Tests#########################################################

#JSSObject Subclasses Tests####################################################

#JSSObjectTemplate Tests#######################################################

#JSSListData Tests#############################################################

#JSSObjectList Tests###########################################################
