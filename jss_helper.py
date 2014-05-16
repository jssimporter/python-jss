#!/usr/bin/python
"""jss_helper.py

Functions to improve human readability of xml output for JAMF API results.

Shea Craig 2014

"""

from xml.etree import ElementTree
import base64
import time
import requests
import FoundationPlist
import os


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


def get_policy(jss_id):
    """Get all data for a policy."""
    apiUrl = repoUrl + "/JSSResource/" + 'policies/id/' + jss_id
    try:
        xmldata = jss_request(apiUrl)
    except RuntimeError:
        #This can fail because you make too many requests, too quickly
        print("Failed... Trying again in 3 seconds")
        xmldata = None
        while xmldata is None:
            time.sleep(3)
            try:
                xmldata = jss_request(apiUrl)
            except RuntimeError:
                xmldata = None
                print("Failed again... Trying again")
    return xmldata


def jss_request(apiUrl):
    """Requests data from the jss.

    apiUrl should be a string of the full URL to the desired get procedure.

    Returns an ElementTree Element.

    """
    print('Trying to reach JSS and fetch at %s' % (apiUrl))
    headers = {'Authorization': "Basic %s" % base64string}
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
        raise RuntimeError('Did not get a valid response from the server')
    #Create an ElementTree for parsing
    jss_results = submitRequest.text
    try:
        xmldata = ElementTree.fromstring(jss_results)
    except:
        raise ElementTree.ParseError("Successfully communicated, but error'd \
                                     when parsing XML")
    return xmldata


def get_policies_scoped_to_computer_group(group):
    """Search for policies that are scoped to a particular computer group."""
    policies = get_policies()
    ids = get_policy_ids(policies)
    full_policies = [get_policy(jss_id) for jss_id in ids]
    results = []
    search = 'scope/computer_groups/computer_group'
    for policy in full_policies:
        for computer_group in policy.findall(search):
            if computer_group.findtext('name') == group:
                results.append((policy.find('general/id'),
                                policy.find('general/name')))
    return results


def get_group_policies(args):
    """Helper function."""
    results = get_policies_scoped_to_computer_group(args.group)
    print("Results:")
    for result in results:
        pprint(result[0])
        pprint(result[1])
