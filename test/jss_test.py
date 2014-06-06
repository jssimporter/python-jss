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


global j_global
jp = JSSPrefs()
j_global = JSS(jss_prefs=jp)


def setup():
    """Make sure failed tests that create policies don't hamper our ability
    to continue testing.

    """
    try:
        cleanup = j_global.Policy('jss python wrapper API test policy')
        cleanup.delete()
    except JSSGetError:
        pass


class testJSSPrefs(object):

    def test_jssprefs(self):
        jp = JSSPrefs()
        result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_user'])
        assert_in(jp.user, result)
        result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_pass'])
        assert_in(jp.password, result)
        result = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_url'])
        assert_in(jp.url, result)

    def test_jssprefs_missing_file_error(self):
        assert_raises(JSSPrefsMissingFileError, JSSPrefs, '/nonexistent_path')

    def test_jssprefs_missing_key_error(self):
        assert_raises(JSSPrefsMissingKeyError, JSSPrefs, 'test/incomplete_preferences.plist')


class testJSS(object):

    def test_jss_with_jss_prefs(self):
        jp = JSSPrefs()
        j = JSS(jss_prefs=jp)
        assert_is_instance(j, JSS)

    def test_jss_with_args(self):
        authUser = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_user'])
        authPass = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_pass'])
        repoUrl = subprocess.check_output(['defaults', 'read', 'org.da.jss_helper', 'jss_url'])
        j = JSS(url=repoUrl, user=authUser, password=authPass)
        assert_is_instance(j, JSS)

    def test_jss_get_error(self):
        assert_raises(JSSGetError, j_global.get, '/donkey-tacos')

    def test_jss_get(self):
        policy = j_global.get(Policy.get_url(None))
        assert_is_instance(policy, ElementTree.Element)

    @with_setup(setup)
    def test_jss_post(self):
        pt = JSSPolicyTemplate()
        new_policy = j_global.Policy(pt)
        # If successful, we'll get a new ID number
        assert_is_instance(new_policy.id, int)
        new_policy.delete()

    def test_jss_method_constructors(self):
        skip_these_methods = ['__init__', 'get', 'delete', 'put', 'post', '_error_handler']
        method_constructors = [ m[1] for m in inspect.getmembers(j_global) if inspect.ismethod(m[1]) and m[0] not in skip_these_methods]
        for cls in method_constructors:
            instance = cls()
            yield self.check_jss_method_constructor, instance

    def check_jss_method_constructor(self, instance):
            assert_true(isinstance(instance, JSSObject) or isinstance(instance, JSSObjectList))

    @with_setup(setup)
    def test_jss_put(self):
        pt = JSSPolicyTemplate()
        new_policy = j_global.Policy(pt)
        id_ = new_policy.id

        # Change the policy.
        recon = new_policy.find('maintenance/recon')
        # This is str, not bool...
        recon.text = 'false'
        new_policy.update()

        test_policy = j_global.Policy(id_)
        assert_equal(test_policy.find('maintenance/recon').text, 'false')

        new_policy.delete()

    @with_setup(setup)
    def test_jss_delete(self):
        pt = JSSPolicyTemplate()
        new_policy = j_global.Policy(pt)
        # If successful, we'll get a new ID number
        assert_is_instance(new_policy.id, int)
        id_ = new_policy.id

        # Test delete. This is of course successful if the previous two tests
        # pass.
        new_policy.delete()
        assert_raises(JSSGetError, j_global.Policy, id_)


class testJSSObject(object):
    def test_jssobject_unsupported_search_method_error(self):
        assert_raises(JSSUnsupportedSearchMethodError,
                      j_global.Policy, 'taco=alpastor')

    def test_JSSObject_get_url(self):
        assert_equal(Policy.get_url(None), '/policies')
        assert_equal(Policy.get_url(42), '/policies/id/42')
        assert_equal(Policy.get_url('taco'), '/policies/name/taco')
        assert_equal(Computer.get_url('match=taco'), '/computers/match/taco')
        assert_equal(Computer.get_url('udid=taco'), '/computers/udid/taco')

    def test_JSSObject_get_post_url(self):
        assert_equal(Policy.get_post_url(), '/policies/id/0')

    def test_JSSObject_get_object_url(self):
        pt = JSSPolicyTemplate()
        new_policy = j_global.Policy(pt)

        assert_equal(new_policy.get_object_url(), '/policies/id/%s' % 
                     new_policy.id)

        new_policy.delete()

    def test_jssobject_method_not_allowed(self):
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


class testJSSObjectFactory(object):
    def test_JSSObjectFactory_list(self):
        obj_list = j_global.factory.get_object(Policy)
        assert_is_instance(obj_list, JSSObjectList)

    def test_JSSObjectFactory_JSSObject(self):
        obj_list = j_global.factory.get_object(Policy, 242)
        assert_is_instance(obj_list, Policy)


class testJSSDeviceObjects(object):
    def test_JSSDeviceObject_properties(self):
        computer = j_global.Computer('name=craigs-imac')
        assert_equal(computer.udid, '012CDB33-82E1-558F-9F6F-18EAAC05B5AC')
        assert_equal(computer.serial_number, 'D25H40JBDHJV')

    def test_Computer_properties(self):
        computer = j_global.Computer('name=craigs-imac')
        assert_is_instance(computer.mac_addresses, list)
        assert_equal(computer.mac_addresses, ['3C:07:54:6E:8B:14',
                                                '04:54:53:0F:E9:D1'])
        match = j_global.Computer('match=craigs-imac')
        assert_is_instance(match, JSSObjectList)

    def test_MobileDevice_properties(self):
        computer = j_global.MobileDevice('name=Testing iPad - 2')
        assert_equal(computer.wifi_mac_address, '28:6A:BA:11:F0:A3')
        assert_equal(computer.bluetooth_mac_address, '28:6A:BA:11:F0:A4')

class testJSSObject_Subclasses(object):
    def jssobject_runner(self, object_cls):
        """ Helper function to test individual object classes."""
        obj_list = j_global.factory.get_object(object_cls)
        assert_is_instance(obj_list, JSSObjectList)
        # There should be objects in the JSS to test for.
        assert_greater(len(obj_list), 0)
        id_ = obj_list[0].id
        obj = j_global.factory.get_object(object_cls, id_)
        assert_is_instance(obj, object_cls, msg='The object of type %s was not '
                          'expected.' % type(obj))

    def test_container_JSSObject_subclasses(self):
        """Test for factory to return objects of each of our JSSObject
        subclasses that are containers.

        """
        objs = [Category, Computer, ComputerGroup, Policy, MobileDevice,
                MobileDeviceConfigurationProfile, MobileDeviceGroup]
        for obj in objs:
            yield self.jssobject_runner, obj


class testJSSObjectTemplate(object):
    pass


class testJSSListData(object):
    # The methods on JSSListData are indirectly tested in many of the above
    # tests.
    pass


class testJSSObjectList(object):
    def test_retrieve(self):
        computers = j_global.Computer()
        assert_is_instance(computers.retrieve(1), Computer)

    def test_retrieve_by_id(self):
        computers = j_global.Computer()
        search_id = computers[-1].id
        assert_is_instance(computers.retrieve_by_id(search_id), Computer)

    def test_retrieve_all(self):
        # We use policies since they're smaller, and hopefully smaller in
        #number
        policies = j_global.Policy()
        full_policies = policies.retrieve_all()
        assert_is_instance(full_policies, list)
        assert_is_instance(full_policies[1], Policy)

    def test_sort(self):
        policies = j_global.Policy()
        policies.sort()
        first_policy_id = policies[0].id
        sorted = [True for policy in policies if policy.id > first_policy_id]
        assert_not_in(False, sorted)

    def test_sort_by_name(self):
        policies = j_global.Policy()
        policies.sort()
        first_policy_name = policies[0].name
        sorted = [True for policy in policies if policy.name >
                  first_policy_name]
        assert_not_in(False, sorted)
