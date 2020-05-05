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
"""jssobject.py

Base Classes representing JSS database objects and their API endpoints
"""
from __future__ import print_function
from __future__ import absolute_import
from six import string_types

import collections
import copy
import sys

try:
    import cPickle  # Python 2.X
except ImportError:
    import _pickle as cPickle  # Python 3+

import datetime as dt
import gzip
import os
from xml.etree import ElementTree

from .exceptions import JSSError, MethodNotAllowedError, PutError, PostError
from .pretty_element import PrettyElement
from jss import tools



DATE_FMT = "%Y/%m/%d-%H:%M:%S.%f"
_MATCH = "match"

# Map Python 2 unicode type for Python 3.
if sys.version_info.major == 3:
    unicode = str

class Identity(dict):
    """Subclass of dict used simply for type-checking."""
    pass


class JSSObject(PrettyElement):
    """Subclass for JSS objects which do not return a list of objects.

    These objects have in common that they cannot be created. They can,
    however, be updated.

    Attributes:
        cached (:obj:`datetime.datetime`, optional): False, or datetime.datetime since last retrieval.
        can_get (bool): whether object allows a GET request.
        can_put (bool): whether object allows a PUT request.
        can_post (bool): whether object allows a POST request.
        can_delete (bool): whether object allows a DEL request.

    Args:
        jss (:obj:`JSS`, optional): JSS to get data from, or None if no JSS
            communications need to be performed.
        data (:obj:`xml.etree.ElementTree.Element`): data for the object
        **kwargs: Unused, but present to support a unified signature
            for all subclasses (which need and use kwargs).
    """
    _endpoint_path = None
    can_get = True
    can_put = True
    can_post = False
    can_delete = False

    __str__ = tools.triggers_cache(tools.element_str)

    def __init__(self, jss, data, **kwargs):
        self.jss = jss
        self.cached = False

        # Turn Elements into PrettyElements (adds pretty printing
        # and fancy attribute finding).
        super(JSSObject, self).__init__(data)

    @property
    def cached(self):
        # Check to see whether cache should be invalidated due to age.
        # If jss.max_age is 0, never cache.
        # If jss.max_age is negative, cache lasts forever.
        if isinstance(self._cached, dt.datetime) and self.jss.max_age > -1:
            max_age = dt.timedelta(seconds=self.jss.max_age)
            now = dt.datetime.now()
            if now - self._cached > max_age:
                self._cached = False

        return self._cached

    @cached.setter
    def cached(self, val):
        self._cached = val

    @classmethod
    def build_query(cls, *args, **kwargs):
        """Return the path for query based on data type and contents.

        Args:
            *args, **kwargs: Left for compatibility with more
            full-featured subclasses' overrides.

        Returns:
            str path construction for this class to query.
        """
        return 'JSSResource/%s' % cls._endpoint_path

    @property
    def url(self):
        """Return the path subcomponent of the url to this object.

        For example: "/activationcode"
        """
        # Flat objects have no ID property, so there is only one URL.
        return 'JSSResource/%s' % self._endpoint_path

    def __repr__(self):
        if isinstance(self.cached, dt.datetime):
            cached = self.cached.strftime(DATE_FMT)
        else:
            cached = bool(self.cached)
        return "<{} cached: {} at 0x{:0x}>".format(
            self.__class__.__name__, cached, id(self))

    def __eq__(self, other):
        # There is no way to really compare as equal without grabbing
        # full data, so trigger a retrieval with `str()`
        return other.__class__ == self.__class__ and str(self) == str(other)

    def __hash__(self):
        # There is no way to really compare as equal without grabbing
        # full data, so trigger a retrieval with `str()`
        return hash(str(self))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Try to save on the way out of the with statement."""
        self.save()

    def _reset_data(self, updated_data):
        """Clear all children of base element and replace with update"""
        self.clear()
        # Convert all incoming data to PrettyElements.
        for child in updated_data.getchildren():
            if not isinstance(child, PrettyElement):
                child = PrettyElement(child)
            self._children.append(child)

    def retrieve(self):
        """Replace this object's data with JSS data, reset cache-age."""
        if self.jss.verbose:
            print("Retrieving data from JSS...")

        xmldata = self.jss.get(self.url)
        self._reset_data(xmldata)
        self.cached = dt.datetime.now()

    def save(self):
        """Update or create a new object on the JSS.

        If this object is not yet on the JSS, this method will create
        a new object with POST, otherwise, it will try to update the
        existing object with PUT.

        Data validation is up to the client; The JSS in most cases will
        at least give you some hints as to what is invalid.
        """
        try:
            self.jss.put(self.url, data=self)
        except PutError as put_error:
            # Something when wrong.
            raise PutError(put_error)

        # Replace current instance's data with new, JSS-validated data.
        self.retrieve()

    def to_file(self, path):
        """Write object XML to path.

        Args:
            path: String file path to the file you wish to (over)write.
                Path will have ~ expanded prior to opening.
        """
        with open(os.path.expanduser(path), "w") as ofile:
            ofile.write(str(self))

    def to_string(self):
        """Return indented object XML as bytes."""
        return self.__str__()

    def pickle(self, path):
        """Write object to python pickle.

        Pickling is Python's method for serializing/deserializing
        Python objects. This allows you to save a fully functional
        JSSObject to disk, and then load it later, without having to
        retrieve it from the JSS.

        Args:
            path: String file path to the file you wish to (over)write.
                Path will have ~ expanded prior to opening.
        """
        with open(os.path.expanduser(path), "wb") as pickle:
            cPickle.Pickler(pickle, cPickle.HIGHEST_PROTOCOL).dump(self)

    def tree(self, depth=None):
        """Return a formatted string representing object's tags

        This method removes redundent entries, so you only see
        unique keys.

        Args:
            depth (int): Depth of the tree to represent. Defaults to
                showing the entire tree.

        Returns:
            str with proper indention and newlines embedded, ready for
            printing.
        """
        results = self._get_tags(self, depth)
        return '\n'.join(results)

    def _get_tags(self, element, depth, level=0):
        results = []
        space = ' '
        indent_size = 4
        if depth is None or level < depth:
            for child in element:
                entry = space * indent_size * level + child.tag
                if entry not in results:
                    results.append(entry)
                    if len(child):
                        results.extend(self._get_tags(child, depth, level + 1))

        return results


# Decorate all public API methods that should trigger a retrieval of the
# object's full data from the JSS.
cache_triggers = (
    '__getitem__', '__len__', '__setitem__', '__str__', 'copy',
    'extend', 'find', 'findall', 'findtext', 'get', 'getchildren',
    'getiterator', 'insert', 'items', 'iter', 'iterfind', 'itertext', 'keys',
    'remove', 'set')

# Ones that block us:
# - Are not methods: 'tail', 'text', 'attrib','tag'
# - Used in setup: 'append',,'__setattr__', 'append',
tools.decorate_class_with_caching(JSSObject, cache_triggers)


class Container(JSSObject):
    """Subclass for members of a type of object.

    This includes the majority of objects in the JSS, for example
    Computers and Policies.

    Attributes:
        cached (:obj:`datetime.datetime`, optional): False, or datetime.datetime since last retrieval.
        can_get (bool): whether object allows a GET request.
        can_put (bool): whether object allows a PUT request.
        can_post (bool): whether object allows a POST request.
        can_delete (bool): whether object allows a DEL request.
        **kwargs: Keyword argument dictionary used in the original
            GET request to retrieve this object. By default, kwargs are
            applied to subsequent `retrieve()` operations unless
            cleared.
        default_search (str): String default search type to utilize for GET.
        search_types (dict): Dict of search types available to object:
            Key: Search type name. At least one must match the
                default_search.
            Val: URL component to use to request via this search_type.
        allowed_kwargs: Tuple of query extensions that are
            available (or sometimes required). Please see the Casper
            API documentation for the final word on how these work.
        root_tag (str): String singular form of object type found in
            containers (e.g. ComputerGroup has a container with tag:
            "computers" holding "computer" elements. The root_tag is
            "computer").
        data_keys (dict): Dictionary of keys to create if instantiating a
            blank object using the _new method.
            Keys: String names of keys to create at top level.
            Vals: Values to set for the key.
                Int and bool values get converted to string.
                Dicts are recursively added (so their keys are added to
                    parent key, etc).
        _id_path (str): URL Path subcomponent used to reference an
            object by ID when querying or posting.
        _name_element (str): XML path to element which contains
            the name of the object, used for creating new objects only.

            Most objects use a name tag at the root, (e.g. "name")
            Some, however, put it into "general/name". If you are
            implementing `data_keys` for an object type not yet
            impelemented, make sure to set this if it differs from the
            default/inherited value.

    Args:
        jss (:obj:`JSS`, optional): JSS to get data from, or None if no JSS
            communications need to be performed.
        data (:obj:`xml.etree.ElementTree.Element`, :obj:`Identity`, str): XML
            data to use for creating the object, a name to use for
            creating a new object, or an Identity object representing
            basic object info.
        **kwargs: Key/value pairs to be added to the object when
            building one from scratch.
    """
    root_tag = "Container"
    can_get = True
    can_put = True
    can_post = True
    can_delete = True
    default_search = "name"
    search_types = {"name": "name"}
    allowed_kwargs = tuple()
    data_keys = {}
    _id_path = "id"
    # TODO: Determine correct values for all endpoints.
    _name_element = "name"

    # Overrides ###############################################################
    def __init__(self, jss, data, **kwargs):
        self.jss = jss
        self._basic_identity = Identity(name="", id="")
        self.kwargs = {}

        if isinstance(data, string_types):
            self._new(data, **kwargs)
            self.cached = "Unsaved"

        elif isinstance(data, ElementTree.Element):
            # Create a new object from passed XML.
            super(Container, self).__init__(jss, data)
            # If this has an ID, assume it's from the JSS and set the
            # cache time, otherwise set it to "Unsaved".
            if data.findtext("id") or data.findtext("general/id"):
                self.cached = dt.datetime.now()
            else:
                self.cached = "Unsaved"

        elif isinstance(data, Identity):
            # This is basic identity information, probably from a
            # listing operation.
            new_xml = PrettyElement(tag=self.root_tag)
            super(Container, self).__init__(jss, new_xml)
            self._basic_identity = Identity(data)
            # Store any kwargs used in retrieving this object.
            self.kwargs = kwargs

        else:
            raise TypeError(
                "JSSObjects data argument must be of type "
                "xml.etree.ElemenTree.Element, Identity, or str")

    def __repr__(self):
        return "<{} with id: {} name: {} cached: {} at 0x{:0x}>".format(
            self.__class__.__name__, self.id, self.name, self.cached,
            id(self))

    def __contains__(self, obj):
        if hasattr(obj, "as_list_data"):
            list_data = obj.as_list_data()
        else:
            return False
        other_id = list_data.findtext("id")
        tags = self.iter(list_data.tag)
        # Give findtext a default non-integer value so that it won't
        # ever compare equal if not found.
        return any(i.findtext("id", "Nay") == other_id for i in tags)

    def retrieve(self, clear_kwargs=False):
        """Replace this object's data with JSS data, reset cache-age.

        Args:
            clear_kwargs (bool): If True, clear the stored request
                kwargs prior to retrieving the full record.
        """
        if clear_kwargs:
            self.kwargs = {}
        super(Container, self).retrieve()

    @classmethod
    def build_query(cls, data, **kwargs):
        """Return the path for query based on data type and contents.

        Args:
            data (int, str, unicode, None): Accepts multiple types.

                Int: Generate URL to object with data ID.
                None: Get basic object GET URL (list).
                String/Unicode: Search for <data> with default_search,
                    usually "name". If the wildcard character, '*' is
                    present, and the object can do 'match' searches,
                    a match search will be performed rather than a
                    normal one.
                String/Unicode with "=": Other searches, for example
                    Computers can be searched by uuid with:
                    "udid=E79E84CB-3227-5C69-A32C-6C45C2E77DF5"
                    See the class "search_types" attribute for options.
            kwargs:
                Some classes allow additional filters, subsets, etc,
                in their queries. Check the object's `allowed_kwargs`
                attribute for a complete list of implemented keys.

                Not all classes offer all types of searches, nor are they
                all necessarily offered in a single query. Consult the
                Casper API documentation for usage.

                In general, the key name is applied to the end of the
                URL, followed by the val; e.g. '<url>/subset/general'.

                subset (list of str or str): XML subelement tags to
                    request (e.g.  ['general', 'purchasing']), OR an '&'
                    delimited string (e.g.  'general&purchasing').
                    Defaults to None.
                start_date/end_date (str or datetime): Either dates in
                    the form 'YYYY-MM-DD' or a datetime.datetime object.

        Returns:
            str path construction for this class to query.
        """
        url_components = ['JSSResource', cls._endpoint_path]

        try:
            data = int(data)
        except (ValueError, TypeError):
            pass
        if isinstance(data, int):
            url_components.extend([cls._id_path, str(data)])

        elif isinstance(data, string_types):
            if "=" in data:
                key, value = data.split("=")   # pylint: disable=no-member
                if key in cls.search_types:
                    url_components.extend([cls.search_types[key], value])

                else:
                    raise TypeError(
                        "This object cannot be queried by %s." % key)

            elif "*" in data and _MATCH in cls.search_types:
                # If wildcard char present, make this a match search if
                # possible
                url_components.extend([cls.search_types[_MATCH], data])
            elif data:
                url_components.extend(
                    [cls.search_types[cls.default_search], data])

        url_components.extend(cls._process_kwargs(kwargs))

        url = os.path.join(*url_components)

        return url

    @classmethod
    def _process_kwargs(cls, kwargs):
        kwarg_urls = []
        if kwargs and all(key in cls.allowed_kwargs for key in kwargs):
            kwargs = cls._handle_kwargs(kwargs)
            for key, val in kwargs.items():
                kwarg_urls.extend(cls._urlify_arg(key, val))
        return kwarg_urls

    @classmethod
    def _handle_kwargs(cls, kwargs):
        """Do nothing. Can be overriden by classes which need it."""
        return kwargs

    @classmethod
    def _urlify_arg(cls, key, val):
        """Convert keyword arguments' values to proper format for GET"""
        if key == 'subset':
            if not isinstance(val, list):
                val = val.split("&")

            # If this is not a "basic" subset, and it's missing
            # "general", add it in, because we need the ID.
            if all(k not in val for k in ("general", "basic")):
                val.append("general")

            return ['subset', "&".join(val)]

        elif key == 'date_range':
            start, end = val
            fmt = lambda s: s.strftime('%Y-%m-%d')
            start = start if isinstance(start, string_types) else fmt(end)
            end = end if isinstance(end, string_types) else fmt(end)
            return ['{}_{}'.format(start, end)]

        else:
            return [key, val]

    @property
    def url(self):
        """Return the path subcomponent of the url to this object.

        For example: "computers/id/451"
        """
        url_components = ['JSSResource', self._endpoint_path, self._id_path, self.id]
        url_components.extend(self._process_kwargs(self.kwargs))
        return os.path.join(*url_components)

    def save(self):
        """Update or create a new object on the JSS.

        If this object is not yet on the JSS, this method will create
        a new object with POST, otherwise, it will try to update the
        existing object with PUT.

        Data validation is up to the client; The JSS in most cases will
        at least give you some hints as to what is invalid.
        """
        # Object probably exists if it has an ID (user can't assign
        # one).
        if self.can_put and self.id != "0":
            # The JSS will reject PUT requests for objects that do not have
            # a category. The JSS assigns a name of "No category assigned",
            # which it will reject. Therefore, if that is the category
            # name, changed it to "", which is accepted.
            categories = [elem for elem in self.findall("category")]
            categories.extend([elem for elem in self.findall("category/name")])
            for cat_tag in categories:
                if cat_tag.text == "No category assigned":
                    cat_tag.text = ""

            super(Container, self).save()

        elif self.can_post:
            try:
                id_ = self.jss.post(self.url, data=self)
            except PostError as err:
                raise PostError(err)

            self._basic_identity["id"] = id_
            # Replace current instance's data with new, JSS-validated data.
            # and update cached time.
            self.retrieve()

        else:
            raise MethodNotAllowedError(self.__class__.__name__)

    # Methods #################################################################
    def _new(self, name, **kwargs):
        """Create a new JSSObject with name and "keys".

        Generate a default XML template for this object, based on
        the class attribute "keys".

        Args:
            name: String name of the object to use as the
                object's name property.
            kwargs:
                Accepted keyword args can be viewed by checking the
                "data_keys" class attribute. Typically, they include all
                top-level keys, and non-duplicated keys used elsewhere.

                Values will be cast to string. (Int 10, bool False
                become string values "10" and "false").

                Ignores kwargs that aren't in object's keys attribute.
        """
        new_xml = PrettyElement(tag=self.root_tag)
        super(Container, self).__init__(self.jss, new_xml)
        self.cached = "Unsaved"

        # Name is required, so set it outside of the helper func.
        current_tag = self
        for path_element in self._name_element.split("/"):
            ElementTree.SubElement(current_tag, path_element)
            current_tag = current_tag.find(path_element)

        current_tag.text = name

        for item in self.data_keys.items():
            self._set_xml_from_keys(self, item, **kwargs)

    def _set_xml_from_keys(self, root, item, **kwargs):
        """Create SubElements of root with kwargs.

        Args:
            root: Element to add SubElements to.
            item: Tuple key/value pair from self.data_keys to add.
            kwargs:
                For each item in self.data_keys, if it has a
                corresponding kwarg, create a SubElement at root with
                the kwarg's value.

                Int and bool values will be cast to string. (Int 10,
                bool False become string values "10" and "false").

                Dicts will be recursively added to their key's Element.
        """
        key, val = item
        target_key = root.find(key)
        if target_key is None:
            target_key = ElementTree.SubElement(root, key)

        if isinstance(val, dict):
            for dict_item in val.items():
                self._set_xml_from_keys(target_key, dict_item, **kwargs)
            return

        # Convert kwarg data to the appropriate string.
        # TODO: Factor out repeated kwargs[key] usage
        if key in kwargs:
            kwarg = kwargs[key]
            if isinstance(kwarg, bool):
                kwargs[key] = str(kwargs[key]).lower()
            elif kwarg is None:
                kwargs[key] = ""
            elif isinstance(kwarg, int):
                kwargs[key] = str(kwargs[key])
            elif isinstance(kwarg, JSSObject):
                kwargs[key] = kwargs[key].name

        target_key.text = kwargs.get(key, val)

    @property
    def basic(self):
        """Returns a copy of the basic identity information

        For most objects, this is just ID and name. Computers have a
        'basic' subset that includes some other data as well.

        The returned data is a copy to enforce being read-only.
        """
        return copy.copy(self._basic_identity)

    @property
    def name(self):
        """Return object name or None."""
        if not self.cached:
            # name = self._basic_name
            name = self._basic_identity["name"]
        else:
            name = self.findtext("name") or self.findtext("general/name")
        return name

    @name.setter
    def name(self, name):
        if self.findtext("name"):
            path = "name"
        elif self.findtext("general/name"):
            path = "general/name"
        else:
            raise JSSError("Name property couldn't be found!")
        # self._basic_name = self.find('name').text = name
        self._basic_identity["name"] = self.find('name').text = name

    @property
    def id(self):   # pylint: disable=invalid-name
        """Return object ID or None."""
        # Most objects have ID nested in general. Groups don't.

        # After much consideration, I will treat id's as strings. We
        # can't assign ID's, so there's no need to perform arithmetic on
        # them, and having to convert to str all over the place is
        # gross. str equivalency still works.
        if not self.cached or self.cached == "Unsaved":
            # id_ = self._basic_id
            id_ = self._basic_identity["id"]
        else:
            id_ = self.findtext("id") or self.findtext("general/id")
        # If no ID has been found, this object hasn't been POSTed to the
        # JSS. New objects use the ID "0".
        return id_ or "0"

    def as_list_data(self):
        """Return an Element to be used in a list.

        Most lists want an element with tag of root_tag, and
        subelements of id and name.

        Returns:
            Element: list representation of object.
        """
        element = PrettyElement(self.root_tag)
        id_ = ElementTree.SubElement(element, "id")
        id_.text = self.id
        name = ElementTree.SubElement(element, "name")
        name.text = self.name
        return element

    def delete(self, data=None):
        """Delete this object from the JSS."""
        if not self.can_delete:
            raise MethodNotAllowedError(self.__class__.__name__)
        if data:
            self.jss.delete(self.url, data=data)
        else:
            self.jss.delete(self.url)

    def _handle_location(self, location):
        """Return an element located at location with flexible args.

        Args:
            location: String xpath to use in an Element.find search OR
                an Element (which is simply returned).

        Returns:
            The found Element.

        Raises:
            ValueError if the location is a string that results in a
            find of None.
        """
        if not isinstance(location, ElementTree.Element):
            element = self.find(location)
            if element is None:
                raise ValueError("Invalid path!")
        else:
            element = location
        return element

    def set_bool(self, location, value):
        """Set a boolean value.

        Casper booleans in XML are string literals of "true" or "false".
        This method sets the text value of "location" to the correct
        string representation of a boolean.

        Args:
            location: Element or a string path argument to find()
            value: Boolean or string value to set. (Accepts
            "true"/"True"/"TRUE"; all other strings are False).
        """
        element = self._handle_location(location)
        if isinstance(value, string_types):
            value = True if value.upper() == "TRUE" else False
        elif not isinstance(value, bool):
            raise ValueError
        if value is True:
            element.text = "true"
        else:
            element.text = "false"

    def add_object_to_path(self, obj, location):
        """Add an object of type Container to location.

        This method determines the correct list representation of an
        object and adds it to "location". For example, add a Computer to
        a ComputerGroup. The ComputerGroup will now have a child
        Computers/Computer tag with subelements "name" and "id".

        Args:
            obj: A Container subclass.
            location: Element or a string path argument to find()

        Returns:
            Element for the object just added.
        """
        location = self._handle_location(location)
        location.append(obj.as_list_data())
        results = [item for item in location.getchildren() if
                   item.findtext("id") == obj.id][0]
        return results

    def remove_object_from_list(self, obj, list_element):
        """Remove an object from a list element.

        Args:
            obj: Accepts JSSObjects, id's, and names
            list_element: Accepts an Element or a string path to that
                element
        """
        list_element = self._handle_location(list_element)

        if isinstance(obj, Container):
            results = [item for item in list_element.getchildren() if
                       item.findtext("id") == obj.id]
        elif isinstance(obj, (int, string_types)):
            results = [item for item in list_element.getchildren() if
                       item.findtext("id") == str(obj) or
                       item.findtext("name") == obj]

        if len(results) == 1:
            list_element.remove(results[0])
        elif len(results) > 1:
            raise ValueError("There is more than one matching object at that "
                             "path!")

    def clear_list(self, list_element):
        """Clear an Element or everything below a path.

        For example, to clear all Computers in a ComputerGroup:
            `computer_group_instance.clear_list("computers")`

        Args:
            list_element: Accepts an Element or a string path to that
                element, to remove.
        """
        list_element = self._handle_location(list_element)
        list_element.clear()

    @classmethod
    def from_file(cls, jss, filename):
        """Create a new JSSObject from an external XML file.

        Args:
            jss: A JSS object.
            filename: String path to an XML file.
        """
        tree = ElementTree.parse(filename)
        root = tree.getroot()
        return cls(jss, root)

    @classmethod
    def from_string(cls, jss, xml_string):
        """Creates a new JSSObject from a string or unicode.

        Args:
            jss: A JSS object.
            xml_string (str or unicode): XML file data used to create
                object.
        """
        # ElementTree.fromstring in python2 really wants bytes.
        if isinstance(xml_string, unicode):
            xml_string = xml_string.encode('UTF-8')
        root = ElementTree.fromstring(xml_string)
        return cls(jss, root)

    @classmethod
    def from_pickle(cls, path):
        """Load from pickle file.

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

    def to_pickle(self, path, compress=True):
        """Write this object to a Python Pickle.

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
        path = os.path.expanduser(path)
        gz_ext = ".gz"
        if compress and not path.endswith(gz_ext):
            path = path + gz_ext

        opener = gzip.open if compress else open
        with opener(path, 'wb') as file_handle:
            cPickle.Pickler(
                file_handle, cPickle.HIGHEST_PROTOCOL).dump(self)


class Group(Container):
    """Abstract class for ComputerGroup and MobileDeviceGroup."""

    def add_criterion(self, name, priority, and_or, search_type, value):   # pylint: disable=too-many-arguments
        """Add a search criteria object to a smart group.

        Args:
            name: String Criteria type name (e.g. "Application Title")
            priority: Int or Str number priority of criterion.
            and_or: Str, either "and" or "or".
            search_type: String Criteria search type. (e.g. "is", "is
                not", "member of", etc). Construct a SmartGroup with the
                criteria of interest in the web interface to determine
                what range of values are available.
            value: String value to search for/against.
        """
        criterion = SearchCriteria(name, priority, and_or, search_type, value)
        self.criteria.append(criterion)

    @property
    def is_smart(self):
        """Returns boolean for whether group is Smart."""
        result = False
        if self.findtext("is_smart") == "true":
            result = True
        return result

    @is_smart.setter
    def is_smart(self, value):
        """Set group is_smart property to value.

        Args:
            value: Boolean.
        """
        self.set_bool("is_smart", value)
        if value is True:
            if self.find("criteria") is None:
                # pylint: disable=attribute-defined-outside-init
                self.criteria = ElementTree.SubElement(self, "criteria")
                # pylint: enable=attribute-defined-outside-init

    def add_device(self, device, container):
        """Add a device to a group. Wraps JSSObject.add_object_to_path.

        Args:
            device: A JSSObject to add (as list data), to this object.
            location: Element or a string path argument to find()
        """
        # There is a size tag which the JSS manages for us, so we can
        # ignore it.
        if self.findtext("is_smart") == "false":
            self.add_object_to_path(device, container)
        else:
            # Technically this isn't true. It will strangely accept
            # them, and they even show up as members of the group!
            raise ValueError("Devices may not be added to smart groups.")

    def has_member(self, device_object):
        """Return bool whether group has a device as a member.

        Args:
            device_object (Computer or MobileDevice). Membership is
            determined by ID, as names can be shared amongst devices.
        """
        if device_object.tag == "computer":
            container_search = "computers/computer"
        elif device_object.tag == "mobile_device":
            container_search = "mobile_devices/mobile_device"
        else:
            raise ValueError

        return len([device for device in self.findall(container_search) if
                    device.findtext("id") == device_object.id]) is not 0


# class Scoped(Container):
#     """Abstract class for a container that supports a <scope> element."""
#
#     def add_object_to_scope(self, obj):
#         """Add an object to the appropriate scope block.
#
#         Args:
#             obj: JSSObject to add to scope. Accepted subclasses are:
#                 Computer
#                 ComputerGroup
#                 Building
#                 Department
#
#         Raises:
#             TypeError if invalid obj type is provided.
#         """
#         if isinstance(obj, Computer):
#             self.add_object_to_path(obj, "scope/computers")
#         elif isinstance(obj, ComputerGroup):
#             self.add_object_to_path(obj, "scope/computer_groups")
#         elif isinstance(obj, Building):
#             self.add_object_to_path(obj, "scope/buildings")
#         elif isinstance(obj, Department):
#             self.add_object_to_path(obj, "scope/departments")
#         else:
#             raise TypeError
#
#     def clear_scope(self):
#         """Clear all objects from the scope, including exclusions."""
#         clear_list = ["computers", "computer_groups", "buildings",
#                       "departments", "limit_to_users/user_groups",
#                       "limitations/users", "limitations/user_groups",
#                       "limitations/network_segments", "exclusions/computers",
#                       "exclusions/computer_groups", "exclusions/buildings",
#                       "exclusions/departments", "exclusions/users",
#                       "exclusions/user_groups", "exclusions/network_segments"]
#         for section in clear_list:
#             self.clear_list("%s%s" % ("scope/", section))
#
#     def add_object_to_exclusions(self, obj):
#         """Add an object to the appropriate scope exclusions
#         block.
#
#         Args:
#             obj: JSSObject to add to exclusions. Accepted subclasses
#                     are:
#                 Computer
#                 ComputerGroup
#                 Building
#                 Department
#
#         Raises:
#             TypeError if invalid obj type is provided.
#         """
#         if isinstance(obj, Computer):
#             self.add_object_to_path(obj, "scope/exclusions/computers")
#         elif isinstance(obj, ComputerGroup):
#             self.add_object_to_path(obj, "scope/exclusions/computer_groups")
#         elif isinstance(obj, Building):
#             self.add_object_to_path(obj, "scope/exclusions/buildings")
#         elif isinstance(obj, Department):
#             self.add_object_to_path(obj, "scope/exclusions/departments")
#         else:
#             raise TypeError
#
#     def add_object_to_limitations(self, obj):
#         """Add an object to the appropriate scope limitations
#         block.
#
#         Args:
#             obj: JSSObject to add to limitations. Accepted subclasses
#                 are:
#                     User
#                     UserGroup
#                     NetworkSegment
#                     IBeacon
#
#         Raises:
#             TypeError if invalid obj type is provided.
#         """
#         if isinstance(obj, User):
#             self.add_object_to_path(obj, "scope/limitations/users")
#         elif isinstance(obj, UserGroup):
#             self.add_object_to_path(obj, "scope/limitations/user_groups")
#         elif isinstance(obj, NetworkSegment):
#             self.add_object_to_path(obj, "scope/limitations/network_segments")
#         elif isinstance(obj, IBeacon):
#             self.add_object_to_path(obj, "scope/limitations/ibeacons")
#         else:
#             raise TypeError
#

class SearchCriteria(PrettyElement):
    """Object for encapsulating a smart group search criteria."""
    root_tag = "criterion"

    def __init__(self, name, priority, and_or, search_type, value):   # pylint: disable=too-many-arguments
        """Init a SearchCriteria.

        Args:
            name: String Criteria type name (e.g. "Application Title")
            priority: Int or Str number priority of criterion.
            and_or: Str, either "and" or "or".
            search_type: String Criteria search type. (e.g. "is", "is
                not", "member of", etc). Construct a SmartGroup with the
                criteria of interest in the web interface to determine
                what range of values are available.
            value: String value to search for/against.
        """
        super(SearchCriteria, self).__init__(tag=self.root_tag)
        crit_name = ElementTree.SubElement(self, "name")
        crit_name.text = name
        crit_priority = ElementTree.SubElement(self, "priority")
        crit_priority.text = str(priority)
        crit_and_or = ElementTree.SubElement(self, "and_or")
        crit_and_or.text = and_or
        crit_search_type = ElementTree.SubElement(self, "search_type")
        crit_search_type.text = search_type
        crit_value = ElementTree.SubElement(self, "value")
        crit_value.text = value
