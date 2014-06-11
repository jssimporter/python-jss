#!/usr/bin/env python
"""Tests for jss wrapper.
These tests will FAIL! A few of the tests assert values local to my
institution. Edit them to work in your environment, or find a better way to do
it and send me an email!

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

TESTPOLICY = 'python-jss Test Policy'


def setup():
    """Make sure failed tests that create policies don't hamper our ability
    to continue testing.

    """
    try:
        cleanup = j_global.Policy(TESTPOLICY)
        cleanup.delete()
    except JSSGetError:
        pass


class testJSSPrefs(object):

    def test_jssprefs(self):
        jp = JSSPrefs()
        result = subprocess.check_output(['defaults', 'read', 'org.da.python-jss', 'jss_user'])
        assert_in(jp.user, result)
        result = subprocess.check_output(['defaults', 'read', 'org.da.python-jss', 'jss_pass'])
        assert_in(jp.password, result)
        result = subprocess.check_output(['defaults', 'read', 'org.da.python-jss', 'jss_url'])
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
        authUser = subprocess.check_output(['defaults', 'read', 'org.da.python-jss', 'jss_user'])
        authPass = subprocess.check_output(['defaults', 'read', 'org.da.python-jss', 'jss_pass'])
        repoUrl = subprocess.check_output(['defaults', 'read', 'org.da.python-jss', 'jss_url'])
        j = JSS(url=repoUrl, user=authUser, password=authPass)
        assert_is_instance(j, JSS)

    def test_jss_get_error(self):
        assert_raises(JSSGetError, j_global.get, '/donkey-tacos')

    def test_jss_get(self):
        policy = j_global.get(Policy.get_url(None))
        assert_is_instance(policy, ElementTree.Element)

    @with_setup(setup)
    def test_JSS_post(self):
        pt = JSSPolicyTemplate(TESTPOLICY)
        new_policy = j_global.Policy(pt)
        # If successful, we'll get a new ID number
        assert_is_instance(new_policy.id, int)
        new_policy.delete()

    def test_JSS_constructor_methods(self):
        skip_these_methods = ['__init__', 'get', 'delete', 'put', 'post', '_error_handler']
        constructor_methods = [ m[1] for m in inspect.getmembers(j_global) if inspect.ismethod(m[1]) and m[0] not in skip_these_methods]
        for cls in constructor_methods:
            instance = cls()
            yield self.check_JSS_constructor_method, instance

    def check_JSS_constructor_method(self, instance):
            assert_true(isinstance(instance, JSSObject) or isinstance(instance, JSSObjectList))

    @with_setup(setup)
    def test_jss_put(self):
        pt = JSSPolicyTemplate(TESTPOLICY)
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
        pt = JSSPolicyTemplate(TESTPOLICY)
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
        pt = JSSPolicyTemplate(TESTPOLICY)
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
    def test_JSSComputerGroupTemplate(self):
        cgt = JSSComputerGroupTemplate("Test")
        assert_is_instance(cgt, JSSComputerGroupTemplate)
        test_group = j_global.ComputerGroup(cgt)
        assert_is_instance(test_group, ComputerGroup)
        test_group.delete()

    def test_JSSComputerGroupTemplate_Smart(self):
        cgt = JSSComputerGroupTemplate("Test", True)
        assert_is_instance(cgt, JSSComputerGroupTemplate)
        criterion = SearchCriteria("Computer Name", 0, "and", "like", "craigs")
        cgt.add_criterion(criterion)
        test_group = j_global.ComputerGroup(cgt)
        assert_is_instance(test_group, ComputerGroup)
        test_group.delete()

    def test_JSSPackageTemplate(self):
        package_template = JSSPackageTemplate("Taco.pkg")
        assert_is_instance(package_template, JSSPackageTemplate)
        package = j_global.Package(package_template)
        assert_is_instance(package, Package)
        package.delete()

    def test_JSSSimpleTemplate(self):
        cat_template = JSSCategoryTemplate("Python JSS Test Category")
        assert_is_instance(cat_template, JSSCategoryTemplate)
        category = j_global.Category(cat_template)
        assert_is_instance(category, Category)
        category.delete()


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
