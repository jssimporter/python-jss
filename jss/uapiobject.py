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
"""uapiobject.py

Base Classes representing JSS database objects and their UAPI endpoints
"""
from __future__ import print_function
from __future__ import absolute_import
from six import string_types

import os
import datetime as dt
import json

from jss import tools
try:
    from UserDict import UserDict  # Python 2.X
except ImportError:
    from collections import UserDict  # Python 3.3+

from .exceptions import JSSError, MethodNotAllowedError, PutError, PostError


DATE_FMT = "%Y/%m/%d-%H:%M:%S.%f"


class UAPIObject(UserDict):
    """Subclass for JSS UAPI objects which do not return a list of objects.

    These objects have in common that they cannot be created. They can,
    however, be updated.

    Class Attributes:
        cached: False, or datetime.datetime since last retrieval.
        can_get: Bool whether object allows a GET request.
        can_put: Bool whether object allows a PUT request.
        can_post: Bool whether object allows a POST request.
        can_delete: Bool whether object allows a DEL request.
    """
    _endpoint_path = None  # type: Optional[str]
    can_get = True         # type: bool
    can_put = True         # type: bool
    can_post = False       # type: bool
    can_delete = False     # type: bool

    def __init__(self, jss, data, **kwargs):
        # type: (JSS, Optional[dict], Optional[dict]) -> None
        """Initialize a new UAPIObject

        Args:
            jss (JSS, None): JSS to get data from, or None if no JSS
                communications need to be performed.
            data: dict data for the object
            kwargs: Unused, but present to support a unified signature
                for all subclasses (which need and use kwargs).
        """
        UserDict.__init__(self, data)
        self.jss = jss
        self.cached = False
        #super(UAPIObject, self).__init__(data)

    @property
    def cached(self):  # type: () -> bool
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
    def cached(self, val):  # type: (bool) -> None
        self._cached = val

    @classmethod
    def build_query(cls, *args, **kwargs):
        # type: (Optional[List[any]], Optional[dict]) -> str
        """Return the path for query based on data type and contents.

        Args:
            *args, **kwargs: Left for compatibility with more
            full-featured subclasses' overrides.

        Returns:
            str path construction for this class to query.
        """
        return 'uapi/%s' % cls._endpoint_path

    @property
    def url(self):  # type: () -> str
        """Return the path subcomponent of the url to this object.

        For example: "/activationcode"
        """
        # Flat objects have no ID property, so there is only one URL.
        return 'uapi/%s' % self._endpoint_path

    def __repr__(self):
        if isinstance(self.cached, dt.datetime):
            cached = self.cached.strftime(DATE_FMT)
        else:
            cached = bool(self.cached)
        return "<{} cached: {} at 0x{:0x}>".format(
            self.__class__.__name__, cached, id(self))

    def retrieve(self):
        """Replace this object's data with JSS data, reset cache-age."""
        if self.jss.verbose:
            print("Retrieving data from JSS...")

        json_data = self.jss.get(self.url, headers={'Accept': 'application/json'})
        self.update(json_data)
        self.cached = dt.datetime.now()

    def save(self):
        """Update or create a new object on the JSS.

        If this object is not yet on the JSS, this method will create
        a new object with POST, otherwise, it will try to update the
        existing object with PUT.

        New: some UAPI endpoints require a POST even if they are a non CRUD object type. The presence of can_post = True
        will determine which method we use, with PUT always being the default.

        Data validation is up to the client; The JSS in most cases will
        at least give you some hints as to what is invalid.
        """
        if self.can_post:
            self.jss.post(self.url, data=self)
        else:
            self.jss.put(self.url, data=self)

        if self.can_get:
            # Replace current instance's data with new, JSS-validated data.
            self.retrieve()

    def to_file(self, path):
        """Write object JSON to path.

        Args:
            path: String file path to the file you wish to (over)write.
                Path will have ~ expanded prior to opening.
        """
        with open(os.path.expanduser(path), "w") as ofile:
            ofile.write(json.dumps(self))

    def to_string(self):
        """Return indented object JSON as bytes."""
        return self.__str__()


class UAPIContainer(UAPIObject):
    """Subclass for members of a type of UAPI object.

    Class Attributes:
        cached: False, "Unsaved" for newly created objects that have
            not been POSTed to the JSS, or datetime.datetime since last
            retrieval.
        kwargs (dict): Keyword argument dictionary used in the original
            GET request to retrieve this object. By default, kwargs are
            applied to subsequent `retrieve()` operations unless
            cleared.
        can_get: Bool whether object allows a GET request.
        can_put: Bool whether object allows a PUT request.
        can_post: Bool whether object allows a POST request.
        can_delete: Bool whether object allows a DEL request.
        default_search: String default search type to utilize for GET.
        search_types: Dict of search types available to object:
            Key: Search type name. At least one must match the
                default_search.
            Val: URL component to use to request via this search_type.
        allowed_kwargs: Tuple of query extensions that are
            available (or sometimes required). Please see the JAMF Pro
            API documentation for the final word on how these work.
        data_keys: Dictionary of keys to create if instantiating a
            blank object using the _new method.
            Keys: String names of keys to create at top level.
            Vals: Values to set for the key.
                Int and bool values get converted to string.
                Dicts are recursively added (so their keys are added to
                    parent key, etc).

    Private Class Attributes:
        _id_path (str): URL Path subcomponent used to reference an
            object by ID when querying or posting.
    """
    can_get = True
    can_put = True
    can_post = True
    can_delete = True
    default_search = "name"  # type: str
    search_types = {"name": "name"}  # type: dict
    allowed_kwargs = tuple()  # type: Tuple[str]
    data_keys = {}  # type: dict
    _id_path = "id"  # type: str

    # Overrides ###############################################################
    def __init__(self, jss, data, **kwargs):
        """Initialize a new JSSObject from scratch or from a python dict.

        data still adheres to the Classic API convention of being able to pass a string which represents
        the object "name", as well as a dict, which will be the actual representation of the object.

        Args:
            jss (JSS, None): JSS object, or None if no communication
                with the JSS is needed.
            data (dict, Identity, str):
                data to use for creating the object, a name to use for
                creating a new object, or an Identity object representing
                basic object info.
            kwargs (str): Key/value pairs to be added to the object when
                building one from scratch.
        """
        self.jss = jss
        # self._basic_identity = Identity(name="", id="")
        self.kwargs = {}

        if isinstance(data, string_types):
            # self._new(data, **kwargs)
            UAPIObject.__init__(self, jss, {"name": data}, **kwargs)
            self.cached = "Unsaved"

        elif isinstance(data, dict):
            # Create a new object from passed XML.
            UAPIObject.__init__(self, jss, data, **kwargs)
            # If this has an ID, assume it's from the JSS and set the
            # cache time, otherwise set it to "Unsaved".
            if 'id' in data and data['id']:
                self.cached = dt.datetime.now()
            else:
                self.cached = "Unsaved"

        # elif isinstance(data, Identity):
        #     # This is basic identity information, probably from a
        #     # listing operation.
        #     new_xml = PrettyElement(tag=self.root_tag)
        #     super(Container, self).__init__(jss, new_xml)
        #     self._basic_identity = Identity(data)
        #     # Store any kwargs used in retrieving this object.
        #     self.kwargs = kwargs

        else:
            raise TypeError(
                "UAPIObjects data argument must be of type "
                "dict")

    def url(self, method='GET'):
        """Return the path subcomponent of the url to this object.

        For example: "computers/id/451"

        UAPI is not consistent with the endpoint name based on which operation you are performing.
        """
        if hasattr(self, '_endpoint_path_' + method.lower()):
            pass

        url_components = [self._endpoint_path, self._id_path, self.id]
        url_components.extend(self._process_kwargs(self.kwargs))
        return os.path.join(*url_components)

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

    def _new(self, name, **kwargs):
        """Create a new UAPIObject with name and "keys".

        Generate a default Dict template for this object, based on
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
        super(UAPIContainer, self).__init__(self.jss, {"name": name})
        UserDict.__init__(self, kwargs)

        # # ignore _name_element
        # for k, v in self.data_keys.items():
        #     self[k] = v
