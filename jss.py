#!/usr/bin/env python
"""jss.py

Python wrapper for JSS API.
Copyright (C) 2014 Shea G Craig <shea.craig@da.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from xml.etree import ElementTree
import os
import re
import copy

import requests
import FoundationPlist


class JSSPrefsMissingKeyError(Exception):
    pass


class JSSGetError(Exception):
    pass


class JSSPutError(Exception):
    pass


class JSSPostError(Exception):
    pass


class JSSDeleteError(Exception):
    pass


class JSSMethodNotAllowedError(Exception):
    pass


class JSSUnsupportedSearchMethodError(Exception):
    pass


class JSSPrefs(object):
    """Uses the OS X preferences system to store credentials and JSS URL."""
    def __init__(self, preferences_file=None):
        """Create a preferences object.

        preferences_file: Alternate location to look for preferences.

        Preference file should include the following keys:
            jss_url:        Full path, including port, to JSS,
                            e.g. 'https://mycasper.donkey.com:8443'
                            (JSS() handles the appending of /JSSResource)
            jss_user:       API username to use.
            jss_password:   API password.

        """
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

        jss_prefs:  A JSSPrefs object.
        url:        Path with port to a JSS. See JSSPrefs.__doc__
        user:       API Username.
        password:   API Password.
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

    def _error_handler(self, exception_cls, response):
        """Generic error handler. Converts html responses to friendlier
        text.

        """
        # Responses are sent as html. Split on the newlines and give us the
        # <p> text back.
        errorlines = response.text.encode('utf-8').split('\n')
        error = []
        for line in errorlines:
            e = re.search(r'<p.*>(.*)</p>', line)
            if e:
                error.append(e.group(1))

        error = '\n'.join(error)
        raise exception_cls('JSS ERROR. Response Code: %s\tResponse: %s' %
                          (response.status_code, error))

    def get_request(self, url):
        """Get a url, handle errors, and return an etree from the XML data."""
        # For some objects the JSS tries to return JSON if we don't specify
        # that we want XML.
        headers = {'Accept': 'application/xml'}
        response = requests.get(url, auth=(self.user, self.password),
                                verify=self.ssl_verify, headers=headers)

        if response.status_code == 200:
            if self.verbose:
                print("GET: Success.")
        elif response.status_code >= 400:
            self._error_handler(JSSGetError, response)

        # JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        try:
            xmldata = ElementTree.fromstring(jss_results)
        except ElementTree.ParseError:
            raise JSSGetError("Error Parsing XML:\n%s" % jss_results)
        return xmldata

    def raw_get(self, path):
        """Perform a get operation from a specified path.
        path: Path to specific object type.
        Returns an ElementTree element.

        """
        url = '%s%s' % (self._url, path)
        return self.get_request(url)

    def get(self, obj_class, id_=None, url_suffix='/id/'):
        """Get method for JSSObjects."""
        url = obj_class._url
        if id_ is not None and url_suffix:
            # JSS API adds a /id/ between our object type and id number.
            url = '%s%s%s%s' % (self._url, url, url_suffix, str(id_))
            if self.verbose:
                print(url)
        else:
            url = '%s%s' % (self._url, url)
        return self.get_request(url)

    def list(self, obj_class):
        """Query the JSS for a list of all objects of an object type.
        Returns a list of objects of the corresponding type. Objects will have
        a dict as their data property, rather than an Element.

        """
        url = obj_class._url
        url = '%s%s' % (self._url, url)

        if self.verbose:
            print(url)
        xmldata = self.get_request(url)

        # Build a list of objects based on the results. Remove the size elems.
        objects = []
        response_objects = [item for item in xmldata if item is not None and \
                            item.tag != 'size']
        for response_object in response_objects:
            d = {}
            for i in response_object:
                d[i.tag] = i.text

            objects.append(obj_class(self, d))
        return objects

    def post(self, obj_class, data):
        """Post an object to the JSS. For creating new objects only."""
        # The JSS expects a post to ID 0 to create an object
        url = '%s%s%s' % (self._url, obj_class._url, '/id/0')
        data = ElementTree.tostring(data)
        response = requests.post(url, auth=(self.user, self.password),
                                 data=data, verify=self.ssl_verify)

        if response.status_code == 201:
            if self.verbose:
                print("POST: Success")
        elif response.status_code >= 400:
            self._error_handler(JSSPostError, response)

        # Get the ID of the new object. JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        return jss_results

    def put(self, obj_class):
        """Updates an object on the JSS."""
        # Need to convert data to string...
        data = ElementTree.tostring(obj_class.data)
        url = '%s%s%s%s' % (self._url, obj_class._url, '/id/',
                            str(obj_class.id()))
        response = requests.put(url, auth=(self.user, self.password),
                                 verify=self.ssl_verify, data=data)
        if response.status_code == 201:
            if self.verbose:
                print("PUT: Success.")
        elif response.status_code >= 400:
            self._error_handler(JSSPutError, response)

    def delete(self, obj_class):
        """Delete an object from the JSS."""
        url = '%s%s%s%s' % (self._url, obj_class._url, '/id/',
                            str(obj_class.id()))
        response = requests.delete(url, auth=(self.user, self.password),
                                 verify=self.ssl_verify)
        if response.status_code == 200:
            if self.verbose:
                print("DEL: Success.")
        elif response.status_code >= 400:
            self._error_handler(JSSDeleteError, response)

    def _get_list_or_object(self, cls, id_, search):
        """Determine whether to list or get."""
        if id_ is None:
            return cls.list(self)
        else:
            return cls(self, id_, search)

    def ActivationCode(self, id_=None, search=None):
        return self._get_list_or_object(ActivationCode, id_, search)

    def Category(self, id_=None, search=None):
        return self._get_list_or_object(Category, id_, search)

    def Computer(self, id_=None, search=None):
        return self._get_list_or_object(Computer, id_, search)

    def ComputerCheckIn(self, id_=None, search=None):
        return self._get_list_or_object(ComputerCheckIn, id_, search)

    def ComputerCommand(self, id_=None, search=None):
        return self._get_list_or_object(ComputerCommand, id_, search)

    def ComputerGroup(self, id_=None, search=None):
        return self._get_list_or_object(ComputerGroup, id_, search)

    def MobileDevice(self, id_=None, search=None):
        return self._get_list_or_object(MobileDevice, id_, search)

    def MobileDeviceConfigurationProfile(self, id_=None, search=None):
        return self._get_list_or_object(MobileDeviceConfigurationProfile, id_,
                                        search)

    def MobileDeviceGroup(self, id_=None, search=None):
        return self._get_list_or_object(MobileDeviceGroup, id_, search)

    def Policy(self, id_=None, search=None):
        return self._get_list_or_object(Policy, id_, search)


class JSSObject(object):
    """Base class for representing all available JSS API objects.

    """
    _url = None
    can_list = True
    can_get = True
    can_put = True
    can_post = True
    can_delete = True
    search_types = {'name': '/name/'}

    def __init__(self, jss, data=None, search='name'):
        """Object construction depends on the data argument provided to init.
            If data is type:
                None:   Perform a list operation, or for non-container objects,
                        return all data.
                int:    Retrieve an object with ID of <data>
                str:    Retrieve an object with name of <str>. For some
                        objects, this may be overridden to include searching
                        by other criteria. See those objects for more info.
                dict:   Get the existing object with <dict>['id']
                xml.etree.ElementTree.Element:    Create a new object from xml

                search: A string matching the key of one of the object's
                        search_types. Defaults to a name search. See object
                        for available search types.

                Warning! Be sure to pass ID's as ints, not str!

        """
        self.jss = jss

        # Get an object with a numeric ID. Some objects don't list, so if
        # data is None, we do a get anyway.
        if data is None or isinstance(data, int):
            data = self.jss.get(self.__class__, data)

        # This object has been "listed". Copy useful data to a dict
        elif isinstance(data, dict):
            data = {k: v for k, v in data.items()}

        elif isinstance(data, str) and search in self.search_types:
                data = self.jss.get(self.__class__, data,
                                    self.search_types[search])

        # Create a new object
        elif isinstance(data, ElementTree.Element):
            if not self.can_post:
                raise JSSMethodNotAllowedError(self.__class__.__name__)
            results = self.jss.post(self.__class__, data)
            id_ =  re.search(r'<id>([0-9]+)</id>', results).group(1)
            print("Object created with ID: %s" % id_)
            data = self.jss.get(self.__class__, id_)
        elif search not in self.search_types:
            raise JSSUnsupportedSearchMethodError("This object cannot be "
                                                  "queried by %s" % search)

        self.data = data

    #def _get_list_or_object(self, cls, id_):
    #   """Currently unused; may be useful if there are any dependent
    #   objects.
    #
    #   """
    #    if id_ is None:
    #        return cls.list(self)
    #    else:
    #        return cls(self, id_)

    @classmethod
    def list(cls, jss):
        """Ensure that cls doesn't do something it shouldn't."""
        if not cls.can_list and not cls.can_get:
            raise JSSMethodNotAllowedError("Object class %s cannot be listed!"
                                           % cls.__class__.__name__)
        elif not cls.can_list:
            return cls(jss)
        elif not cls.can_get:
            raise JSSMethodNotAllowedError(cls.__class__.__name__)
        else:
            return jss.list(cls)

    def delete(self):
        """Delete this object from the JSS."""
        if not self.can_delete:
            raise JSSMethodNotAllowedError(self.__class__.__name__)
        return self.jss.delete(self)

    def update(self):
        """Update this object on the JSS.

        Data validation is up to the client.

        """
        if not self.can_put:
            raise JSSMethodNotAllowedError(self.__class__.__name__)
        return self.jss.put(self)

    def load(self):
        """Pull down information from the JSS to fill self.data property.

        When you perform a JSSObject.list(), self.data is filled with a dict
        as returned by the JSS. This data is used to perform a get with the ID
        from that dict. This method should be used on items in a list to
        retrieve their full data.

        """
        data = self.jss.get(self.__class__, self.id())
        self.data = data

    def _indent(self, elem, level=0, more_sibs=False):
        """Indent an xml element object to prepare for pretty printing.

        Method is internal to discourage indenting the self.data Element,
        thus potentially corrupting it.

        """
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
                self._indent(kid, level+1, count < num_kids - 1)
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

    def __repr__(self):
        """Make our data human readable."""
        if isinstance(self.data, ElementTree.Element):
            # deepcopy so we don't mess with the valid XML.
            pretty_data = copy.deepcopy(self.data)
            self._indent(pretty_data)
            s = ElementTree.tostring(pretty_data)
        else:
            s = 30 * '-' + '\n'
            for k, v in self.data.items():
                s += "%s:\t%s\n" % (k, v)
        return s.encode('utf-8')

    # Shared properties:
    # Almost all JSSObjects have at least name and id properties, so provide a
    # convenient accessor.
    def name(self):
        if isinstance(self.data, ElementTree.Element):
            return self.data.findtext('name') or \
                    self.data.findtext('general/name')
        else:
            return  self.data['name']

    def id(self):
        if isinstance(self.data, ElementTree.Element):
            id_ = self.data.findtext('id') or self.data.findtext('general/id')
        else:
            id_ = self.data['id']
        return int(id_)


class JSSDeviceObject(JSSObject):
    """Provides convenient accessors for properties of devices.

    This is helpful since Computers and MobileDevices allow us to query
    based on these properties.

    """
    def udid(self):
        if isinstance(self.data, ElementTree.Element):
            return self.data.findtext('general/udid')
        elif 'udid' in self.data:
            return  self.data['udid']
        else:
            return "Load object to retrieve."

    def serial_number(self):
        if isinstance(self.data, ElementTree.Element):
            return self.data.findtext('general/serial_number')
        elif 'serial_number' in self.data:
            return  self.data['serial_number']
        else:
            return "Load object to retrieve."


class ActivationCode(JSSObject):
    _url = '/activationcode'
    can_delete = False
    can_post = False
    can_list = False


class Category(JSSObject):
    _url = '/categories'


class Computer(JSSDeviceObject):
    _url = '/computers'
    search_types = {'name': '/name/', 'serial_number': '/serialnumber/',
                    'udid': '/udid/', 'macaddress': '/macadress/'}

    def mac_addresses(self):
        """Return a list of mac addresses for this device."""
        # Computers don't tell you which network device is which.
        if isinstance(self.data, ElementTree.Element):
            mac_addresses = [self.data.findtext('general/mac_address')]
            if self.data.findtext('general/alt_mac_address'):
                mac_addresses.append(self.data.findtext(\
                        'general/alt_mac_address'))
            return mac_addresses
        else:
            return "Load object to retrieve."


class ComputerCheckIn(JSSObject):
    _url = '/computercheckin'
    can_delete = False
    can_list = False
    can_post = False


class ComputerCommand(JSSObject):
    _url = '/computercommands'
    can_delete = False
    can_put = False


class ComputerGroup(JSSObject):
    _url = '/computergroups'


class MobileDevice(JSSDeviceObject):
    _url = '/mobiledevices'
    search_types = {'name': '/name/', 'serial_number': '/serialnumber/',
                    'udid': '/udid/', 'macaddress': '/macadress/'}

    def wifi_mac_address(self):
        if isinstance(self.data, ElementTree.Element):
            return self.data.findtext('general/wifi_mac_address')
        else:
            return  self.data['wifi_mac_address']

    def bluetooth_mac_address(self):
        if isinstance(self.data, ElementTree.Element):
            return self.data.findtext('general/bluetooth_mac_address') or \
                    self.data.findtext('general/mac_address')
        elif wifi_mac_address in self.data:
            return  self.data['wifi_mac_address'] or \
        self.data['mac_address'] or None
        else:
            return "Load object to retrieve."

class MobileDeviceConfigurationProfile(JSSObject):
    _url = '/mobiledeviceconfigurationprofiles'


class MobileDeviceGroup(JSSObject):
    _url = '/mobiledevicegroups'


class Policy(JSSObject):
    _url = '/policies'
