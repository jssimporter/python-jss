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


class JSSAuthenticationError(Exception):
    pass


class JSSConnectionError(Exception):
    pass


class JSSGetError(Exception):
    pass


class JSS(object):
    """Connect to a JSS and handle API requests."""
    def __init__(self, url, user, password, ssl_verify=True):
        self._url = '%s/JSSResource' % url
        self.user = user
        self.password = password
        self.ssl_verify = ssl_verify
        self.auth = base64.encodestring('%s:%s' %
                                   (user, password)).replace('\n', '')

    def get(self, path, **kwargs):
        """Perform a get operation.
        path: Path to specific object type.
        Returns an ElementTree element.
        
        """
        url = '%s%s' % (self._url, path)
        print('Trying to reach JSS and fetch at %s' % url)
        headers = {'Authorization': "Basic %s" % self.auth}
        response = None
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

repoUrl = "https://uscasper.school.da.org:8443"

# Create a plist file with the API username and password like so:
# defaults write org.da.jss_helper jss_user <username>
# defaults write org.da.jss_helper jss_pass <password>

# Get auth information
preferences = '~/Library/Preferences/org.da.jss_helper.plist'
jss_helper_prefs = FoundationPlist.readPlist(os.path.expanduser(preferences))
authUser = jss_helper_prefs.get('jss_user')
authPass = jss_helper_prefs.get('jss_pass')
base64string = base64.encodestring('%s:%s' %
                                   (authUser, authPass)).replace('\n', '')


def indent(elem, level=0, more_sibs=False):
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


def pprint(et):
    """Get the root of an elementtree and pretty print it."""
    #If I ElementTree.parse() I get an ElementTree object, but
    #ElementTree.fromstring() returns an Element object
    if isinstance(et, ElementTree.ElementTree):
        root = et.getroot()
    else:
        root = et
    indent(root)
    ElementTree.dump(root)


def jss_request(apiUrl):
    """Requests data from the jss.

    apiUrl should be a string of the full URL to the desired get procedure.

    Returns an ElementTree Element.

    """
    print('Trying to reach JSS and fetch at %s' % (apiUrl))
    headers = {'Authorization': "Basic %s" % base64string}
    submitRequest = None
    while submitRequest is None:
        try:
            submitRequest = requests.get(apiUrl, headers=headers)
        except requests.exceptions.SSLError as e:
            if hasattr(e, 'reason'):
                print 'Error! reason:', e.reason
            elif hasattr(e, 'code'):
                print 'Error! code:', e.code
                if e.code == 401:
                    raise RuntimeError('Got a 401 error.. \
                                       check the api username and password')
            #raise RuntimeError('Did not get a valid response from the server')
            print("Failed... Trying again in a moment.")
            time.sleep(2)

    # Does this object exist?
    if submitRequest.status_code == 404:
        print("Object %s does not exist!" % apiUrl)
        exit(404)

    # Create an ElementTree for parsing-encode it properly
    jss_results = submitRequest.text.encode('utf-8')
    try:
        xmldata = ElementTree.fromstring(jss_results)
    except UnicodeEncodeError as e:
        if hasattr(e, 'reason'):
            print 'Error! Reason: %s' % e.reason
            print 'Attempted encoding: %s' % e.encoding
            exit(1)
    return xmldata


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
