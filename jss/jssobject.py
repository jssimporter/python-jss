#!/usr/bin/env python
# Copyright (C) 2014, 2015 Shea G Craig <shea.craig@da.org>
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


from xml.etree import ElementTree

from .exceptions import (JSSUnsupportedSearchMethodError,
                         JSSMethodNotAllowedError, JSSPutError, JSSPostError)
from .tools import element_repr


# python-jss is intended to allow easy, pythonic access to the JSS. As
# such, a heavy emphasis is placed its use for interactive discovery
# and exploration. Because JSSObjects are subclassed from Element, the
# __repr__ method is changed to our custom, pretty-printing one. This
# allows things like Element.find("general") to return something more
# useful than just the tag name when not assigned.
ElementTree.Element.__repr__ = element_repr


class SearchCriteria(ElementTree.Element):
    """Object for encapsulating a smart group search criteria."""
    list_type = "criterion"

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
        super(SearchCriteria, self).__init__(tag=self.list_type)
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

    def makeelement(self, tag, attrib):
        """Return an Element."""
        # We use ElementTree.SubElement() a lot. Unfortunately, it
        # relies on a super() call to its __class__.makeelement(), which
        # will fail due to the method resolution order / multiple
        # inheritance of our objects (they have an editor AND a template
        # or JSSObject parent class).
        # This handles that issue.
        return ElementTree.Element(tag, attrib)


class JSSObject(ElementTree.Element):
    """Base class for all JSS API objects.

    Class Attributes:
        can_list: Bool whether object allows a list GET request.
        can_get: Bool whether object allows a GET request.
        can_put: Bool whether object allows a PUT request.
        can_post: Bool whether object allows a POST request.
        can_delete: Bool whether object allows a DEL request.
        id_url: String URL piece to append to use the ID property for
            requests. (Usually "/id/")
        container: String pluralized object name. This is used in one
            place-Account and AccountGroup use the same API call.
            container is used to differentiate the results.
        default_search: String default search type to utilize for GET.
        search_types: Dict of search types available to object:
            Key: Search type name. At least one must match the
                default_search.
            Val: URL component to use to request via this search_type.
        list_type: String singular form of object type found in
            containers (e.g. ComputerGroup has a container with tag:
            "computers" holding "computer" elements. The list_type is
            "computer").
        data_keys: Dictionary of keys to create if instantiating a
            blank object using the _new method.
            Keys: String names of keys to create at top level.
            Vals: Values to set for the key.
                Int and bool values get converted to string.
                Dicts are recursively added (so their keys are added to
                    parent key, etc).

    Private Class Attributes:
        _name_path: String XML path to where the name of the object
            is stored. Most objects use a name tag at the root, so this
            is not used. Some, however, put it into general/game. If
            you are implementing data_keys for an object type not yet
            impelemented, make sure to set this if it differs from the
            default/inherited value.
    """

    _url = None
    can_list = True
    can_get = True
    can_put = True
    can_post = True
    can_delete = True
    id_url = "/id/"
    _name_path = ""
    container = ""
    default_search = "name"
    search_types = {"name": "/name/"}
    list_type = "JSSObject"
    data_keys = {}

    def __init__(self, jss, data, **kwargs):
        """Initialize a new JSSObject

        Args:
            jss: JSS object.
            data: xml.etree.ElementTree.Element data to use for
                creating the object OR a string name to use for creating
                a new object (provided it has an implemented _new()
                method.
        """
        self.jss = jss
        if isinstance(data, basestring):
            super(JSSObject, self).__init__(tag=self.list_type)
            self._new(data, **kwargs)
        elif isinstance(data, ElementTree.Element):
            super(JSSObject, self).__init__(tag=data.tag)
            for child in data.getchildren():
                self.append(child)
        else:
            raise TypeError("JSSObjects data argument must be of type "
                            "xml.etree.ElemenTree.Element, or a string for the"
                            " name.")

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
        # Name is required, so set it outside of the helper func.
        if self._name_path:
            parent = self
            for path_element in self._name_path.split("/"):
                self._set_xml_from_keys(parent, (path_element, None))
                parent = parent.find(path_element)

            parent.text = name
        else:
            ElementTree.SubElement(self, "name").text = name

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

    def makeelement(self, tag, attrib):
        """Return an Element."""
        # We use ElementTree.SubElement() a lot. Unfortunately, it
        # relies on a super() call to its __class__.makeelement(), which
        # will fail due to the class NOT being Element.
        # This handles that issue.
        return ElementTree.Element(tag, attrib)

    @classmethod
    def get_url(cls, data):
        """Return the URL for a get request based on data type.

        Args:
            data: Accepts multiple types.
                Int: Generate URL to object with data ID.
                None: Get basic object GET URL (list).
                String/Unicode: Search for <data> with default_search,
                    usually "name".
                String/Unicode with "=": Other searches, for example
                    Computers can be search by uuid with:
                    "udid=E79E84CB-3227-5C69-A32C-6C45C2E77DF5"
                    See the class "search_types" attribute for options.
        """
        try:
            data = int(data)
        except (ValueError, TypeError):
            pass
        if isinstance(data, int):
            return "%s%s%s" % (cls._url, cls.id_url, data)
        elif data is None:
            return cls._url
        elif isinstance(data, basestring):
            if "=" in data:
                key, value = data.split("=")   # pylint: disable=no-member
                if key in cls.search_types:
                    return "%s%s%s" % (cls._url, cls.search_types[key], value)
                else:
                    raise JSSUnsupportedSearchMethodError(
                        "This object cannot be queried by %s." % key)
            else:
                return "%s%s%s" % (cls._url,
                                   cls.search_types[cls.default_search], data)
        else:
            raise ValueError

    @classmethod
    def get_post_url(cls):
        """Return the post URL for this object class."""
        return "%s%s%s" % (cls._url, cls.id_url, "0")

    @property
    def url(self):
        """Return the path subcomponent of the url to this object.

        For example: "/computers/id/451"
        """
        if self.id:
            url = "%s%s%s" % (self._url, self.id_url, self.id)
        else:
            url = None
        return url

    def get_object_url(self):
        """Return the path subcomponent of the url to this object.

        For example: "/computers/id/451"

        Deprecated for url property. Will remove in a future release!
        """
        return self.url

    def delete(self):
        """Delete this object from the JSS."""
        if not self.can_delete:
            raise JSSMethodNotAllowedError(self.__class__.__name__)
        self.jss.delete(self.url)

    def save(self):
        """Update or create a new object on the JSS.

        If this object is not yet on the JSS, this method will create
        a new object with POST, otherwise, it will try to update the
        existing object with PUT.

        Data validation is up to the client; The JSS in most cases will
        at least give you some hints as to what is invalid.
        """
        # Object probably exists if it has an ID (user can't assign
        # one).  The only objects that don't have an ID are those that
        # cannot list.
        if self.can_put and (not self.can_list or self.id):
            # The JSS will reject PUT requests for objects that do not have
            # a category. The JSS assigns a name of "No category assigned",
            # which it will reject. Therefore, if that is the category
            # name, changed it to "", which is accepted.
            categories = [elem for elem in self.findall("category")]
            categories.extend([elem for elem in self.findall("category/name")])
            for cat_tag in categories:
                if cat_tag.text == "No category assigned":
                    cat_tag.text = ""

            try:
                self.jss.put(self.url, self)
                updated_data = self.jss.get(self.url)
            except JSSPutError as put_error:
                # Something when wrong.
                raise JSSPutError(put_error)
        elif self.can_post:
            url = self.get_post_url()
            try:
                updated_data = self.jss.post(self.__class__, url, self)
            except JSSPostError as err:
                raise JSSPostError(err)
        else:
            raise JSSMethodNotAllowedError(self.__class__.__name__)

        # Replace current instance's data with new, JSS-validated data.
        self.clear()
        for child in updated_data.getchildren():
            self._children.append(child)

    @property
    def name(self):
        """Return object name or None."""
        return self.findtext("name") or self.findtext("general/name")

    @property
    def id(self):   # pylint: disable=invalid-name
        """Return object ID or None."""
        # Most objects have ID nested in general. Groups don't.
        # After much consideration, I will treat id's as strings. We
        # can't assign ID's, so there's no need to perform arithmetic on
        # them, and having to convert to str all over the place is
        # gross. str equivalency still works.
        return self.findtext("id") or self.findtext("general/id")

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
        if isinstance(value, basestring):
            value = True if value.upper() == "TRUE" else False
        elif not isinstance(value, bool):
            raise ValueError
        if value is True:
            element.text = "true"
        else:
            element.text = "false"

    def add_object_to_path(self, obj, location):
        """Add an object of type JSSContainerObject to location.

        This method determines the correct list representation of an
        object and adds it to "location". For example, add a Computer to
        a ComputerGroup. The ComputerGroup will not have a child
        Computers/Computer tag with subelements "name" and "id".

        Args:
            obj: A JSSContainerObject subclass.
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

        if isinstance(obj, JSSObject):
            results = [item for item in list_element.getchildren() if
                       item.findtext("id") == obj.id]
        elif isinstance(obj, (int, basestring)):
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
        """Creates a new JSSObject from an XML string.

        Args:
            jss: A JSS object.
            xml_string: String XML file data used to create object.
        """
        root = ElementTree.fromstring(xml_string)
        return cls(jss, root)


class JSSContainerObject(JSSObject):
    """Subclass for types which can contain lists of other objects.

    e.g. Computers, Policies.
    """
    list_type = "JSSContainerObject"

    def as_list_data(self):
        """Return an Element to be used in a list.

        Most lists want an element with tag of list_type, and
        subelements of id and name.

        Returns:
            Element: list representation of object.
        """
        element = ElementTree.Element(self.list_type)
        id_ = ElementTree.SubElement(element, "id")
        id_.text = self.id
        name = ElementTree.SubElement(element, "name")
        name.text = self.name
        return element


class JSSGroupObject(JSSContainerObject):
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


class JSSDeviceObject(JSSContainerObject):
    """Abstact class for device types."""

    @property
    def udid(self):
        """Return device's UDID or None."""
        return self.findtext("general/udid")

    @property
    def serial_number(self):
        """Return device's serial number or None."""
        return self.findtext("general/serial_number")


class JSSFlatObject(JSSObject):
    """Subclass for JSS objects which do not return a list of objects.

    These objects have in common that they cannot be created. They can,
    however, be updated.
    """
    search_types = {}

    def _new(self, name, **kwargs):
        """Do nothing. This object cannot be created."""
        raise JSSPostError("This object type cannot be created.")

    @classmethod
    def get_url(cls, data):
        """Return the URL to this object.

        Args:
            data: Must be None. This is in-place to mimic other, more
                featured object types.
        """
        if data is not None:
            raise JSSUnsupportedSearchMethodError(
                "This object cannot be queried by %s." % data)
        else:
            return cls._url

    def get_object_url(self):
        """Return the url to this object. Deprecated.

        Use url instead.
        """
        return self.url

    @property
    def url(self):
        """Return the path subcomponent of the url to this object.

        For example: "/activationcode"
        """
        # Flat objects have no ID property, so there is only one URL.
        return self.get_url(None)


