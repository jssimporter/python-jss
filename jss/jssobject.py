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

Classes representing JSS database objects and their API endpoints
"""


import copy
import mimetypes
import os
import re
import subprocess
from xml.etree import ElementTree

import requests

from .exceptions import *


class SearchCriteria(ElementTree.Element):
    """Object for encapsulating a smart group search criteria."""
    list_type = "criterion"

    def __init__(self, name, priority, and_or, search_type, value):
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
    """

    _url = None
    can_list = True
    can_get = True
    can_put = True
    can_post = True
    can_delete = True
    id_url = "/id/"
    container = ""
    default_search = "name"
    search_types = {"name": "/name/"}
    list_type = "JSSObject"

    def __init__(self, jss, data, **kwargs):
        """Initialize a new JSSObject

        Args:
            jss: JSS object.
            data: xml.etree.ElementTree.Element data to use for
                creating the object OR a string name to use for creating
                a new object (provided it has an implemented new()
                method.
        """
        self.jss = jss
        if isinstance(data, basestring):
            super(JSSObject, self).__init__(tag=self.list_type)
            self.new(data, **kwargs)
        elif isinstance(data, ElementTree.Element):
            super(JSSObject, self).__init__(tag=data.tag)
            for child in data.getchildren():
                self.append(child)
        else:
            raise TypeError("JSSObjects data argument must be of type "
                            "xml.etree.ElemenTree.Element, or a string for the"
                            " name.")

    def new(self, name, **kwargs):
        """Create a new JSSObject with name and blank XML."""
        raise NotImplementedError

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
        else:
            if "=" in data:
                key, value = data.split("=")
                if key in cls.search_types:
                    return "%s%s%s" % (cls._url, cls.search_types[key], value)
                else:
                    raise JSSUnsupportedSearchMethodError(
                        "This object cannot be queried by %s." % key)
            else:
                return "%s%s%s" % (cls._url,
                                   cls.search_types[cls.default_search], data)

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
    def id(self):
        """Return object ID or None."""
        # Most objects have ID nested in general. Groups don't.
        # After much consideration, I will treat id's as strings. We
        # can't assign ID's, so there's no need to perform arithmetic on
        # them, and having to convert to str all over the place is
        # gross. str equivalency still works.
        return self.findtext("id") or self.findtext("general/id")

    def _indent(self, elem, level=0, more_sibs=False):
        """Indent an xml element object to prepare for pretty printing.

        Method is internal to discourage indenting the self._root
        Element, thus potentially corrupting it.

        Args:
            elem: Element to indent.
            level: Int indent level (default is 0)
            more_sibs: Bool, whether to anticipate further siblings.
        """
        i = "\n"
        pad = 4 * " "
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
                if kid.tag == "data":
                    kid.text = "*DATA*"
                self._indent(kid, level + 1, count < num_kids - 1)
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
        """Return a string with indented XML data."""
        # deepcopy so we don't mess with the valid XML.
        pretty_data = copy.deepcopy(self)
        self._indent(pretty_data)
        return ElementTree.tostring(pretty_data).encode("utf-8")

    def pretty_find(self, search):
        """Pretty print the results of a find.

        The inherited find method only prints the tag name and memory
        location when used interactively. This method instead pretty
        prints the element and all of its children as indented XML.

        Args:
            search: xpath passed onto the find method.
        """
        result = self.find(search)
        if result is not None:
            pretty_data = copy.deepcopy(result)
            self._indent(pretty_data)
            print ElementTree.tostring(pretty_data).encode("utf-8")

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
        """
        location = self._handle_location(location)
        location.append(obj.as_list_data())

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
        new_object = cls(jss, data=root)
        return new_object

    @classmethod
    def from_string(cls, jss, xml_string):
        """Creates a new JSSObject from an XML string.

        Args:
            jss: A JSS object.
            xml_string: String XML file data used to create object.
        """
        root = ElementTree.fromstring(xml_string)
        new_object = cls(jss, data=root)
        return new_object


class JSSContainerObject(JSSObject):
    """Subclass for types which can contain lists of other objects.

    e.g. Computers, Policies.
    """
    list_type = "JSSContainerObject"

    def new(self, name, **kwargs):
        """Create an empty XML object.

        Args:
            name: String name of object.
        """
        name_element = ElementTree.SubElement(self, "name")
        name_element.text = name

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

    def add_criterion(self, name, priority, and_or, search_type, value):
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
                self.criteria = ElementTree.SubElement(self, "criteria")

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
        if isinstance(device_object, Computer):
            container_search = "computers/computer"
        elif isinstance(device_object, MobileDevice):
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

    def new(self, name, **kwargs):
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


class Account(JSSContainerObject):
    """JSS account."""
    _url = "/accounts"
    container = "users"
    id_url = "/userid/"
    search_types = {"userid": "/userid/", "username": "/username/",
                    "name": "/username/"}


class AccountGroup(JSSContainerObject):
    """Account groups are groups of users on the JSS.

    Within the API hierarchy they are actually part of accounts, but I
    seperated them.
    """

    _url = "/accounts"
    container = "groups"
    id_url = "/groupid/"
    search_types = {"groupid": "/groupid/", "groupname": "/groupname/",
                    "name": "/groupname/"}


class ActivationCode(JSSFlatObject):
    _url = "/activationcode"
    list_type = "activation_code"
    can_delete = False
    can_post = False
    can_list = False


class AdvancedComputerSearch(JSSContainerObject):
    _url = "/advancedcomputersearches"


class AdvancedMobileDeviceSearch(JSSContainerObject):
    _url = "/advancedmobiledevicesearches"


class AdvancedUserSearch(JSSContainerObject):
    _url = "/advancedusersearches"


class Building(JSSContainerObject):
    _url = "/buildings"
    list_type = "building"


class BYOProfile(JSSContainerObject):
    _url = "/byoprofiles"
    list_type = "byoprofiles"
    can_delete = False
    can_post = False


class Category(JSSContainerObject):
    _url = "/categories"
    list_type = "category"


class Class(JSSContainerObject):
    _url = "/classes"


class Computer(JSSDeviceObject):
    list_type = "computer"
    _url = "/computers"
    search_types = {"name": "/name/", "serial_number": "/serialnumber/",
                    "udid": "/udid/", "macaddress": "/macadress/",
                    "match": "/match/"}

    @property
    def mac_addresses(self):
        """Return a list of mac addresses for this device.

        Computers don't tell you which network device is which.
        """
        mac_addresses = [self.findtext("general/mac_address")]
        if self.findtext("general/alt_mac_address"):
            mac_addresses.append(self.findtext("general/alt_mac_address"))
            return mac_addresses


class ComputerCheckIn(JSSFlatObject):
    _url = "/computercheckin"
    can_delete = False
    can_list = False
    can_post = False


class ComputerCommand(JSSContainerObject):
    _url = "/computercommands"
    can_delete = False
    can_put = False
    # TODO: You _can_ POST computer commands, but it is not yet
    # implemented
    can_post = False


class ComputerConfiguration(JSSContainerObject):
    _url = "/computerconfigurations"
    list_type = "computer_configuration"


class ComputerExtensionAttribute(JSSContainerObject):
    _url = "/computerextensionattributes"


class ComputerGroup(JSSGroupObject):
    _url = "/computergroups"
    list_type = "computer_group"

    def __init__(self, jss, data, **kwargs):
        """Init a ComputerGroup, adding in extra Elements."""
        # Temporary solution to #34.
        # When grabbing a ComputerGroup from the JSS, we don't get the
        # convenience properties for accessing some of the elements
        # that the new() method adds. For now, this just adds in a
        # criteria property. But...
        # TODO(Shea): Find a generic/higher level way to add these
        #   convenience accessors.
        super(ComputerGroup, self).__init__(jss, data, **kwargs)
        self.criteria = self.find("criteria")

    def new(self, name, **kwargs):
        """Create a computer group from scratch.

        Smart groups with no criteria by default select ALL computers.

        Args:
            name: String name of group.
            kwargs: One kwarg of "smart" is accepted, with bool val.
        """
        element_name = ElementTree.SubElement(self, "name")
        element_name.text = name
        # is_smart is a JSSGroupObject @property.
        ElementTree.SubElement(self, "is_smart")
        self.criteria = ElementTree.SubElement(self, "criteria")
        # If specified add is_smart, otherwise default to False.
        self.is_smart = kwargs.get("smart", False)
        self.computers = ElementTree.SubElement(self, "computers")

    def add_computer(self, computer):
        """Add a computer to the group.

        Args:
            computer: A Computer object to add to the group.
        """
        super(ComputerGroup, self).add_device(computer, "computers")

    def remove_computer(self, device):
        """Remove a computer from the group.

        Args:
            computer: A Computer object to add to the group.
        """
        super(ComputerGroup, self).remove_object_from_list(computer, "computers")


class ComputerInventoryCollection(JSSFlatObject):
    _url = "/computerinventorycollection"
    can_list = False
    can_post = False
    can_delete = False


class ComputerInvitation(JSSContainerObject):
    _url = "/computerinvitations"
    can_put = False
    search_types = {"name": "/name/", "invitation": "/invitation/"}


class ComputerReport(JSSContainerObject):
    _url = "/computerreports"
    can_put = False
    can_post = False
    can_delete = False


class Department(JSSContainerObject):
    _url = "/departments"
    list_type = "department"


class DirectoryBinding(JSSContainerObject):
    _url = "/directorybindings"


class DiskEncryptionConfiguration(JSSContainerObject):
    _url = "/diskencryptionconfigurations"


class DistributionPoint(JSSContainerObject):
    _url = "/distributionpoints"


class DockItem(JSSContainerObject):
    _url = "/dockitems"


class EBook(JSSContainerObject):
    _url = "/ebooks"


class FileUpload(object):
    """FileUploads are a special case in the API. They allow you to add
    file resources to a number of objects on the JSS.

    To use, instantiate a new FileUpload object, then use the save()
    method to upload.

    Once the upload has been posted you may only interact with it
    through the web interface. You cannot list/get it or delete it
    through the API.

    However, you can reuse the FileUpload object if you wish, by
    changing the parameters, and issuing another save().
    """
    _url = "fileuploads"

    def __init__(self, j, resource_type, id_type, _id, resource):
        """Prepare a new FileUpload.

        Args:
            j: A JSS object to POST the upload to.
            resource_type:
                String. Acceptable Values:
                    Attachments:
                        computers
                        mobiledevices
                        enrollmentprofiles
                        peripherals
                    Icons:
                        policies
                        ebooks
                        mobiledeviceapplicationsicon
                    Mobile Device Application:
                        mobiledeviceapplicationsipa
                    Disk Encryption
                        diskencryptionconfigurations
            id_type:
                String of desired ID type:
                    id
                    name
            _id: Int or String referencing the identity value of the
                resource to add the FileUpload to.
            resource: String path to the file to upload.
        """
        resource_types = ["computers", "mobiledevices", "enrollmentprofiles",
                          "peripherals", "policies", "ebooks",
                          "mobiledeviceapplicationsicon",
                          "mobiledeviceapplicationsipa",
                          "diskencryptionconfigurations"]
        id_types = ["id", "name"]

        self.jss = j

        # Do some basic error checking on parameters.
        if resource_type in resource_types:
            self.resource_type = resource_type
        else:
            raise JSSFileUploadParameterError("resource_type must be one of: "
                                              "%s" % resource_types)
        if id_type in id_types:
            self.id_type = id_type
        else:
            raise JSSFileUploadParameterError("id_type must be one of: "
                                              "%s" % id_types)
        self._id = str(_id)

        basename = os.path.basename(resource)
        content_type = mimetypes.guess_type(basename)[0]
        self.resource = {"name": (basename, open(resource, "rb"),
                                  content_type)}
        self._set_upload_url()

    def _set_upload_url(self):
        """Generate the full URL for a POST."""
        self._upload_url = "/".join([self.jss._url, self._url,
                                     self.resource_type, self.id_type,
                                     str(self._id)])

    def save(self):
        """POST the object to the JSS."""
        try:
            response = requests.post(self._upload_url,
                                     auth=self.jss.session.auth,
                                     verify=self.jss.session.verify,
                                     files=self.resource)
        except JSSPostError as e:
            if e.status_code == 409:
                raise JSSPostError(e)
            else:
                raise JSSMethodNotAllowedError(self.__class__.__name__)

        if response.status_code == 201:
            if self.jss.verbose:
                print "POST: Success"
                print response.text.encode("utf-8")
        elif response.status_code >= 400:
            self.jss._error_handler(JSSPostError, response)


class GSXConnection(JSSFlatObject):
    _url = "/gsxconnection"
    can_list = False
    can_post = False
    can_delete = False


class IBeacon(JSSContainerObject):
    _url = "/ibeacons"
    list_type = "ibeacon"


class JSSUser(JSSFlatObject):
    """JSSUser is deprecated."""
    _url = "/jssuser"
    can_list = False
    can_post = False
    can_put = False
    can_delete = False
    search_types = {}


class LDAPServer(JSSContainerObject):
    _url = "/ldapservers"

    def search_users(self, user):
        """Search for LDAP users.

        Args:
            user: User to search for. It is not entirely clear how the
                JSS determines the results- are regexes allowed, or
                globbing?

        Returns:
            LDAPUsersResult object.

        Raises:
            Will raise a JSSGetError if no results are found.
        """
        user_url = "%s/%s/%s" % (self.url, "user", user)
        print user_url
        response = self.jss.get(user_url)
        return LDAPUsersResults(self.jss, response)

    def search_groups(self, group):
        """Search for LDAP groups.

        Args:
            group: Group to search for. It is not entirely clear how the
                JSS determines the results- are regexes allowed, or
                globbing?

        Returns:
            LDAPGroupsResult object.

        Raises:
            JSSGetError if no results are found.
        """
        group_url = "%s/%s/%s" % (self.url, "group", group)
        response = self.jss.get(group_url)
        return LDAPGroupsResults(self.jss, response)

    def is_user_in_group(self, user, group):
        """Test for whether a user is in a group.

        There is also the ability in the API to test for whether
        multiple users are members of an LDAP group, but you should just
        call is_user_in_group over an enumerated list of users.

        Args:
            user: String username.
            group: String group name.

        Returns bool.
        """
        search_url = "%s/%s/%s/%s/%s" % (self.url, "group", group,
                                         "user", user)
        response = self.jss.get(search_url)
        # Sanity check
        length = len(response)
        result = False
        if length  == 1:
            # User doesn't exist. Use default False value.
            pass
        elif length == 2:
            if response.findtext("ldap_user/username") == user:
                if response.findtext("ldap_user/is_member") == "Yes":
                    result = True
        elif len(response) >= 2:
            raise JSSGetError("Unexpected response.")
        return result

    @property
    def id(self):
        """Return object ID or None."""
        # LDAPServer's ID is in "connection"
        result = self.findtext("connection/id")
        return result

    @property
    def name(self):
        """Return object name or None."""
        # LDAPServer's name is in "connection"
        result = self.findtext("connection/name")
        return result


class LDAPUsersResults(JSSContainerObject):
    """Helper class for results of LDAPServer queries for users."""
    can_get = False
    can_post = False
    can_put = False
    can_delete = False


class LDAPGroupsResults(JSSContainerObject):
    """Helper class for results of LDAPServer queries for groups."""
    can_get = False
    can_post = False
    can_put = False
    can_delete = False


class LicensedSoftware(JSSContainerObject):
    _url = "/licensedsoftware"


class MacApplication(JSSContainerObject):
    _url = "/macapplications"
    list_type = "mac_application"


class ManagedPreferenceProfile(JSSContainerObject):
    _url = "/managedpreferenceprofiles"


class MobileDevice(JSSDeviceObject):
    """Mobile Device objects include a "match" search type which queries
    across multiple properties.
    """

    _url = "/mobiledevices"
    list_type = "mobile_device"
    search_types = {"name": "/name/", "serial_number": "/serialnumber/",
                    "udid": "/udid/", "macaddress": "/macadress/",
                    "match": "/match/"}

    @property
    def wifi_mac_address(self):
        """Return device's WIFI MAC address or None."""
        return self.findtext("general/wifi_mac_address")

    @property
    def bluetooth_mac_address(self):
        """Return device's Bluetooth MAC address or None."""
        return self.findtext("general/bluetooth_mac_address") or \
            self.findtext("general/mac_address")


class MobileDeviceApplication(JSSContainerObject):
    _url = "/mobiledeviceapplications"


class MobileDeviceCommand(JSSContainerObject):
    _url = "/mobiledevicecommands"
    can_put = False
    can_delete = False
    search_types = {"name": "/name/", "uuid": "/uuid/",
                    "command": "/command/"}
    # TODO: This object _can_ post, but it works a little differently
    # and is not yet implemented
    can_post = False


class MobileDeviceConfigurationProfile(JSSContainerObject):
    _url = "/mobiledeviceconfigurationprofiles"


class MobileDeviceEnrollmentProfile(JSSContainerObject):
    _url = "/mobiledeviceenrollmentprofiles"
    search_types = {"name": "/name/", "invitation": "/invitation/"}


class MobileDeviceExtensionAttribute(JSSContainerObject):
    _url = "/mobiledeviceextensionattributes"


class MobileDeviceInvitation(JSSContainerObject):
    _url = "/mobiledeviceinvitations"
    can_put = False
    search_types = {"invitation": "/invitation/"}


class MobileDeviceGroup(JSSGroupObject):
    _url = "/mobiledevicegroups"
    list_type = "mobile_device_group"

    def add_mobile_device(self, device):
        """Add a mobile_device to the group.

        Args:
            device: A MobileDevice object to add to group.
        """
        super(MobileDeviceGroup, self).add_device(device, "mobile_devices")

    def remove_mobile_device(self, device):
        """Remove a mobile_device from the group.

        Args:
            device: A MobileDevice object to remove from the group.
        """
        super(MobileDeviceGroup, self).remove_object_from_list(
            device, "mobile_devices")


class MobileDeviceProvisioningProfile(JSSContainerObject):
    _url = "/mobiledeviceprovisioningprofiles"
    search_types = {"name": "/name/", "uuid": "/uuid/"}


class NetbootServer(JSSContainerObject):
    _url = "/netbootservers"


class NetworkSegment(JSSContainerObject):
    _url = "/networksegments"


class OSXConfigurationProfile(JSSContainerObject):
    _url = "/osxconfigurationprofiles"


class Package(JSSContainerObject):
    _url = "/packages"
    list_type = "package"

    def new(self, filename, **kwargs):
        """Create a new Package from scratch.

        Args:
            filename: String filename of the package to use for the
                Package object's Display Name (here, "name").
            kwargs:
                Accepted keyword args include:
                    cat_name: Name of category to assign Package.
        """
        name = ElementTree.SubElement(self, "name")
        name.text = filename
        category = ElementTree.SubElement(self, "category")
        category.text = kwargs.get("cat_name")
        fname = ElementTree.SubElement(self, "filename")
        fname.text = filename
        ElementTree.SubElement(self, "info")
        ElementTree.SubElement(self, "notes")
        priority = ElementTree.SubElement(self, "priority")
        priority.text = "10"
        reboot = ElementTree.SubElement(self, "reboot_required")
        reboot.text = "false"
        fut = ElementTree.SubElement(self, "fill_user_template")
        fut.text = "false"
        feu = ElementTree.SubElement(self, "fill_existing_users")
        feu.text = "false"
        boot_volume = ElementTree.SubElement(self, "boot_volume_required")
        boot_volume.text = "true"
        allow_uninstalled = ElementTree.SubElement(self, "allow_uninstalled")
        allow_uninstalled.text = "false"
        ElementTree.SubElement(self, "os_requirements")
        required_proc = ElementTree.SubElement(self, "required_processor")
        required_proc.text = "None"
        switch_w_package = ElementTree.SubElement(self, "switch_with_package")
        switch_w_package.text = "Do Not Install"
        install_if = ElementTree.SubElement(self,
                                            "install_if_reported_available")
        install_if.text = "false"
        reinstall_option = ElementTree.SubElement(self, "reinstall_option")
        reinstall_option.text = "Do Not Reinstall"
        ElementTree.SubElement(self, "triggering_files")
        send_notification = ElementTree.SubElement(self, "send_notification")
        send_notification.text = "false"

    def set_os_requirements(self, requirements):
        """Set package OS Requirements

        Args:
            requirements: A string of comma seperated OS versions. A
                lowercase "x" is allowed as a wildcard, e.g.  "10.9.x"
        """
        self.find("os_requirements").text = requirements

    def set_category(self, category):
        """Set package category

        Args:
            category: String of an existing category's name, or a
                Category object.
        """
        # For some reason, packages only have the category name, not the
        # ID.
        if isinstance(category, Category):
            name = category.name
        else:
            name = category
        self.find("category").text = name


class Peripheral(JSSContainerObject):
    _url = "/peripherals"
    search_types = {}


class PeripheralType(JSSContainerObject):
    _url = "/peripheraltypes"
    search_types = {}


class Policy(JSSContainerObject):
    _url = "/policies"
    list_type = "policy"

    def new(self, name="Unknown", category=None):
        """Create a Policy from scratch.

        Args:
            name: String Policy name
            category: A Category object or string name of the category.
        """
        # General
        self.general = ElementTree.SubElement(self, "general")
        self.name_element = ElementTree.SubElement(self.general, "name")
        self.name_element.text = name
        self.enabled = ElementTree.SubElement(self.general, "enabled")
        self.set_bool(self.enabled, True)
        self.frequency = ElementTree.SubElement(self.general, "frequency")
        self.frequency.text = "Once per computer"
        self.category = ElementTree.SubElement(self.general, "category")
        if category:
            self.category_name = ElementTree.SubElement(self.category, "name")
            if isinstance(category, Category):
                self.category_name.text = category.name
            elif isinstance(category, basestring):
                self.category_name.text = category

        # Scope
        self.scope = ElementTree.SubElement(self, "scope")
        self.computers = ElementTree.SubElement(self.scope, "computers")
        self.computer_groups = ElementTree.SubElement(self.scope,
                                                      "computer_groups")
        self.buildings = ElementTree.SubElement(self.scope, "buldings")
        self.departments = ElementTree.SubElement(self.scope, "departments")
        self.exclusions = ElementTree.SubElement(self.scope, "exclusions")
        self.excluded_computers = ElementTree.SubElement(self.exclusions,
                                                         "computers")
        self.excluded_computer_groups = ElementTree.SubElement(
            self.exclusions, "computer_groups")
        self.excluded_buildings = ElementTree.SubElement(
            self.exclusions, "buildings")
        self.excluded_departments = ElementTree.SubElement(self.exclusions,
                                                           "departments")

        # Self Service
        self.self_service = ElementTree.SubElement(self, "self_service")
        self.use_for_self_service = ElementTree.SubElement(
            self.self_service, "use_for_self_service")
        self.set_bool(self.use_for_self_service, True)

        # Package Configuration
        self.pkg_config = ElementTree.SubElement(self, "package_configuration")
        self.pkgs = ElementTree.SubElement(self.pkg_config, "packages")

        # Maintenance
        self.maintenance = ElementTree.SubElement(self, "maintenance")
        self.recon = ElementTree.SubElement(self.maintenance, "recon")
        self.set_bool(self.recon, True)

    def add_object_to_scope(self, obj):
        """Add an object to the appropriate scope block.

        Args:
            obj: JSSObject to add to scope. Accepted subclasses are:
                Computer
                ComputerGroup
                Building
                Department

        Raises:
            TypeError if invalid obj type is provided.
        """
        if isinstance(obj, Computer):
            self.add_object_to_path(obj, "scope/computers")
        elif isinstance(obj, ComputerGroup):
            self.add_object_to_path(obj, "scope/computer_groups")
        elif isinstance(obj, Building):
            self.add_object_to_path(obj, "scope/buildings")
        elif isinstance(obj, Department):
            self.add_object_to_path(obj, "scope/departments")
        else:
            raise TypeError

    def clear_scope(self):
        """Clear all objects from the scope, including exclusions."""
        clear_list = ["computers", "computer_groups", "buildings",
                      "departments", "limit_to_users/user_groups",
                      "limitations/users", "limitations/user_groups",
                      "limitations/network_segments", "exclusions/computers",
                      "exclusions/computer_groups", "exclusions/buildings",
                      "exclusions/departments", "exclusions/users",
                      "exclusions/user_groups", "exclusions/network_segments"]
        for section in clear_list:
            self.clear_list("%s%s" % ("scope/", section))

    def add_object_to_exclusions(self, obj):
        """Add an object to the appropriate scope exclusions
        block.

        Args:
            obj: JSSObject to add to exclusions. Accepted subclasses
                    are:
                Computer
                ComputerGroup
                Building
                Department

        Raises:
            TypeError if invalid obj type is provided.
        """
        if isinstance(obj, Computer):
            self.add_object_to_path(obj, "scope/exclusions/computers")
        elif isinstance(obj, ComputerGroup):
            self.add_object_to_path(obj, "scope/exclusions/computer_groups")
        elif isinstance(obj, Building):
            self.add_object_to_path(obj, "scope/exclusions/buildings")
        elif isinstance(obj, Department):
            self.add_object_to_path(obj, "scope/exclusions/departments")
        else:
            raise TypeError

    def add_package(self, pkg):
        """Add a Package object to the policy with action=install.

        Args:
            pkg: A Package object to add.
        """
        if isinstance(pkg, Package):
            package = self.add_object_to_path(
                pkg, "package_configuration/packages")
            action = ElementTree.SubElement(package, "action")
            action.text = "Install"

    def set_self_service(self, state=True):
        """Set use_for_self_service to bool state."""
        self.set_bool(self.find("self_service/use_for_self_service"), state)

    def set_recon(self, state=True):
        """Set policy's recon value to bool state."""
        self.set_bool(self.find("maintenance/recon"), state)

    def set_category(self, category):
        """Set the policy's category.

        Args:
            category: A category object.
        """
        pcategory = self.find("general/category")
        pcategory.clear()
        name = ElementTree.SubElement(pcategory, "name")
        if isinstance(category, Category):
            id_ = ElementTree.SubElement(pcategory, "id")
            id_.text = category.id
            name.text = category.name
        elif isinstance(category, basestring):
            name.text = category


class Printer(JSSContainerObject):
    _url = "/printers"


class RestrictedSoftware(JSSContainerObject):
    _url = "/restrictedsoftware"


class RemovableMACAddress(JSSContainerObject):
    _url = "/removablemacaddresses"


class SavedSearch(JSSContainerObject):
    _url = "/savedsearches"
    can_put = False
    can_post = False
    can_delete = False


class Script(JSSContainerObject):
    _url = "/scripts"
    list_type = "script"


class Site(JSSContainerObject):
    _url = "/sites"
    list_type = "site"


class SoftwareUpdateServer(JSSContainerObject):
    _url = "/softwareupdateservers"


class SMTPServer(JSSFlatObject):
    _url = "/smtpserver"
    id_url = ""
    can_list = False
    can_post = False
    search_types = {}


class UserExtensionAttribute(JSSContainerObject):
    _url = "/userextensionattributes"


class User(JSSContainerObject):
    _url = "/users"


class UserGroup(JSSContainerObject):
    _url = "/usergroups"


class VPPAccount(JSSContainerObject):
    _url = "/vppaccounts"
    list_type = "vpp_account"
