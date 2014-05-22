#!/usr/bin/env python
"""jss.py

Python wrapper for JSS API.

Shea Craig 2014

"""

from xml.etree import ElementTree
import base64
import os
import re

import requests
import FoundationPlist


class JSSPrefsMissingKeyError(Exception):
    pass


class JSSAuthenticationError(Exception):
    pass


class JSSConnectionError(Exception):
    pass


class JSSGetError(Exception):
    pass


class JSSCreationError(Exception):
    pass

class JSSDeletionError(Exception):
    pass


class JSSPrefs(object):
    def __init__(self, preferences_file=None):
        if preferences_file is None:
            path = '~/Library/Preferences/org.da.jss_helper.plist'
            preferences_file = os.path.expanduser(path)
        try:
            prefs = FoundationPlist.readPlist(os.path.expanduser(
                    preferences_file))
            self.user = prefs.get('jss_user')
            self.password = prefs.get('jss_pass')
            self.url = prefs.get('jss_url')
        except:
            raise JSSPrefsMissingKeyError("Please provide all required"
                                          " preferences!")


class JSS(object):
    """Connect to a JSS and handle API requests."""
    def __init__(self, jss_prefs=None, url=None, user=None, password=None,
                 ssl_verify=True, verbose=False):
        """Provide either a JSSPrefs object OR specify url, user, and password
        to init.

        jss_prefs: A JSSPrefs object.
        url: Path with port to a JSS.
        user: API Username.
        password: API Password.
        ssl_verify: Boolean indicating whether to verify SSL certificates.
                Defaults to True.

        """
        if jss_prefs is not None:
            url = jss_prefs.url
            user = jss_prefs.user
            password = jss_prefs.password

        self._url = '%s/JSSResource' % url
        self.user = user
        self.password = password
        self.ssl_verify = ssl_verify
        self.verbose = verbose

    def get_request(self, url):
        """Get a url, handle errors, and return an etree from the XML data."""
        response = requests.get(url, auth=(self.user, self.password),
                                verify=self.ssl_verify)

        if response.status_code == 401:
            raise JSSAuthenticationError(
                    'Authentication error: check the api username and password')
        elif response.status_code == 404:
            raise JSSGetError("Object %s does not exist!" % url)

        # JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        xmldata = ElementTree.fromstring(jss_results)
        return xmldata

    def raw_get(self, path):
        """Perform a get operation from a specified path.
        path: Path to specific object type.
        Returns an ElementTree element.

        """
        url = '%s%s' % (self._url, path)
        return self.get_request(url)

    def get(self, obj_class, id_=None):
        """Get method for JSSObjects."""
        url = obj_class._url
        if id_ is not None:
            # JSS API adds a /id/ between our object type and id number.
            url = '%s%s%s%s' % (self._url, url, '/id/', str(id_))
            if self.verbose:
                print(url)
        else:
            url = '%s%s' % (self._url, url)
        return self.get_request(url)

    def list(self, obj_class):
        """Query the JSS for a list of all objects of an object type.
        Returns a list of objects of the corresponding type.

        """
        url = obj_class._url
        url = '%s%s' % (self._url, url)

        if self.verbose:
            print(url)
        xmldata = self.get_request(url)

        # Build a list of objects based on the results. Remove the size elements.
        lst = [obj_class(self, item) for item in xmldata if item is not None and item.tag != 'size']
        return lst

    def post(self, obj_class, data):
        """Post an object to the JSS. For creating new objects only."""
        # The JSS expects a post to ID 0 to create an object
        url = '%s%s%s' % (self._url, obj_class._url, '/id/0')
        response = requests.post(url, auth=(self.user, self.password),
                                 data=data, verify=self.ssl_verify)

        if response.status_code == 401:
            raise JSSAuthenticationError(
                    'Authentication error: check the api username and password')
        elif response.status_code == 409:
            raise JSSCreationError(
                    'Creation error: Possible name conflict or other problem.'
                    '\n%s' % response.text.encode('utf-8'))

        # Get the ID of the new object. JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        return jss_results

    def put(self, url):
        pass

    def delete(self, obj_class):
        """Delete an object from the JSS."""
        url = '%s%s%s%s' % (self._url, obj_class._url, '/id/', 
                            str(obj_class.id()))
        response = requests.delete(url, auth=(self.user, self.password),
                                 verify=self.ssl_verify)
        if response.status_code == 200:
            print("Success.")
        elif response.status_code == 404:
            raise JSSDeletionError('Deletion error: %s' %
                                   response.text.encode('utf-8'))


    def _get_list_or_object(self, cls, id_):
        if id_ is None:
            return cls.list(self)
        else:
            return cls(self, id_)

    def Category(self, id_=None):
        return self._get_list_or_object(Category, id_)

    def Computer(self, id_=None):
        return self._get_list_or_object(Computer, id_)

    def ComputerGroup(self, id_=None):
        return self._get_list_or_object(ComputerGroup, id_)

    def MobileDevice(self, id_=None):
        return self._get_list_or_object(MobileDevice, id_)

    def MobileDeviceConfigurationProfile(self, id_=None):
        return self._get_list_or_object(MobileDeviceConfigurationProfile, id_)

    def MobileDeviceGroup(self, id_=None):
        return self._get_list_or_object(MobileDeviceGroup, id_)

    def Policy(self, id_=None):
        return self._get_list_or_object(Policy, id_)


class JSSObject(object):
    """Base class for representing all available JSS API objects."""
    _url = None

    def __init__(self, jss, data=None):
        self.jss = jss

        #if data is None or type(data) in [int, str]:
        if data is None or isinstance(data, int):
            data = self.jss.get(self.__class__, data)
        # Create a new object
        elif isinstance(data, str):
            results = self.jss.post(self.__class__, data)
            print results
            id_ =  re.search(r'<id>([0-9]+)</id>', results).group(1)
            print("Object created with ID: %s" % id_)
            #data = ElementTree.fromstring(data)
            data = self.jss.get(self.__class__, id_)

        self.xml = data

    def _get_list_or_object(self, cls, id):
        if id is None:
            return cls.list(self)
        else:
            return cls(self, id)

    @classmethod
    def list(cls, jss):
        return jss.list(cls)

    def _create(self):
        self.xml = self.gitlab.post(self)

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
                self.indent(kid, level+1, count < num_kids - 1)
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

    def pprint(self):
        """Pretty print our XML data."""
        self.indent(self.xml)
        ElementTree.dump(self.xml)

    # Shared properties
    def name(self):
        return self.xml.find('general/name').text

    def id(self):
        return self.xml.find('general/id').text


class Category(JSSObject):
    _url = '/categories'

class Computer(JSSObject):
    _url = '/computers'


class ComputerGroup(JSSObject):
    _url = '/computergroups'


class MobileDevice(JSSObject):
    _url = '/mobiledevices'


class MobileDeviceConfigurationProfile(JSSObject):
    _url = '/mobiledeviceconfigurationprofiles'


class MobileDeviceGroup(JSSObject):
    _url = '/mobiledevicegroups'


class Policy(JSSObject):
    _url = '/policies'
