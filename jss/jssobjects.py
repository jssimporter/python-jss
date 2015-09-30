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
"""jssobjects.py

Classes representing JSS database objects and their API endpoints
"""


import mimetypes
import os
from xml.etree import ElementTree

import requests

from .exceptions import (JSSMethodNotAllowedError, JSSPostError,
                         JSSFileUploadParameterError, JSSGetError)
from .jssobject import (JSSContainerObject, JSSFlatObject,
                        JSSGroupObject, JSSDeviceObject)
from .tools import error_handler


# pylint: disable=missing-docstring
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
    data_keys = {
        "is_smart": False,
        "criteria": None,
        "computers": None,}

    def __init__(self, jss, data, **kwargs):
        """Init a ComputerGroup

        Adds convenience attributes to assist in configuring.

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
        super(ComputerGroup, self).__init__(jss, data, **kwargs)
        self.criteria = self.find("criteria")

    def add_computer(self, computer):
        """Add a computer to the group.

        Args:
            computer: A Computer object to add to the group.
        """
        super(ComputerGroup, self).add_device(computer, "computers")

    def remove_computer(self, computer):
        """Remove a computer from the group.

        Args:
            computer: A Computer object to add to the group.
        """
        super(ComputerGroup, self).remove_object_from_list(computer,
                                                           "computers")


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


# pylint: disable=too-few-public-methods
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
        # pylint: disable=protected-access
        self._upload_url = "/".join(
            [self.jss._url, self._url, self.resource_type, self.id_type,
             str(self._id)])
        # pylint: enable=protected-access

    def save(self):
        """POST the object to the JSS."""
        try:
            response = requests.post(self._upload_url,
                                     auth=self.jss.session.auth,
                                     verify=self.jss.session.verify,
                                     files=self.resource)
        except JSSPostError as error:
            if error.status_code == 409:
                raise JSSPostError(error)
            else:
                raise JSSMethodNotAllowedError(self.__class__.__name__)

        if response.status_code == 201:
            if self.jss.verbose:
                print "POST: Success"
                print response.text.encode("utf-8")
        elif response.status_code >= 400:
            error_handler(JSSPostError, response)


# pylint: enable=too-few-public-methods

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
        if length == 1:
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
    data_keys = {
        "category": None,
        "info": None,
        "notes": None,
        "priority": "10",
        "reboot_required": "false",
        "fill_user_template": "false",
        "fill_existing_users": "false",
        "boot_volume_required": "true",
        "allow_uninstalled": "false",
        "os_requirements": None,
        "required_processor": "None",   # Really. The string "None".
        "switch_with_package": "Do Not Install",
        "install_if_reported_available": "false",
        "reinstall_option": "Do Not Reinstall",
        "triggering_files": None,
        "send_notification": "false",}

    def _new(self, name, **kwargs):
        """Create a new Package from scratch.

        Args:
            name: String filename of the package to use for the
                Package object's Display Name (here, "name").
                Will also be used as the "filename" value. Casper will
                let you specify different values, but it is not
                recommended.
            kwargs:
                Accepted keyword args include all top-level keys.
                Values will be cast to string. (Int 10, bool False
                become string values "10" and "false").
        """
        # We want these to match, so circumvent the for loop.
        # ElementTree.SubElement(self, "name").text = name
        super(Package, self)._new(name, **kwargs)
        ElementTree.SubElement(self, "filename").text = name

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


# pylint: disable=too-many-instance-attributes
# This class has a lot of convenience attributes. Sorry pylint.
class Policy(JSSContainerObject):
    _url = "/policies"
    list_type = "policy"
    _name_path = "general/name"
    data_keys = {
        "general": {
            "enabled": "true",
            "frequency": "Once per computer",
            "category": "",},
        "scope": {
            "computers": None,
            "computer_groups": None,
            "buildings": None,
            "departments": None,
            "exclusions": {
                "computers": None,
                "computer_groups": None,
                "buildings": None,
                "departments": None,},},
        "self_service": {
            "use_for_self_service": "true"},
        "package_configuration": {
            "packages": None},
        "maintenance": {
            "recon": "true"},
    }

    def __init__(self, jss, name, **kwargs):
        """Init a Policy from scratch.

        Adds convenience attributes to assist in configuring.

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
        super(Policy, self).__init__(jss, name, **kwargs)

        # Set convenience attributes.
        # This is an experiment. If it prooves to be more cumbersome
        # than it is worth, they may come out.
        # General
        self.general = self.find("general")
        self.enabled = self.general.find("enabled")
        self.frequency = self.general.find("frequency")
        self.category = self.general.find("category")

        # Scope
        self.scope = self.find("scope")
        self.computers = self.find("scope/computers")
        self.computer_groups = self.find("scope/computer_groups")
        self.buildings = self.find("scope/buildings")
        self.departments = self.find("scope/departments")
        self.exclusions = self.find("scope/exclusions")
        self.excluded_computers = self.find("scope/exclusions/computers")
        self.excluded_computer_groups = self.find(
            "scope/exclusions/computer_groups")
        self.excluded_buildings = self.find("scope/exclusions/buildings")
        self.excluded_departments = self.find("scope/exclusions/departments")

        # Self Service
        self.self_service = self.find("self_service")
        self.use_for_self_service = self.find("self_service/"
                                              "use_for_self_service")
        # Package Configuration
        self.pkg_config = self.find("package_configuration")
        self.pkgs = self.find("package_configuration/packages")
        # Maintenance
        self.maintenance = self.find("maintenance")
        self.recon = self.find("maintenance/recon")


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

# pylint: enable=too-many-instance-attributes, too-many-locals

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

# pylint: enable=missing-docstring
