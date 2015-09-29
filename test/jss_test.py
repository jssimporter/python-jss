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


import os
import subprocess
import inspect
from xml.etree import ElementTree

from nose.tools import *

from jss import *
from jss.jssobjectlist import JSSObjectList
try:
    from jss.contrib import FoundationPlist
except ImportError as e:
    if os.uname()[0] == 'Darwin':
        print("Warning: Import of FoundationPlist failed: %s" % e)
        print("See README for information on this issue.")
    import plistlib


global j_global
prefs = "com.github.sheagcraig.python-jss.test-server.plist"
if is_osx():
    PREF_PATH = os.path.join("~/Library/Preferences", prefs)
elif is_linux():
    PREF_PATH = os.path.join("~", "." + prefs)
else:
    raise Exception("Unknown/unsupported OS.")
jp = JSSPrefs(PREF_PATH)
j_global = JSS(jss_prefs=jp)

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


class TestJSSPrefs(object):

    def test_jssprefs(self):
        jp = JSSPrefs(PREF_PATH)
        try:
            prefs = FoundationPlist.readPlist(os.path.expanduser(PREF_PATH))
        except NameError:
            # Plist files are probably not binary on non-OS X
            # machines, so this should be safe.
            try:
                prefs = plistlib.readPlist(os.path.expanduser(PREF_PATH))
            except ExpatError:
                subprocess.call(['plutil', '-convert', 'xml1',
                                    PREF_PATH])
                prefs = plistlib.readPlist(os.path.expanduser(PREF_PATH))
        #result = subprocess.check_output(['defaults', 'read', 'com.github.sheagcraig.python-jss', 'jss_user'])
        assert_in(jp.user, prefs["jss_user"])
        #result = subprocess.check_output(['defaults', 'read', 'com.github.sheagcraig.python-jss', 'jss_pass'])
        assert_in(jp.password, prefs["jss_pass"] )
        #result = subprocess.check_output(['defaults', 'read', 'com.github.sheagcraig.python-jss', 'jss_url'])
        assert_in(jp.url, prefs["jss_url"])

    def test_jssprefs_missing_file_error(self):
        assert_raises(JSSPrefsMissingFileError, JSSPrefs, '/nonexistent_path')

    def test_jssprefs_missing_key_error(self):
        assert_raises(JSSPrefsMissingKeyError, JSSPrefs, 'test/incomplete_preferences.plist')


class TestJSS(object):

    def test_jss_with_jss_prefs(self):
        jp = JSSPrefs()
        j = JSS(jss_prefs=jp)
        assert_is_instance(j, JSS)

    def test_jss_with_args(self):
        try:
            prefs = FoundationPlist.readPlist(os.path.expanduser(PREF_PATH))
        except NameError:
            # Plist files are probably not binary on non-OS X
            # machines, so this should be safe.
            try:
                prefs = plistlib.readPlist(os.path.expanduser(PREF_PATH))
            except ExpatError:
                subprocess.call(['plutil', '-convert', 'xml1',
                                    PREF_PATH])
                prefs = plistlib.readPlist(os.path.expanduser(PREF_PATH))
        authUser = prefs["jss_user"]
        authPass = prefs["jss_pass"]
        repoUrl = prefs["jss_url"]
        j = JSS(url=repoUrl, user=authUser, password=authPass)
        assert_is_instance(j, JSS)

    def test_jss_get_error(self):
        assert_raises(JSSGetError, j_global.get, '/donkey-tacos')

    def test_jss_get(self):
        policy = j_global.get(Policy.get_url(None))
        assert_is_instance(policy, ElementTree.Element)

    @with_setup(setup)
    def test_JSS_post(self):
        new_policy = Policy(j_global, TESTPOLICY)
        new_policy.save()
        # If successful, we'll get a new ID number
        assert_is_instance(new_policy.id, str)
        new_policy.delete()

    def test_JSS_constructor_methods(self):
        skip_these_methods = ['__init__', 'get', 'delete', 'put', 'post', '_error_handler', "_docstring_parameter"]
        constructor_methods = [m[1] for m in inspect.getmembers(j_global) if inspect.ismethod(m[1]) and m[0] not in skip_these_methods]
        for cls in constructor_methods:
            instance = cls()
            yield self.check_JSS_constructor_method, instance

    def check_JSS_constructor_method(self, instance):
            assert_true(isinstance(instance, JSSObject) or isinstance(instance, JSSObjectList))

    @with_setup(setup)
    def test_jss_put(self):
        new_policy = Policy(j_global, TESTPOLICY)
        new_policy.save()
        id_ = new_policy.id

        # Change the policy.
        recon = new_policy.find('maintenance/recon')
        # This is str, not bool...
        recon.text = 'false'
        new_policy.save()

        test_policy = j_global.Policy(id_)
        assert_equal(test_policy.find('maintenance/recon').text, 'false')

        new_policy.delete()

    @with_setup(setup)
    def test_jss_delete(self):
        new_policy = Policy(j_global, TESTPOLICY)
        new_policy.save()
        id_ = new_policy.id

        # Test delete. This is of course successful if the previous two tests
        # pass.
        new_policy.delete()
        assert_raises(JSSGetError, j_global.Policy, id_)


class TestJSSObjectFactory(object):
    def test_JSSObjectFactory_list(self):
        obj_list = j_global.factory.get_object(Policy)
        assert_is_instance(obj_list, JSSObjectList)

    def test_JSSObjectFactory_JSSObject(self):
        obj_list = j_global.factory.get_object(Policy, 1)
        assert_is_instance(obj_list, Policy)


class TestJSSObject(object):
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

    @with_setup(setup)
    def test_JSSObject_get_object_url(self):
        new_policy = Policy(j_global, TESTPOLICY)
        new_policy.save()

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

            def new(self, name, **kwargs):
                pass

        class NoPutObject(JSSObject):
            """We don't need to test for this. This is just for doc purposes.

            """
            can_put = False
            pass

        class NoPutNoPostObject(JSSObject):
            can_put = False
            can_post = False

            def new(self, name):
                pass

        class NoDeleteObject(JSSObject):
            can_delete = False

            def new(self, name):
                pass

        assert_raises(JSSMethodNotAllowedError, j_global.factory.get_object,
                      NoListObject, None)
        assert_raises(JSSMethodNotAllowedError, j_global.factory.get_object,
                      NoGetObject, None)
        bad_policy = NoPostObject(j_global, "No workie")
        assert_raises(JSSMethodNotAllowedError, bad_policy.save)

        np = NoPutNoPostObject(j_global, "TestNoPutNoPost")
        assert_raises(JSSMethodNotAllowedError, np.save)

        nd = NoDeleteObject(j_global, "TestNoDelete")
        assert_raises(JSSMethodNotAllowedError, nd.delete)


class TestJSSFlatObject(object):
    def test_JSSFlatObject_new(self):
        """Ensure we cannot create new objects of this type."""
        assert_raises(JSSPostError, ActivationCode, j_global, "Test")


class TestJSSDeviceObjects(object):
    def test_JSSDeviceObject_properties(self):
        computer = j_global.Computer('name=fs-mbp-test')
        assert_equal(computer.udid, '6552F6E6-6A51-51DB-A395-7DFD8F33461C')
        assert_equal(computer.serial_number, 'W8939GV266D')

    def test_Computer_properties(self):
        computer = j_global.Computer('name=fs-mbp-test')
        assert_is_instance(computer.mac_addresses, list)
        assert_equal(computer.mac_addresses, [
            '00:26:BB:5B:57:FA', '00:26:BB:11:5A:10'])
        match = j_global.Computer('match=fs-mbp-test')
        assert_is_instance(match, JSSObjectList)

    # Don't currently have any iOS devices in test JSS, so this will
    # fail.
    def test_MobileDevice_properties(self):
        computer = j_global.MobileDevice('name=abenson-jsstest')
        assert_equal(computer.wifi_mac_address, 'B0:65:BD:13:EF:47')
        assert_equal(computer.bluetooth_mac_address, 'B0:65:BD:13:EF:48')


class TestJSSObject_Subclasses(object):
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


class TestJSSObjectNewMethods(object):
    """Tests for ensuring that objects covered by new methods work as expected.

    """

    @with_setup(setup)
    def test_ComputerGroupNew(self):
        cg = ComputerGroup(j_global, TESTGROUP)
        cg.save()
        assert_is_instance(cg, ComputerGroup)
        cg.delete()

    @with_setup(setup)
    def test_ComputerGroup_Smart(self):
        cg = ComputerGroup(j_global, TESTGROUP, is_smart=True)
        cg.add_criterion("Computer Name", 0, "and", "like", "craigs-imac")
        cg.findtext("criteria/criterion/name")
        cg.save()
        assert_is_instance(cg, ComputerGroup)
        assert_true(cg.is_smart)
        assert_equals(cg.findall("criteria/criterion/name")[0].text,
                      "Computer Name")
        cg.delete()

    def test_PackageTemplate(self):
        package = Package(j_global, "Taco.pkg", cat_name="Testing")
        package.save()
        assert_is_instance(package, Package)
        package.delete()

    def test_JSSSimpleTemplate(self):
        category = Category(j_global, "Python JSS Test Category")
        category.save()
        assert_is_instance(category, Category)
        category.delete()

    def test_Policy_new(self):
        policy = Policy(j_global, "python-jss-test-policy")
        assert_is_instance(policy, Policy)
        computer = j_global.Computer('craigs-imac')
        policy.add_object_to_scope(computer)
        policy_string = sorted(r"""<policy>
    <general>
        <name>python-jss-test-policy</name>
        <enabled>true</enabled>
        <frequency>Once per computer</frequency>
        <category />
    </general>
    <scope>
        <computers>
            <computer>
                <id>2</id>
                <name>craigs-imac</name>
            </computer>
        </computers>
        <computer_groups />
        <buildings />
        <departments />
        <exclusions>
            <computers />
            <computer_groups />
            <buildings />
            <departments />
        </exclusions>
    </scope>
    <self_service>
        <use_for_self_service>true</use_for_self_service>
    </self_service>
    <package_configuration>
        <packages />
    </package_configuration>
    <maintenance>
        <recon>true</recon>
    </maintenance>
</policy>
""".splitlines())
        assert_equal(sorted(policy.__repr__().splitlines()), policy_string)
        policy.save()
        # Test whether JSS accepts our new() object. Will throw an exception if
        # it doesn't work; replaces data if it does, thus they should no longer
        # match.
        assert_not_equal(policy.__repr__(), policy_string)
        policy.delete()


class TestJSSListData(object):
    # The methods on JSSListData are indirectly tested in many of the above
    # tests.
    pass


class TestJSSObjectList(object):
    def test_retrieve(self):
        computers = j_global.Computer()
        assert_is_instance(computers.retrieve(1), Computer)

    def test_retrieve_by_id(self):
        computers = j_global.Computer()
        search_id = computers[-1].id
        assert_is_instance(computers.retrieve_by_id(search_id), Computer)

    def test_retrieve_all(self):
        # We use policies since they're smaller, and hopefully smaller in
        # number
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
