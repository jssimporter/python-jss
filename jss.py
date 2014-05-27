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


class JSSPutError(Exception):
    pass


class JSSCreationError(Exception):
    pass


class JSSDeletionError(Exception):
    pass


class JSSMethodNotAllowedError(Exception):
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
        # For some objects the JSS tries to return JSON if we don't specify
        # that we want XML.
        headers = {'Accept': 'application/xml'}
        response = requests.get(url, auth=(self.user, self.password),
                                verify=self.ssl_verify, headers=headers)

        if response.status_code == 401:
            raise JSSAuthenticationError(
                    'Authentication error: check the api username and password'
                    ', and verify user has access to this object.')
        elif response.status_code == 404:
            raise JSSGetError("Object %s does not exist!" % url)

        # JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        try:
            xmldata = ElementTree.fromstring(jss_results)
        except ElementTree.ParseError:
            print("Error Parsing XML:\n%s" % jss_results)
            raise JSSGetError
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

        # Build a list of objects based on the results. Remove the size elems.
        lst = [obj_class(self, item) for item in xmldata if
               item is not None and item.tag != 'size']
        return lst

    def post(self, obj_class, data):
        """Post an object to the JSS. For creating new objects only."""
        # The JSS expects a post to ID 0 to create an object
        url = '%s%s%s' % (self._url, obj_class._url, '/id/0')
        response = requests.post(url, auth=(self.user, self.password),
                                 data=data, verify=self.ssl_verify)

        # Technically, you're supposed to get a 403 if you don't have
        # permissions... Need to research and test.
        if response.status_code == 401:
            raise JSSAuthenticationError(
                    'Authentication error: check the api username and password'
                    ', and verify user has access to this object.')
        elif response.status_code == 409:
            raise JSSCreationError(
                    'Creation error: Possible name conflict or other problem.'
                    '\n%s' % response.text.encode('utf-8'))

        # Get the ID of the new object. JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        return jss_results

    def put(self, obj_class):
        """Updates an object on the JSS."""
        # Need to convert data to string...
        data = ElementTree.tostring(obj_class.xml)
        url = '%s%s%s%s' % (self._url, obj_class._url, '/id/',
                            str(obj_class.id()))
        response = requests.put(url, auth=(self.user, self.password),
                                 verify=self.ssl_verify, data=data)
        if response.status_code == 201:
            print("Success.")
        else:
            #raise JSSPutError('Put error. Response Code: %s\tResponse: %s'
            #                  (response.status_code,
            #                   response.text.encode('utf-8')))
            raise JSSPutError(response.status_code)


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

    def ActivationCode(self, id_=None):
        return ActivationCode(self, None)

    def Category(self, id_=None):
        return self._get_list_or_object(Category, id_)

    def Computer(self, id_=None):
        return self._get_list_or_object(Computer, id_)

    def ComputerCheckIn(self, id_=None):
        return ComputerCheckIn(self, None)

    def ComputerCommand(self, id_=None):
        return self._get_list_or_object(ComputerCommand, id_)

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
    """Base class for representing all available JSS API objects.

    Object construction depends on the data argument provided to init.
    If data is type:
        None:   Perform a list operation
        int:    Retrieve an object with ID of <data>
        str:    Create a new object with xml <str>

        Warning! Be careful to not pass an ID number as a str, as this will
        attempt to create a new object, but fail due to flawed XML.
    """
    _url = None
    can_list = True
    can_get = True
    can_put = True
    can_post = True
    can_delete = True

    def __init__(self, jss, data=None):
        self.jss = jss

        if data is None or isinstance(data, int):
            data = self.jss.get(self.__class__, data)
        # Create a new object
        elif isinstance(data, str):
            if not self.can_post:
                raise JSSMethodNotAllowedError(self.__class__.__name__)
            results = self.jss.post(self.__class__, data)
            id_ =  re.search(r'<id>([0-9]+)</id>', results).group(1)
            print("Object created with ID: %s" % id_)
            #data = ElementTree.fromstring(data)
            data = self.jss.get(self.__class__, id_)

        self.xml = data

    def _get_list_or_object(self, cls, id):
        # Currently unused; may be useful if there are any dependent objects.
        if id is None:
            return cls.list(self)
        else:
            return cls(self, id)

    @classmethod
    def list(cls, jss):
        if not cls.can_list:
            raise JSSMethodNotAllowedError("Object class %s cannot be listed!"
                                           % cls.__class__.__name__)
        if not cls.can_get:
            raise JSSMethodNotAllowedError(cls.__class__.__name__)
        else:
            return jss.list(cls)

    def delete(self):
        if not self.can_delete:
            raise JSSMethodNotAllowedError(self.__class__.__name__)
        return self.jss.delete(self)

    def update(self):
        if not self.can_put:
            raise JSSMethodNotAllowedError(self.__class__.__name__)
        return self.jss.put(self)

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
        if self.xml.find('name') is not None:
            return self.xml.find('name').text
        else:
            return self.xml.find('general/name').text

    def id(self):
        if self.xml.find('id') is not None:
            return int(self.xml.find('id').text)
        else:
            return int(self.xml.find('general/id').text)


class ActivationCode(JSSObject):
    _url = '/activationcode'
    can_delete = False
    can_post = False
    can_list = False


class Category(JSSObject):
    _url = '/categories'


class Computer(JSSObject):
    _url = '/computers'


class ComputerCheckIn(JSSObject):
    _url = '/computercheckin'
    can_delete = False
    can_list = False
    can_post = False


class ComputerCommand(JSSObject):
    _url = '/computercommands'
    can_delete = False
    #can_list = False
    can_put = False


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
