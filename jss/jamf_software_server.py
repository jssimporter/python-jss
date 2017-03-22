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


import cPickle
import os
import re
from xml.etree import ElementTree

from . import distribution_points
from .curl_adapter import CurlAdapter
from .exceptions import (JSSGetError, JSSPutError, JSSPostError,
                         JSSDeleteError, JSSMethodNotAllowedError)
from .jssobject import JSSFlatObject, Identity
from . import jssobjects
from .jssobjectlist import JSSObjectList
from .tools import error_handler, quote_and_encode


# Pylint wants us to store our many attributes in a dictionary.
# However, to maintain backwards compatibility with the interface,
# we can't do that.
# pylint: disable=too-many-instance-attributes, too-many-public-methods
class JSS(object):
    """Represents a JAMF Software Server, with object search methods.

    Attributes:
        base_url: String, full URL to the JSS, with port.
        user: String API username.
        password: String API password for user.
        repo_prefs: List of dicts of repository configuration data.
        verbose: Boolean whether to include extra output.
        jss_migrated: Boolean whether JSS has had scripts "migrated".
            Used to determine whether to upload scripts in Script
            object XML or as files to the distribution points.
        session: "Session" used to make all HTTP requests through
            whichever network adapter is in use (default is CurlAdapter).
        ssl_verify: Boolean whether to verify SSL traffic from the JSS
            is genuine.
        factory: JSSObjectFactory object for building JSSObjects.
        distribution_points: DistributionPoints
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self, jss_prefs=None, url=None, user=None, password=None,
        repo_prefs=None, ssl_verify=True, verbose=False, jss_migrated=False,
        **kwargs):
        """Setup a JSS for making API requests.

        Provide either a JSSPrefs object OR specify url, user, and
        password to init. Other parameters are optional.

        Args:
            jss_prefs:  A JSSPrefs object.
            url: String, full URL to a JSS, with port.
            user: API Username.
            password: API Password.

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

                        This form uses the distributionpoints API call to
                        determine the remaining information. There is also
                        an explicit form; See distribution_points package
                        for more info

                        CDP and JDS types require one dict for the master,
                        with key:
                            type: String, either "CDP" or "JDS".

            ssl_verify: Boolean whether to verify SSL traffic from the
                JSS is genuine.
            verbose: Boolean whether to include extra output.
            jss_migrated: Boolean whether JSS has had scripts
                "migrated". Used to determine whether to upload scripts
                in Script object XML or as files to the distribution
                points.
        """
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

        self.session = CurlAdapter()
        self.user = user
        self.password = password
        self.repo_prefs = repo_prefs if repo_prefs else []
        self.verbose = verbose
        self.jss_migrated = jss_migrated
        self.ssl_verify = ssl_verify

        self.factory = JSSObjectFactory(self)
        self.distribution_points = distribution_points.DistributionPoints(self)

    # pylint: disable=too-many-arguments

    @property
    def _url(self):
        """The URL to the Casper JSS API endpoints. Get only."""
        return "%s/%s" % (self.base_url, "JSSResource")

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

    def get(self, url_path):
        """GET a url, handle errors, and return an etree.

        In general, it is better to use a higher level interface for
        API requests, like the search methods on this class, or the
        JSSObjects themselves.

        Args:
            url_path: String API endpoint path to GET (e.g. "/packages")

        Returns:
            ElementTree.Element for the XML returned from the JSS.

        Raises:
            JSSGetError if provided url_path has a >= 400 response, for
            example, if an object queried for does not exist (404). Will
            also raise JSSGetError for bad XML.

            This behavior will change in the future for 404/Not Found
            to returning None.
        """
        request_url = "%s%s" % (self._url, quote_and_encode(url_path))
        response = self.session.get(request_url)

        if response.status_code == 200 and self.verbose:
            print "GET %s: Success." % request_url
        elif response.status_code >= 400:
            error_handler(JSSGetError, response)

        # ElementTree in python2 only accepts bytes.
        try:
            xmldata = ElementTree.fromstring(response.content)
        except ElementTree.ParseError:
            raise JSSGetError("Error Parsing XML:\n%s" % response.content)

        return xmldata

    def post(self, obj_class, url_path, data):
        """POST an object to the JSS. For creating new objects only.

        The data argument is POSTed to the JSS, which, upon success,
        returns the complete XML for the new object. This data is used
        to get the ID of the new object, and, via the
        JSSObjectFactory, GET that ID to instantiate a new JSSObject of
        class obj_class.

        This allows incomplete (but valid) XML for an object to be used
        to create a new object, with the JSS filling in the remaining
        data. Also, only the JSS may specify things like ID, so this
        method retrieves those pieces of data.

        In general, it is better to use a higher level interface for
        creating new objects, namely, creating a JSSObject subclass and
        then using its save method.

        Args:
            obj_class: JSSObject subclass to create from POST.
            url_path: String API endpoint path to POST (e.g.
                "/packages/id/0")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class.

        Returns:
            An object of class obj_class, representing a newly created
            object on the JSS. The data is what has been returned after
            it has been parsed by the JSS and added to the database.

        Raises:
            JSSPostError if provided url_path has a >= 400 response.
        """
        # The JSS expects a post to ID 0 to create an object

        request_url = "%s%s" % (self._url, quote_and_encode(url_path))
        data = ElementTree.tostring(data, encoding='UTF-8')
        response = self.session.post(request_url, data=data)

        if response.status_code == 201 and self.verbose:
            print "POST %s: Success" % request_url
        elif response.status_code >= 400:
            error_handler(JSSPostError, response)

        id_ = int(re.search(r"<id>([0-9]+)</id>", response.text).group(1))

        return self.factory.get_object(obj_class, id_)

    def put(self, url_path, data):
        """Update an existing object on the JSS.

        In general, it is better to use a higher level interface for
        updating objects, namely, making changes to a JSSObject subclass
        and then using its save method.

        Args:
            url_path: String API endpoint path to PUT, with ID (e.g.
                "/packages/id/<object ID>")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class.
        Raises:
            JSSPutError if provided url_path has a >= 400 response.
        """
        request_url = "%s%s" % (self._url, quote_and_encode(url_path))
        data = ElementTree.tostring(data, encoding='UTF-8')
        response = self.session.put(request_url, data=data)

        if response.status_code == 201 and self.verbose:
            print "PUT %s: Success." % request_url
        elif response.status_code >= 400:
            error_handler(JSSPutError, response)

    def delete(self, url_path, data=None):
        """Delete an object from the JSS.

        In general, it is better to use a higher level interface for
        deleting objects, namely, using a JSSObject's delete method.

        Args:
            url_path: String API endpoint path to DEL, with ID (e.g.
                "/packages/id/<object ID>")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class. Most classes don't need this.

        Raises:
            JSSDeleteError if provided url_path has a >= 400 response.
        """
        request_url = "%s%s" % (self._url, quote_and_encode(url_path))
        if data:
            data = ElementTree.tostring(data, encoding='UTF-8')
            response = self.session.delete(request_url, data=data)
        else:
            response = self.session.delete(request_url)

        if response.status_code == 200 and self.verbose:
            print "DEL %s: Success." % request_url
        elif response.status_code >= 400:
            error_handler(JSSDeleteError, response)

    def pickle_all(self, path):
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
                Path will have ~ expanded prior to opening.
        """
        all_search_methods = [(name, self.__getattribute__(name)) for name in
                              dir(self) if name[0].isupper()]
        # all_search_methods = [("Account", self.__getattribute__("Account")), ("Package", self.__getattribute__("Package"))]
        all_objects = {}
        for method in all_search_methods:
            result = method[1]()
            if isinstance(result, JSSFlatObject):
                all_objects[method[0]] = result
            else:
                try:
                    all_objects[method[0]] = result.retrieve_all()
                except JSSGetError:
                    # A failure to get means the object type has zero
                    # results.
                    print method[0], " has no results! (GETERRROR)"
                    all_objects[method[0]] = []
        # all_objects = {method[0]: method[1]().retrieve_all()
        #                for method in all_search_methods}
        with open(os.path.expanduser(path), "wb") as pickle:
            cPickle.Pickler(pickle, cPickle.HIGHEST_PROTOCOL).dump(all_objects)

    def from_pickle(cls, path):
        """Load all objects from pickle file and return as dict.

        The dict returned will have keys named the same as the
        JSSObject classes contained, and the values will be
        JSSObjectLists of all full objects of that class (for example,
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
        with open(os.path.expanduser(path), "rb") as pickle:
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
        all_search_methods = [(name, self.__getattribute__(name)) for name in
                              dir(self) if name[0].isupper()]
        # all_search_methods = [("Account", self.__getattribute__("Account")), ("Package", self.__getattribute__("Package"))]
        all_objects = {}
        for method in all_search_methods:
            result = method[1]()
            if isinstance(result, JSSFlatObject):
                all_objects[method[0]] = result
            else:
                try:
                    all_objects[method[0]] = result.retrieve_all()
                except JSSGetError:
                    # A failure to get means the object type has zero
                    # results.
                    print method[0], " has no results! (GETERRROR)"
                    all_objects[method[0]] = []
        # all_objects = {method[0]: method[1]().retrieve_all()
        #                for method in all_search_methods}
        with open(os.path.expanduser(path), "w") as ofile:
            root = ElementTree.Element("JSS")
            for obj_type, objects in all_objects.items():
                if objects is not None:
                    sub_element = ElementTree.SubElement(root, obj_type)
                    sub_element.extend(objects)

            et = ElementTree.ElementTree(root)
            et.write(ofile, encoding="utf-8")

    def load_from_xml(self, path):
        """Load all objects from XML file and return as dict.

        The dict returned will have keys named the same as the
        JSSObject classes contained, and the values will be
        JSSObjectLists of all full objects of that class (for example,
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
            obj_type = self.__getattribute__(child.tag)
            objects = [obj_type(obj) for obj in child]
            all_objects[child.tag] = JSSObjectList(self.factory, None, objects)

        return all_objects


# There's a lot of repetition involved in creating the object query
# methods on JSS, so we create them dynamically at import time.
def add_search_method(cls, name):
    """Add a class-specific search method to a class (JSS)"""
    # Get the actual class to search for, from str `name`
    obj_type = getattr(jssobjects, name)

    # Create a closure over the retrieved class to do our search.
    def api_method(self, data=None, subset=None):
        """Flexibly search the JSS for objects of type {0}.

            Args:
                data (None, int, str, xml.etree.ElementTree.Element):
                    Argument to query for. Different queries are
                    performed depending on the type of this arg:
                        None (or provide no argument / default):
                            Search for all objects.
                        int: Search for an object by ID.
                        str: Search for an object by name.
                        xml.etree.ElementTree.Element: create a new
                            object from the Element's data.
                subset (list of str or str): Some JSS types allow you to
                    request a subset of data be returned. See the JSS API
                    documentation for a complete list. This argument is
                    {1} for this type.

                    This argument should be either A list of XML
                    subelement tags to request or an '&' delimited str.
                    (e.g. ['general', 'purchasing'] or
                    'general&purchasing')

            Returns:
                JSSObjectList: If data=None, return all objects of this
                    type.
                {0}: If searching or creating new objects, return an
                    instance of that object.
                None: (FUTURE) Will return None if nothing is found that
                    matches the search criteria.

            Raises:
                JSSGetError for nonexistent objects.
        """
        return self.factory.get_object(obj_type, data, subset)

    # Add in the missing variables to the docstring and set name.
    subset_support = 'supported' if obj_type.can_subset else 'unsupported'
    api_method.__doc__ = api_method.__doc__.format(name, subset_support)
    api_method.__name__ = name
    # Add the method to the class with the correct name.
    setattr(cls, name, api_method)


# Run `add_search_method` against everything that jss.jssobjects exports.
for jss_class in jssobjects.__all__:
    add_search_method(JSS, jss_class)


# pylint: disable=too-many-instance-attributes, too-many-public-methods

class JSSObjectFactory(object):
    """Create JSSObjects intelligently based on a single parameter.

    Attributes:
        jss: Copy of a JSS object to which API requests are
        delegated.
    """

    def __init__(self, jss):
        """Configure a JSSObjectFactory

        Args:
            jss: JSS object to which API requests should be
                 delegated.
        """
        self.jss = jss

    def get_object(self, obj_class, data=None, subset=None):
        """Return a subclassed JSSObject instance by querying for
        existing objects or posting a new object.

        Args:
            obj_class: The JSSObject subclass type to search for or
                create.
            data: The data parameter performs different operations
                depending on the type passed.

                - None: Perform a list operation, or for non-container
                  objects, return all data.
                - int: Retrieve an object with ID of <data>.
                - str: Retrieve an object with name of <str>. For some
                  objects, this may be overridden to include searching
                  by other criteria. See those objects for more info.
                - xml.etree.ElementTree.Element: Create a new object from
                  xml.
            subset:
                A list of XML subelement tags to request (e.g.
                ['general', 'purchasing']), OR an '&' delimited string
                (e.g. 'general&purchasing'). This is not supported for
                all JSSObjects.

        Returns:
            JSSObjectList: for empty or None arguments to data.
            JSSObject: Returns an object of type obj_class for searches
                and new objects.
            (FUTURE) Will return None if nothing is found that match
                the search criteria.

        Raises:
            TypeError: if subset not formatted properly.
            JSSMethodNotAllowedError: if you try to perform an operation
                not supported by that object type.
            JSSGetError: If object searched for is not found.
            JSSPostError: If attempted object creation fails.
        """
        if subset:
            if not isinstance(subset, list):
                if isinstance(subset, basestring):
                    subset = subset.split("&")
                else:
                    raise TypeError

        if data is None:
            return self.get_list(obj_class, data, subset)
        elif isinstance(data, (basestring, int)):
            return self.get_individual_object(obj_class, data, subset)
        elif isinstance(data, ElementTree.Element):
            return self.get_new_object(obj_class, data)
        else:
            raise ValueError

    def get_list(self, obj_class, data, subset):
        """Get a list of objects as JSSObjectList.

        Args:
            obj_class: The JSSObject subclass type to search for.
            data: None
            subset: Some objects support a subset for listing; namely
                Computer, with subset="basic".

        Returns:
            JSSObjectList
        """
        url = obj_class.get_url(data)
        if obj_class.can_list and obj_class.can_get:
            if (subset and len(subset) == 1 and subset[0].upper() ==
                    "BASIC") and obj_class is jssobjects.Computer:
                url += "/subset/basic"

            result = self.jss.get(url)

            if obj_class.container:
                result = result.find(obj_class.container)

            return self._build_jss_object_list(result, obj_class)

        # Single object

        elif obj_class.can_get:
            xmldata = self.jss.get(url)
            return obj_class(self.jss, xmldata)
        else:
            raise JSSMethodNotAllowedError(
                obj_class.__class__.__name__)

    def get_individual_object(self, obj_class, data, subset):
        """Return a JSSObject of type obj_class searched for by data.

        Args:
            obj_class: The JSSObject subclass type to search for.
            data: The data parameter performs different operations
                depending on the type passed.
                int: Retrieve an object with ID of <data>.
                str: Retrieve an object with name of <str>. For some
                    objects, this may be overridden to include searching
                    by other criteria. See those objects for more info.
            subset:
                A list of XML subelement tags to request (e.g.
                ['general', 'purchasing']), OR an '&' delimited string
                (e.g. 'general&purchasing'). This is not supported for
                all JSSObjects.

        Returns:
            JSSObject: Returns an object of type obj_class.
            (FUTURE) Will return None if nothing is found that match
                the search criteria.

        Raises:
            TypeError: if subset not formatted properly.
            JSSMethodNotAllowedError: if you try to perform an operation
                not supported by that object type.
            JSSGetError: If object searched for is not found.
        """
        if obj_class.can_get:
            url = obj_class.get_url(data)
            if subset:
                if not "general" in subset:
                    subset.append("general")
                url += "/subset/%s" % "&".join(subset)

            xmldata = self.jss.get(url)

            # Some name searches may result in multiple found
            # objects. e.g. A computer search for "MacBook Pro" may
            # return ALL computers which have not had their name
            # changed.
            if xmldata.find("size") is not None:
                return self._build_jss_object_list(xmldata, obj_class)
            else:
                return obj_class(self.jss, xmldata)
        else:
            raise JSSMethodNotAllowedError(obj_class.__class__.__name__)

    def get_new_object(self, obj_class, data):
        """Create a new object.

        Args:
            obj_class: The JSSObject subclass type to create.
            data: xml.etree.ElementTree.Element; Create a new object
                from xml.

        Returns:
            JSSObject: Returns an object of type obj_class.

        Raises:
            JSSMethodNotAllowedError: if you try to perform an operation
                not supported by that object type.
            JSSPostError: If attempted object creation fails.
        """
        # if obj_class.can_post:
        #     url = obj_class.get_post_url()
        #     return self.jss.post(obj_class, url, data)
        return obj_class(self.jss, data)
        # else:
        #     raise JSSMethodNotAllowedError(obj_class.__class__.__name__)

    def _build_jss_object_list(self, response, obj_class):
        """Build a JSSObject from response."""
        response_objects = [item for item in response
                            if item is not None and
                            item.tag != "size"]
        objects = [
            obj_class(self.jss, data=Identity(obj.findtext('name'), obj.findtext('id')))
            for obj in response_objects]

        return JSSObjectList(self, obj_class, objects)
