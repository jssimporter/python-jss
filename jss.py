#!/usr/bin/python
"""jss.py

Python wrapper for JSS API.

Shea Craig 2014

"""

from xml.etree import ElementTree
import base64
import time
import requests
import FoundationPlist
import os
from sys import exit


class JSSPrefsMissingKeyError(Exception):
    pass


class JSSAuthenticationError(Exception):
    pass


class JSSConnectionError(Exception):
    pass


class JSSGetError(Exception):
    pass


class JSSPrefs(object):
    def __init__(self, preferences_file=None):
        if not preferences_file:
            path = '~/Library/Preferences/org.da.jss_helper.plist'
            preferences = os.path.expanduser(path)
        else:
            preferences = preferences_file
        try:
            prefs = FoundationPlist.readPlist(os.path.expanduser(preferences))
            self.user = prefs.get('jss_user')
            self.password = prefs.get('jss_pass')
            self.url = prefs.get('jss_url')
        except:
            raise JSSPrefsMissingKeyError


class JSS(object):
    """Connect to a JSS and handle API requests."""
    def __init__(self, jss_prefs=None, url=None, user=None, password=None,
                 ssl_verify=True):
        """Provide either a JSSPrefs object OR specify url, user, and password
        to init.

        jss_prefs: A JSSPrefs object.
        url: Path with port to a JSS.
        user: API Username.
        password: API Password.
        ssl_verify: Boolean indicating whether to verify SSL certificates.

        """
        if jss_prefs is not None:
            url = jss_prefs.url
            user = jss_prefs.user
            password = jss_prefs.password

        self._url = '%s/JSSResource' % url
        self._user = user
        self._password = password
        self.ssl_verify = ssl_verify
        self.auth = base64.encodestring('%s:%s' %
                                   (user, password)).replace('\n', '')

    def user(self, user):
        self._user = user
        auth = (self._user, self._password)
        self.auth = base64.encodestring('%s:%s' % auth).replace('\n', '')

    def password(self, password):
        self._password = password
        auth = (self._user, self._password)
        self.auth = base64.encodestring('%s:%s' % auth).replace('\n', '')

    def get(self, path, **kwargs):
        """Perform a get operation.
        path: Path to specific object type.
        Returns an ElementTree element.
        
        """
        # Not sure I'll be needing the **kwargs
        url = '%s%s' % (self._url, path)
        headers = {'Authorization': "Basic %s" % self.auth}
        response = None
        print('Trying to reach JSS at %s' % url)
        while response is None:
            try:
                response = requests.get(url, headers=headers, 
                                         verify=self.ssl_verify)
            except requests.exceptions.SSLError as e:
                if hasattr(e, 'reason'):
                    print 'Error! reason:', e.reason
                #raise RuntimeError('Did not get a valid response from the server')
                print("Failed... Trying again in a moment.")
                time.sleep(2)

        if response.status_code == 401:
            raise JSSAuthenticationError('Authentication error: check the ' \
                                         'api username and password')
        elif response.status_code == 404:
            raise JSSGetError("Object %s does not exist!" % url)

        # Create an ElementTree for parsing-encode it properly
        jss_results = response.text.encode('utf-8')
        try:
            xmldata = ElementTree.fromstring(jss_results)
        except UnicodeEncodeError as e:
            if hasattr(e, 'reason'):
                print 'Error! Reason: %s' % e.reason
                print 'Attempted encoding: %s' % e.encoding
                exit(1)
        return xmldata


class JSSObject(object):
    """Base class for representing all available JSS API objects."""
    def __init__(self):
        pass

    def indent(self, elem, level=0, more_sibs=False):
        """Indent an xml element object to prepare for pretty printing."""
        i = "\n"
        pad = '    '
        if level:
            i += (level - 1) * pad
        num_kids = len(elem)
        if num_kids:
            if not elem.text or not elem.text.strip():
                elem.text = i + pad
                if level:
                    elem.text += pad
            count = 0
            for kid in elem:
                indent(kid, level+1, count < num_kids - 1)
                count += 1
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
                if more_sibs:
                    elem.tail += pad
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
                if more_sibs:
                    elem.tail += pad


    def pprint(self, et):
        """Get the root of an elementtree and pretty print it."""
        #If I ElementTree.parse() I get an ElementTree object, but
        #ElementTree.fromstring() returns an Element object
        if isinstance(et, ElementTree.ElementTree):
            root = et.getroot()
        else:
            root = et
        indent(root)
        ElementTree.dump(root)


#OLD STUFF#####################################################################


#Computer Functions############################################################


def get_policies():
    """Gets the list of all policies from the JSS."""
    # build our request for the entire list of items
    apiUrl = repoUrl + "/JSSResource/" + 'policies'
    xmldata = jss_request(apiUrl)
    return xmldata


def get_policy_ids(xmldata):
    """Parse an etree of policies for id numbers."""
    elements = xmldata.findall('policy/id')
    return [element.text for element in elements]


def get_policy_by_id(jss_id):
    """Get all data for a policy."""
    apiUrl = repoUrl + "/JSSResource/" + 'policies/id/' + jss_id
    return jss_request(apiUrl)


def get_policy_by_name(policy_name):
    """Get all data for a policy."""
    apiUrl = repoUrl + "/JSSResource/" + 'policies/name/' + policy_name
    return jss_request(apiUrl)


def get_policies_scoped_to_computer_group(group):
    """Search for policies that are scoped to a particular computer group."""
    policies = get_policies()
    ids = get_policy_ids(policies)
    full_policies = [get_policy_by_id(jss_id) for jss_id in ids]
    results = []
    search = 'scope/computer_groups/computer_group'
    for policy in full_policies:
        for computer_group in policy.findall(search):
            if computer_group.findtext('name') == group:
                results.append((policy.find('general/id'),
                                policy.find('general/name')))
    return results


#Mobile Device Functions#######################################################


def get_md_configps():
    """Gets the list of all mobile device configuration profiles from the
    JSS.

    """
    # build our request for the entire list of items
    apiUrl = repoUrl + "/JSSResource/" + 'mobiledeviceconfigurationprofiles'
    xmldata = jss_request(apiUrl)
    return xmldata


def get_md_configp_ids(xmldata):
    """Parse an etree of configuration profiles for id numbers."""
    elements = xmldata.findall('configuration_profile/id')
    return [element.text for element in elements]


def get_configp_by_id(jss_id):
    """Get all data for a configuration profile."""
    apiUrl = repoUrl + "/JSSResource/" + 'mobiledeviceconfigurationprofiles/id/' + jss_id
    return jss_request(apiUrl)


def get_md_configp_scoped_to_group(group):
    """Search for configuration profiles that are scoped to a particular
    group.

    """
    configps = get_md_configps()
    ids = get_md_configp_ids(configps)
    full_configps = [get_configp_by_id(jss_id) for jss_id in ids]
    results = []
    search = 'scope/mobile_device_groups/mobile_device_group'
    for configp in full_configps:
        for device_group in configp.findall(search):
            if device_group.findtext('name') == group:
                results.append((configp.find('general/id'),
                                configp.find('general/name')))
    return results
