#!/usr/bin/env python
# Copyright (C) 2014-2017 Shea G Craig
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""jss.py

Classes representing a JSS, and its available API calls, represented
as JSSObjects.
"""
from __future__ import print_function

from __future__ import absolute_import
try:
    import cPickle  # Python 2.X
except ImportError:
    import _pickle as cPickle  # Python 3+

import sys
import gzip
import os
import platform
import re
import json
from xml.etree import ElementTree

sys.path.insert(0, '/Library/AutoPkg/JSSImporter')
import requests

try:
    from UserDict import UserDict  # Python 2.X
except ImportError:
    from collections import UserDict  # Python 3.3+

# from jss.nsurlsession_adapter import NSURLSessionAdapter
from .curl_adapter import CurlAdapter
from .auth import UAPIAuth
from .distribution_points import DistributionPoints
from .exceptions import GetError, PutError, PostError, DeleteError
from .jssobject import JSSObject
from . import jssobjects
from . import uapiobjects
from .queryset import QuerySet
from .tools import error_handler, quote_and_encode


# Pylint wants us to store our many attributes in a dictionary.
# However, to maintain backwards compatibility with the interface,
# we can't do that.
# pylint: disable=too-many-instance-attributes, too-many-public-methods
class JSS(object):
    """Represents a JAMF Software Server, with object search methods.

    Setup a JSS for making API requests.

    Provide either a JSSPrefs object OR specify url, user, and
    password to init. Other parameters are optional.

    Attributes:
        base_url (str): Full URL to the JSS, with port.
        user (str): API username.
        password (str): API password for user.
        token (str, optional): UAPI authorization token.
        repo_prefs (list): List of dicts of repository configuration data.
        verbose (bool): Whether to include extra output.
        session: "Session" used to make all HTTP requests through
            whichever network adapter is in use (default is the requests adapter).
        ssl_verify (bool): Whether to verify SSL traffic from the JSS
            is genuine.
        distribution_points (:obj:`DistributionPoints`): DistributionPoints
        max_age (int): Number of seconds cached object information
            should be kept before re-retrieving. Defaults to '-1'.

            Possible values:
                -1: Keep cached data forever, or until manually
                    retrieved with the `JSSObject.retrieve()` method.
                0: Retrieve data from data for every access.
                positive number: Number of seconds to keep.
        uapi (:obj:`UAPI`): Reference to the UAPI transport facade.
        api (:obj:`JSSAPI`): Reference to the classic API facade.

    Args:
        jss_prefs (:obj:`JSSPrefs`): A JSSPrefs object.
        url (str): String, full URL to a JSS, with port.
        user (str): API Username.
        password (str): API Password.

            repo_prefs: A list of dicts with repository names and
                passwords.
            repos: (Optional) List of file repositories dicts to
                    connect.
                repo dicts:
                    Each file-share distribution point requires:
                        name: String name of the distribution point.
                            Must match the value on the JSS.
                        password: String password for the read/write
                            user.
        repo_prefs (list): A list of dicts with repository names and passwords.

            repos: (Optional) List of file repositories dicts to
            connect.
                repo dicts:
                    Each file-share distribution point requires:
                        name: String name of the distribution point.
                            Must match the value on the JSS.
                        password: String password for the read/write
                            user.

                    This form uses the distributionpoints API call to
                    determine the remaining information. There is also
                    an explicit form; See distribution_points package
                    for more info

                    CDP and JDS types require one dict for the master,
                    with key:
                        type: String, either "CDP" or "JDS".

        ssl_verify (bool): Boolean whether to verify SSL traffic from the
            JSS is genuine.
        verbose (bool): Boolean whether to include extra output.
    """

    class UAPI(object):
        """This object represents the UAPI. All UAPI search methods will be attached here."""
        def __init__(self, jss, url=None):
            self.jss = jss
            self._base_url = url
            self.max_age = -1

        @property
        def base_url(self):
            """The URL to the Casper JSS, including port if needed."""
            return self._base_url

        @base_url.setter
        def base_url(self, url):
            """The URL to the Casper JSS, including port if needed."""
            # Remove the frequently included yet incorrect trailing slash.
            self._base_url = url.rstrip("/")

        @property
        def url(self):  # type: () -> str
            return "%s/%s" % (self.base_url, "uapi")

    class JSSAPI(object):
        """This object represents the XML API. All regular API search methods will be attached here."""
        def __init__(self, jss, url=None):
            self.jss = jss
            self._base_url = url

        @property
        def base_url(self):
            """The URL to the Casper JSS, including port if needed."""
            return self._base_url

        @base_url.setter
        def base_url(self, url):
            """The URL to the Casper JSS, including port if needed."""
            # Remove the frequently included yet incorrect trailing slash.
            self._base_url = url.rstrip("/")

        @property
        def url(self):  # type: () -> str
            return "%s/%s" % (self.base_url, "JSSResource")

    # pylint: disable=too-many-arguments
    def __init__(
        self, jss_prefs=None, url=None, user=None, password=None,
        repo_prefs=None, ssl_verify=True, verbose=False, **kwargs):

        if jss_prefs is not None:
            url = jss_prefs.url
            user = jss_prefs.user
            password = jss_prefs.password
            repo_prefs = jss_prefs.repos
            ssl_verify = jss_prefs.verify
            suppress_warnings = jss_prefs.suppress_warnings

        # TODO: This method currently accepts '**kwargs' to soften
        # the deprecation of the urllib warnings removal.

        self.base_url = url

        if 'adapter' in kwargs:
            self.session = kwargs['adapter']
        else:
            self.session = requests.session()

        self.user = user
        self.password = password
        self.token = None  # For uapi
        self.repo_prefs = repo_prefs if repo_prefs else []
        self.verbose = verbose
        self.ssl_verify = ssl_verify

        self.distribution_points = DistributionPoints(self)
        self.max_age = -1
        self.uapi = JSS.UAPI(self, url)
        self.api = JSS.JSSAPI(self, url)

    # pylint: disable=too-many-arguments

    @property
    def _url(self):
        """The URL to the Casper JSS API endpoints. Get only."""
        return self.api.url

    @property
    def base_url(self):
        """The URL to the Casper JSS, including port if needed."""
        return self._base_url

    @base_url.setter
    def base_url(self, url):
        """The URL to the Casper JSS, including port if needed."""
        # Remove the frequently included yet incorrect trailing slash.
        self._base_url = url.rstrip("/")

    @property
    def user(self):
        """Username used to connect to the Casper API"""
        return self.session.auth[0]

    @user.setter
    def user(self, value):
        """Username used to connect to the Casper API.

        Args:
            value (str): username.
        """
        auth = self.session.auth
        password = auth[1] if auth else ''
        self.session.auth = (value, password)

    @property
    def password(self):
        """Password used to connect to the Casper API"""
        return self.session.auth[1]

    @password.setter
    def password(self, value):
        """Password used to connect to the Casper API.

        Args:
            value (str): password.
        """
        auth = self.session.auth
        user = auth[0] if auth else ''
        self.session.auth = (user, value)

    @property
    def ssl_verify(self):
        """Boolean value for whether to verify SSL traffic is valid."""
        return self.session.verify

    @ssl_verify.setter
    def ssl_verify(self, value):
        """Boolean value for whether to verify SSL traffic is valid.

        Args:
            value: Boolean.
        """
        self.session.verify = value

    def mount_network_adapter(self, network_adapter):
        """Mount a network adapter that uses the Requests API.

        The existing user, password, and ssl_verify values are
        transferred to the new adapter.

        Args:
            network_adapter: A network adapter object that uses the
                basic Requests API. Included in python-jss are the
                CurlAdapter and RequestsAdapter.
        """
        auth = (self.user, self.password)
        ssl_verify = self.ssl_verify
        self.session = network_adapter
        self.user, self.password = auth
        self.ssl_verify = ssl_verify

    def get(self, url_path, headers=None, **kwargs):
        # type: (str) -> Union[ElementTree.Element, dict, bytes]
        """GET a url, handle errors, and return an etree.

        In general, it is better to use a higher level interface for
        API requests, like the search methods on this class, or the
        JSSObjects themselves.

        Args:
            url_path: String API endpoint path to GET (e.g. "packages")
            headers: [Optional] headers to add to the request

        Returns:
            ElementTree.Element for the XML returned from the JSS if the response was XML,
            dict if the response had Content-Type for json,
            bytes for anything else

        Raises:
            GetError if provided url_path has a >= 400 response, for
            example, if an object queried for does not exist (404). Will
            also raise GetError for bad XML.

            This behavior will change in the future for 404/Not Found
            to returning None.
        """
        request_url = os.path.join(self.base_url, quote_and_encode(url_path))
        if headers is None:  # Fall back to XML to support python-jss prior to addition of UAPI
            headers = {'Content-Type': 'text/xml', 'Accept': 'text/xml'}

        response = self.session.get(request_url, headers=headers, **kwargs)

        if response.status_code == 200 and self.verbose:
            print("GET %s: Success." % request_url)
        elif response.status_code >= 400:
            error_handler(GetError, response)

        if 'text/xml' in response.headers['content-type']:
            # ElementTree in python2 only accepts bytes.
            try:
                xmldata = ElementTree.fromstring(response.content)
                return xmldata
            except ElementTree.ParseError:
                raise GetError("Error Parsing XML:\n%s" % response.content)
        elif response.headers['content-type'].startswith('application/json'):
            return response.json()
        else:
            return response.content

    def post(self, url_path, data=None):
        # type: (str, Union[ElementTree.Element, dict]) -> str
        """POST an object to the JSS. For creating new objects only.

        The JSS responds with the new object's ID number if successful.

        Args:
            url_path: String API endpoint path to POST (e.g.
                "packages/id/0")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class.

        Returns:
            str ID number of the newly created object.

        Raises:
            PostError if provided url_path has a >= 400 response.
        """
        # The JSS expects a post to ID 0 to create an object

        request_url = os.path.join(self.base_url, quote_and_encode(url_path))
        headers = {}

        if isinstance(data, ElementTree.Element):
            data = ElementTree.tostring(data, encoding='UTF-8')
            headers = {'Content-Type': 'text/xml', 'Accept': 'text/xml'}
        elif isinstance(data, dict):
            data = json.dumps(data)
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        elif isinstance(data, UserDict):
            data = json.dumps(data.data)
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        else:
            headers = {'Content-Type': 'application/octet-stream', 'Accept': '*/*'}

        response = self.session.post(request_url, data=data, headers=headers)

        if response.status_code == 201 and self.verbose:
            print("POST %s: Success" % request_url)
        elif response.status_code >= 400:
            error_handler(PostError, response)

        if 'text/xml' in response.headers['content-type']:
            id_ = re.search(r"<id>([0-9]+)</id>", response.content.decode("utf-8")).group(1)
        else:
            return response

        return id_

    def put(self, url_path, data):
        # type: (str, Union[ElementTree.Element, dict]) -> str
        """Update an existing object on the JSS.

        In general, it is better to use a higher level interface for
        updating objects, namely, making changes to a JSSObject subclass
        and then using its save method.

        Args:
            url_path: String API endpoint path to PUT, with ID (e.g.
                "packages/id/<object ID>")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class.

        Raises:
            PutError if provided url_path has a >= 400 response.
        """
        request_url = os.path.join(self.base_url, quote_and_encode(url_path))
        headers = {}

        if isinstance(data, ElementTree.Element):
            data = ElementTree.tostring(data, encoding='UTF-8')
            headers = {'Content-Type': 'text/xml', 'Accept': 'text/xml'}
        elif isinstance(data, dict):
            data = json.dumps(data)
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        elif isinstance(data, UserDict):
            data = json.dumps(data.data)
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        else:
            raise TypeError('Could not PUT unrecognised data type')

        response = self.session.put(request_url, data=data, headers=headers)

        if response.status_code == 201 and self.verbose:
            print("PUT %s: Success." % request_url)
        elif response.status_code >= 400:
            error_handler(PutError, response)

    def delete(self, url_path, data=None):
        # type: (str, Optional[Union[ElementTree.Element, dict]]) -> None
        """Delete an object from the JSS.

        In general, it is better to use a higher level interface for
        deleting objects, namely, using a JSSObject's delete method.

        Args:
            url_path: String API endpoint path to DEL, with ID (e.g.
                "packages/id/<object ID>")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class. Most classes don't need this.

        Raises:
            DeleteError if provided url_path has a >= 400 response.
        """
        request_url = os.path.join(self.base_url, quote_and_encode(url_path))
        if data:
            data = ElementTree.tostring(data, encoding='UTF-8')
            response = self.session.delete(request_url, data=data,
                                           headers={'Content-Type': 'text/xml', 'Accept': 'text/xml'})
        else:
            response = self.session.delete(request_url)

        if response.status_code == 200 and self.verbose:
            print("DEL %s: Success." % request_url)
        elif response.status_code >= 400:
            error_handler(DeleteError, response)

    def retrieve_all(self):
        all_search_methods = [
            getattr(self, name) for name in jssobjects.__all__]

        all_objects = {}
        for method in all_search_methods:
            name = method.__name__
            try:
                result = method()
            except GetError as err:
                msg = "Unable to retrieve '{}'"
                if err.status_code == 401:
                    msg += "; permission error"
                print(msg.format(name))
                continue


            # Flat objects can go straight in.
            if isinstance(result, JSSObject):
                all_objects[name] = result.retrieve()
            # Container types need to be retrieved.
            else:
                try:
                    all_objects[name] = result.retrieve_all()
                except GetError:
                    # A failure to get means the object type has zero
                    # results.
                    print(name, " has no results! (GETERRROR)")
                    all_objects[name] = []

        return all_objects

    def pickle_all(self, path, compress=True):
        """Back up entire JSS to a Python Pickle.

        For each object type, retrieve all objects, and then pickle
        the entire smorgasbord. This will almost certainly take a long
        time!

        Pickling is Python's method for serializing/deserializing
        Python objects. This allows you to save a fully functional
        JSSObject to disk, and then load it later, without having to
        retrieve it from the JSS.

        Args:
            path: String file path to the file you wish to (over)write.
                Path will have ~ expanded prior to opening, and `.gz`
                appended if compress=True and it's missing.
            compress (bool): Whether to gzip output. Default is True.
        """
        all_objects = self.retrieve_all()
        path = os.path.expanduser(path)
        gz_ext = ".gz"
        if compress and not path.endswith(gz_ext):
            path = path + gz_ext

        opener = gzip.open if compress else open
        with opener(path, 'wb') as file_handle:
            cPickle.Pickler(
                file_handle, cPickle.HIGHEST_PROTOCOL).dump(all_objects)

    @classmethod
    def from_pickle(cls, path):
        """Load all objects from pickle file and return as dict.

        The dict returned will have keys named the same as the
        JSSObject classes contained, and the values will be
        QuerySets of all full objects of that class (for example,
        the equivalent of my_jss.Computer().retrieve_all()).

        This method can potentially take a very long time!

        Pickling is Python's method for serializing/deserializing
        Python objects. This allows you to save a fully functional
        JSSObject to disk, and then load it later, without having to
        retrieve it from the JSS.

        Args:
            path: String file path to the file you wish to load from.
                Path will have ~ expanded prior to opening.
        """
        gz_magic = "\x1f\x8b\x08"

        # Determine if file is gzipped.
        with open(os.path.expanduser(path), "rb") as pickle:
            pickle_magic = pickle.read(len(gz_magic))
            compressed = True if pickle_magic == gz_magic else False

        opener = gzip.open if compressed else open

        with opener(os.path.expanduser(path), "rb") as pickle:
            return cPickle.Unpickler(pickle).load()

    def write_all(self, path):
        """Back up entire JSS to XML file.

        For each object type, retrieve all objects, and then pickle
        the entire smorgasbord. This will almost certainly take a long
        time!

        Pickling is Python's method for serializing/deserializing
        Python objects. This allows you to save a fully functional
        JSSObject to disk, and then load it later, without having to
        retrieve it from the JSS.

        Args:
            path: String file path to the file you wish to (over)write.
                Path will have ~ expanded prior to opening.
        """
        all_objects = self.retrieve_all()

        with open(os.path.expanduser(path), "w") as ofile:
            root = ElementTree.Element("JSS")
            for obj_type, objects in all_objects.items():
                if objects:
                    sub_element = ElementTree.SubElement(root, obj_type)
                    sub_element.extend(objects)

            et = ElementTree.ElementTree(root)
            et.write(ofile, encoding="utf-8")

    def load_from_xml(self, path):
        """Load all objects from XML file and return as dict.

        The dict returned will have keys named the same as the
        JSSObject classes contained, and the values will be
        QuerySets of all full objects of that class (for example,
        the equivalent of my_jss.Computer().retrieve_all()).

        This method can potentially take a very long time!

        Args:
            path: String file path to the file you wish to load from.
                Path will have ~ expanded prior to opening.
        """
        with open(os.path.expanduser(path), "r") as ifile:
            et = ElementTree.parse(ifile)

        root = et.getroot()

        all_objects = {}
        for child in root:
            obj_type = getattr(jssobjects, child.tag)
            objects = [obj_type(self, obj) for obj in child]
            all_objects[child.tag] = QuerySet(objects)

        return all_objects

    def scrape(self, url_path, session_id=None):
        """This method allows for access to things that don't have an API.

        It's entirely up to you how to implement handling the requests/responses because there's no way Jamf will
        support this.

        Args:
            url_path: String the path to scrape
            session_id: String the session id to use. You can extract a session cookie from a previous response,
                probably using JSESSIONID
        """
        if session_id is None:
            response = self.session.post(self.base_url, data={'username': self.user, 'password': self.password})

            if response.status_code == 200:
                scrape_url = '{}/{}'.format(self.base_url, url_path)
                return self.session.get(scrape_url)

    def version(self):
        return self.JSSUser().version.text

# There's a lot of repetition involved in creating the object query
# methods on JSS, so we create them dynamically at import time.
def add_search_method(cls, name):
    """Add a class-specific search method to a class (JSS)"""
    # Get the actual class to search for, from str `name`
    obj_type = getattr(jssobjects, name)

    # Create a closure over the retrieved class to do our search.
    def api_method(self, data=None, **kwargs):
        """Flexibly search the JSS for objects of type {0}.

            Args:
                data (int, str, :obj:`xml.etree.ElementTree.Element`, optional): Argument to query for.

                    Different queries are performed depending on the type of this arg:
                        - **None** (or provide no argument / default):
                            Search for all objects.
                        - **int**: Search for an object by ID.
                        - **str**: Search for an object by name. Some objects
                            allow 'match' searches, using '*' as the
                            wildcard operator.
                        - :obj:`xml.etree.ElementTree.Element`: create a new
                            object from the Element's data.

                **kwargs:
                    {1}

                    Some classes allow additional filters, subsets, etc,
                    in their queries. Check the object's `allowed_kwargs`
                    attribute for a complete list of implemented keys.

                    Not all classes offer all types of searches, nor are
                    they all necessarily offered in a single query.
                    Consult the Casper API documentation for usage.

                    In general, the key name is applied to the end of the
                    URL, followed by the val; e.g.
                    '<url>/subset/general'.

                    Some common types of extra arguments:

                    subset (list of str or str): XML subelement tags to
                        request (e.g.  ['general', 'purchasing']), OR an
                        '&' delimited string (e.g.
                        'general&purchasing').  Defaults to None.
                    start_date/end_date (str or datetime): Either dates
                        in the form 'YYYY-MM-DD' or a datetime.datetime
                        object.

            Returns:
                QuerySet: If data=None, return all objects of this
                    type.
                {0}: If searching or creating new objects, return an
                    instance of that object.
                None: (FUTURE) Will return None if nothing is found that
                    matches the search criteria.

            Raises:
                GetError for nonexistent objects.
        """
        if not isinstance(data, ElementTree.Element):
            url = obj_type.build_query(data, **kwargs)
            data = self.get(url)

        # TODO: Deprecated and pending removal
        if hasattr(obj_type, "container"):
            data = data.find(obj_type.container)

        if data.find("size") is not None:
            return QuerySet.from_response(obj_type, data, self, **kwargs)
        else:
            return obj_type(self, data)

    # Add in the missing variables to the docstring and set name.
    if hasattr(obj_type, 'allowed_kwargs') and obj_type.allowed_kwargs:
        allowed = ', '.join(obj_type.allowed_kwargs)
        msg = 'Allowed keyword arguments for this class are:\n{}{}'
        kwarg_doc = msg.format(6 * "    ", allowed) if allowed else ""
    else:
        kwarg_doc = "(None supported)"
    api_method.__doc__ = api_method.__doc__.format(name, kwarg_doc)
    api_method.__name__ = name
    # Add the method to the class with the correct name.
    setattr(cls, name, api_method)


# TODO: DRY.. this is just a temp copy/paste to try abstracting
def add_uapi_search_method(cls, name):
    """Add a class-specific search method to a class (JSS)"""
    # Get the actual class to search for, from str `name`
    obj_type = getattr(uapiobjects, name)

    # Create a closure over the retrieved class to do our search.
    def api_method(self, data=None, **kwargs):
        """Flexibly search the JSS for objects of type {0}.

            Args:
                data (None, int, str, xml.etree.ElementTree.Element):
                    Argument to query for. Different queries are
                    performed depending on the type of this arg:
                        None (or provide no argument / default):
                            Search for all objects.
                        int: Search for an object by ID.
                        str: Search for an object by name. Some objects
                            allow 'match' searches, using '*' as the
                            wildcard operator.
                        xml.etree.ElementTree.Element: create a new
                            object from the Element's data.
                kwargs:
                    {1}

                    Some classes allow additional filters, subsets, etc,
                    in their queries. Check the object's `allowed_kwargs`
                    attribute for a complete list of implemented keys.

                    Not all classes offer all types of searches, nor are
                    they all necessarily offered in a single query.
                    Consult the Casper API documentation for usage.

                    In general, the key name is applied to the end of the
                    URL, followed by the val; e.g.
                    '<url>/subset/general'.

                    Some common types of extra arguments:

                    subset (list of str or str): XML subelement tags to
                        request (e.g.  ['general', 'purchasing']), OR an
                        '&' delimited string (e.g.
                        'general&purchasing').  Defaults to None.
                    start_date/end_date (str or datetime): Either dates
                        in the form 'YYYY-MM-DD' or a datetime.datetime
                        object.

            Returns:
                QuerySet: If data=None, return all objects of this
                    type.
                {0}: If searching or creating new objects, return an
                    instance of that object.
                None: (FUTURE) Will return None if nothing is found that
                    matches the search criteria.

            Raises:
                GetError for nonexistent objects.
        """
        if not isinstance(data, dict):
            url = obj_type.build_query(data, **kwargs)
            data = self.jss.get(url, headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                            auth=UAPIAuth(self.jss.user, self.jss.password, "{}/uapi/auth/tokens".format(self.jss.base_url)))

        if isinstance(data, list):
            return [obj_type(self.jss, d) for d in data]
        else:
            return obj_type(self.jss, data)

    # Add in the missing variables to the docstring and set name.
    if hasattr(obj_type, 'allowed_kwargs') and obj_type.allowed_kwargs:
        allowed = ', '.join(obj_type.allowed_kwargs)
        msg = 'Allowed keyword arguments for this class are:\n{}{}'
        kwarg_doc = msg.format(6 * "    ", allowed) if allowed else ""
    else:
        kwarg_doc = "(None supported)"
    api_method.__doc__ = api_method.__doc__.format(name, kwarg_doc)
    api_method.__name__ = name
    # Add the method to the class with the correct name.
    setattr(cls, name, api_method)


# Run `add_search_method` against everything that jss.jssobjects exports.
for jss_class in jssobjects.__all__:
    add_search_method(JSS, jss_class)

for jss_uapi_class in uapiobjects.__all__:
    add_uapi_search_method(JSS.UAPI, jss_uapi_class)

# pylint: disable=too-many-instance-attributes, too-many-public-methods


class JSSObjectFactory(object):
    """Deprecated"""
    pass
