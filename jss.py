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
        if preferences_file is None:
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

    def raw_get(self, path):
        """Perform a get operation.
        path: Path to specific object type.
        Returns an ElementTree element.
        
        """
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

    def post(self, url, **kwargs):
        pass

    def put(self, url, **kwargs):
        pass

    def delete(self, url):
        pass

    def get(self, obj_class, idn=None):
        url = obj_class._url
        if idn is not None:
            url = '%s%s%s%s' % (self._url, url, '/id/', str(idn))
            print(url)
        else:
            url = '%s%s' % (self._url, url)

        headers = {'Authorization': "Basic %s" % self.auth}

        response = requests.get(url, headers=headers,
                                 verify=self.ssl_verify)

        if response.status_code == 401:
            raise JSSAuthenticationError('Authentication error: check the ' \
                                         'api username and password')
        elif response.status_code == 404:
            raise JSSGetError("Object %s does not exist!" % url)

        # JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        xmldata = ElementTree.fromstring(jss_results)
        return xmldata

    def list(self, obj_class, **kwargs):
        url = obj_class._url
        url = '%s%s' % (self._url, url)

        headers = {'Authorization': "Basic %s" % self.auth}

        response = requests.get(url, headers=headers,
                                 verify=self.ssl_verify)

        if response.status_code == 401:
            raise JSSAuthenticationError('Authentication error: check the ' \
                                         'api username and password')
        elif response.status_code == 404:
            raise JSSGetError("Object %s does not exist!" % url)

        # JSS returns xml encoded in utf-8
        jss_results = response.text.encode('utf-8')
        xmldata = ElementTree.fromstring(jss_results)

        #l = [obj_class(self, item) for item in xmldata if item is not None]
        l = [obj_class(self, item) for item in xmldata if item is not None and item.tag != 'size']
        if kwargs:
            for k, v in kwargs.items():
                for obj in l:
                    obj.__dict__[k] = str(v)
        return l

    #def Policies(self):



class JSSObject(object):
    """Base class for representing all available JSS API objects."""
    _url = None

    def __init__(self, jss, data=None, **kwargs):
        self.jss = jss

        if data is None or type(data) in [int, str, unicode]:
            data = self.jss.get(self.__class__, data, **kwargs)

        self._setFromDict(data)

        if kwargs:
            for k, v in kwargs.items():
                self.__dict__[k] = v

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
        """Take xml, indent it, and print nicely."""
        #If I ElementTree.parse() I get an ElementTree object, but
        #ElementTree.fromstring() returns an Element object
        #if isinstance(et, ElementTree.ElementTree):
        #    root = et.getroot()
        #else:
        #    root = et
        self.indent(self.data)
        ElementTree.dump(self.data)

    def _get_list_or_object(self, cls, id, **kwargs):
        if id is None:
            return cls.list(self, **kwargs)
        else:
            return cls(self, id, **kwargs)

    @classmethod
    def list(cls, jss, **kwargs):
        return jss.list(cls, **kwargs)

    def _setFromDict(self, data):
        # TODO!
        # data.getchildren, and need to split tag and text manually
        for k, v in data.items():
            if isinstance(v, list):
                self.__dict__[k] = []
                for i in v:
                    self.__dict__[k].append(self._getObject(k, i))
            elif v:
                self.__dict__[k] = self._getObject(k, v)
            else:  # None object
                #self.__dict__[k] = None
                self.__dict__[k] = v.text



#class Policies(JSSObject):
#    _url = '/policies'


class Policy(JSSObject):
    _url = '/policies'
