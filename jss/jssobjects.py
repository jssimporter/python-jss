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
"""jssobjects.py

Classes representing JSS database objects and their API endpoints
"""


import mimetypes
import os
from xml.etree import ElementTree
from xml.sax.saxutils import escape

import requests

from .exceptions import GetError
from .jssobject import Container, Group, JSSObject
from .tools import error_handler


__all__ = (
    'Account', 'AccountGroup', 'ActivationCode', 'AdvancedComputerSearch',
    'AdvancedMobileDeviceSearch', 'AdvancedUserSearch',
    'AllowedFileExtension', 'Building', 'BYOProfile', 'Category', 'Class',
    'Computer', 'ComputerApplication', 'ComputerApplicationUsage',
    'ComputerCheckIn', 'ComputerCommand', 'ComputerConfiguration',
    'ComputerExtensionAttribute', 'ComputerGroup',
    'ComputerHardwareSoftwareReport', 'ComputerHistory',
    'ComputerInventoryCollection', 'ComputerInvitation', 'ComputerManagement',
    'ComputerReport', 'Department', 'DirectoryBinding',
    'DiskEncryptionConfiguration', 'DistributionPoint', 'DockItem', 'EBook',
    'GSXConnection', 'HealthcareListener', 'HealthcareListenerRule', 'IBeacon',
    'InfrastructureManager', 'JSSUser', 'JSONWebTokenConfigurations',
    'LDAPServer', 'LicensedSoftware', 'MacApplication',
    'ManagedPreferenceProfile', 'MobileDevice', 'MobileDeviceApplication',
    'MobileDeviceCommand', 'MobileDeviceConfigurationProfile',
    'MobileDeviceEnrollmentProfile', 'MobileDeviceExtensionAttribute',
    'MobileDeviceGroup', 'MobileDeviceHistory', 'MobileDeviceInvitation',
    'MobileDeviceProvisioningProfile', 'NetbootServer', 'NetworkSegment',
    'OSXConfigurationProfile', 'Package', 'Patch', 'Peripheral',
    'PeripheralType', 'Policy', 'Printer', 'RestrictedSoftware',
    'RemovableMACAddress', 'SavedSearch', 'Script', 'Site',
    'SoftwareUpdateServer', 'SMTPServer', 'UserExtensionAttribute', 'User',
    'UserGroup', 'VPPAccount', 'VPPAssignment', 'VPPInvitation', 'Webhook')


# pylint: disable=missing-docstring
class Account(Container):
    """JSS account."""
    _endpoint_path = "accounts"
    # TODO: This is pending removal.
    container = "users"
    id_url = "userid"
    search_types = {"userid": "userid", "username": "username",
                    "name": "username"}


class AccountGroup(Container):
    """Account groups are groups of users on the JSS.

    Within the API hierarchy they are actually part of accounts, but I
    seperated them.
    """

    _endpoint_path = "accounts"
    # TODO: This is pending removal.
    container = "groups"
    id_url = "groupid"
    search_types = {"groupid": "groupid", "groupname": "groupname",
                    "name": "groupname"}


class ActivationCode(JSSObject):
    _endpoint_path = "activationcode"
    can_delete = False
    can_post = False


class AdvancedComputerSearch(Container):
    _endpoint_path = "advancedcomputersearches"


class AdvancedMobileDeviceSearch(Container):
    _endpoint_path = "advancedmobiledevicesearches"


class AdvancedUserSearch(Container):
    _endpoint_path = "advancedusersearches"


class AllowedFileExtension(Container):
    _endpoint_path = "allowedfileextensions"
    can_put = False
    default_search = "extension"
    search_types = {"extension": "extension"}


class Building(Container):
    _endpoint_path = "buildings"
    root_tag = "building"


class BYOProfile(Container):
    _endpoint_path = "byoprofiles"
    root_tag = "byoprofiles"
    can_delete = False
    can_post = False
    search_types = {"sitename": "site/name", "siteid": "site/id",
                    "name": "name"}


class Category(Container):
    _endpoint_path = "categories"
    root_tag = "category"


class Class(Container):
    _endpoint_path = "classes"


class Computer(Container):
    root_tag = "computer"
    _endpoint_path = "computers"
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macaddress"}
    # The '/computers/match/name/{matchname}' variant is not supported
    # here because in testing, it didn't actually do anything.
    allowed_kwargs = ('subset', 'match')

    @property
    def mac_addresses(self):
        """Return a list of mac addresses for this device.

        Computers don't tell you which network device is which.
        """
        mac_addresses = [self.findtext("general/mac_address")]
        if self.findtext("general/alt_mac_address"):
            mac_addresses.append(self.findtext("general/alt_mac_address"))
            return mac_addresses


class ComputerApplication(Container):
    _endpoint_path = "computerapplications"
    can_delete = False
    can_put = False
    can_post = False
    default_search = "application"
    search_types = {"application": "application"}
    allowed_kwargs = ("version", "inventory")


class ComputerApplicationUsage(Container):
    _endpoint_path = "computerapplicationusage"
    can_delete = False
    can_put = False
    can_post = False
    allowed_kwargs = ('start_date', 'end_date')
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macaddress",
                    "match": "match"}

    @classmethod
    def _handle_kwargs(cls, kwargs):
        """Do nothing. Can be overriden by classes which need it."""
        if not all(key in kwargs for key in ('start_date', 'end_date')):
            raise TypeError(
                "This class requires a `start_date` and an `end_date` "
                "parameter.")

        # The current `build_query` implementation needs dates to be a
        # single item in the keywords dict, so combine them.
        start, end = kwargs.pop('start_date'), kwargs.pop('end_date')
        kwargs['date_range'] = (start, end)
        return kwargs


class ComputerCheckIn(JSSObject):
    _endpoint_path = "computercheckin"
    can_delete = False
    can_post = False


class ComputerCommand(Container):
    _endpoint_path = "computercommands"
    can_delete = False
    can_put = False
    # TODO: You _can_ POST computer commands, but it is not yet
    # implemented
    can_post = False


class ComputerConfiguration(Container):
    _endpoint_path = "computerconfigurations"
    root_tag = "computer_configuration"


class ComputerExtensionAttribute(Container):
    _endpoint_path = "computerextensionattributes"


class ComputerGroup(Group):
    _endpoint_path = "computergroups"
    root_tag = "computer_group"
    data_keys = {
        "is_smart": False,
        "criteria": None,
        "computers": None,}

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
        super(ComputerGroup, self).remove_object_from_list(
            computer, "computers")


class ComputerHardwareSoftwareReport(Container):
    _endpoint_path = "computers"
    can_put = False
    can_post = False
    can_delete = False
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress",
                    "match": "match"}
    allowed_kwargs = ('start_date', 'end_date', 'subset')


class ComputerHardwareSoftwareReport(Container):
    """Unimplemented at this time."""
    _endpoint_path = "computerhardwaresoftwarereports"
    can_delete = False
    can_put = False
    can_post = False


class ComputerHistory(Container):
    _endpoint_path = "computerhistory"
    can_delete = False
    can_put = False
    can_post = False
    allowed_kwargs = ('subset',)
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress"}


class ComputerInventoryCollection(JSSObject):
    _endpoint_path = "computerinventorycollection"
    can_post = False
    can_delete = False


class ComputerInvitation(Container):
    _endpoint_path = "computerinvitations"
    can_put = False
    search_types = {"name": "name", "invitation": "invitation"}


class ComputerManagement(Container):
    _endpoint_path = "computermanagement"
    can_put = False
    can_post = False
    can_delete = False
    allowed_kwargs = ('patchfilter', 'username', 'subset')
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress"}


class ComputerReport(Container):
    _endpoint_path = "computerreports"
    can_put = False
    can_post = False
    can_delete = False


class Department(Container):
    _endpoint_path = "departments"
    root_tag = "department"


class DirectoryBinding(Container):
    _endpoint_path = "directorybindings"


class DiskEncryptionConfiguration(Container):
    _endpoint_path = "diskencryptionconfigurations"


class DistributionPoint(Container):
    _endpoint_path = "distributionpoints"


class DockItem(Container):
    _endpoint_path = "dockitems"


class EBook(Container):
    _endpoint_path = "ebooks"
    allowed_kwargs = ('subset',)


class GSXConnection(JSSObject):
    _endpoint_path = "gsxconnection"
    can_post = False
    can_delete = False


class HealthcareListener(Container):
    _endpoint_path = "healthcarelistener"
    can_post = False
    can_delete = False
    default_search = "id"
    search_types = {"id": "id"}


class HealthcareListenerRule(Container):
    _endpoint_path = "healthcarelistenerrule"
    can_delete = False
    default_search = "id"
    search_types = {"id": "id"}


class IBeacon(Container):
    _endpoint_path = "ibeacons"
    root_tag = "ibeacon"


class InfrastructureManager(Container):
    _endpoint_path = "infrastructuremanager"
    can_post = False
    can_delete = False
    default_search = "id"
    search_types = {"id": "id"}


class JSSUser(JSSObject):
    """JSSUser is deprecated."""
    _endpoint_path = "jssuser"
    can_post = False
    can_put = False
    can_delete = False


class JSONWebTokenConfigurations(JSSObject):
    _endpoint_path = "jsonwebtokenconfigurations"
    default_search = "id"
    search_types = {"id": "id"}


class LDAPServer(Container):
    _endpoint_path = "ldapservers"

    def search_users(self, user):
        """Search for LDAP users.

        Args:
            user: User to search for. It is not entirely clear how the
                JSS determines the results- are regexes allowed, or
                globbing?

        Returns:
            LDAPUsersResult object.

        Raises:
            Will raise a GetError if no results are found.
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
            GetError if no results are found.
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
            raise GetError("Unexpected response.")
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


class LDAPUsersResults(Container):
    """Helper class for results of LDAPServer queries for users."""
    can_get = False
    can_post = False
    can_put = False
    can_delete = False


class LDAPGroupsResults(Container):
    """Helper class for results of LDAPServer queries for groups."""
    can_get = False
    can_post = False
    can_put = False
    can_delete = False


class LicensedSoftware(Container):
    _endpoint_path = "licensedsoftware"


class MacApplication(Container):
    _endpoint_path = "macapplications"
    root_tag = "mac_application"
    allowed_kwargs = ('subset',)


class ManagedPreferenceProfile(Container):
    _endpoint_path = "managedpreferenceprofiles"
    allowed_kwargs = ('subset',)


class MobileDevice(Container):
    """Mobile Device objects include a "match" search type which queries
    across multiple properties.
    """

    _endpoint_path = "mobiledevices"
    root_tag = "mobile_device"
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress",
                    "match": "match"}
    allowed_kwargs = ('subset',)


class MobileDeviceApplication(Container):
    _endpoint_path = "mobiledeviceapplications"
    allowed_kwargs = ('subset',)


class MobileDeviceCommand(Container):
    _endpoint_path = "mobiledevicecommands"
    can_put = False
    can_delete = False
    search_types = {"name": "name", "uuid": "uuid",
                    "command": "command"}
    # TODO: This object _can_ post, but it works a little differently
    # and is not yet implemented
    can_post = False


class MobileDeviceConfigurationProfile(Container):
    _endpoint_path = "mobiledeviceconfigurationprofiles"
    allowed_kwargs = ('subset',)


class MobileDeviceEnrollmentProfile(Container):
    _endpoint_path = "mobiledeviceenrollmentprofiles"
    search_types = {"name": "name", "invitation": "invitation"}
    allowed_kwargs = ('subset',)


class MobileDeviceExtensionAttribute(Container):
    _endpoint_path = "mobiledeviceextensionattributes"


class MobileDeviceGroup(Group):
    _endpoint_path = "mobiledevicegroups"
    root_tag = "mobile_device_group"

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


class MobileDeviceHistory(Container):
    _endpoint_path = "mobiledevicehistory"
    can_delete = False
    can_put = False
    can_post = False
    allowed_kwargs = ('subset',)
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress"}


class MobileDeviceInvitation(Container):
    _endpoint_path = "mobiledeviceinvitations"
    can_put = False
    search_types = {"invitation": "invitation"}


class MobileDeviceProvisioningProfile(Container):
    _endpoint_path = "mobiledeviceprovisioningprofiles"
    search_types = {"name": "name", "uuid": "uuid"}
    allowed_kwargs = ('subset',)


class NetbootServer(Container):
    _endpoint_path = "netbootservers"


class NetworkSegment(Container):
    _endpoint_path = "networksegments"


class OSXConfigurationProfile(Container):
    _endpoint_path = "osxconfigurationprofiles"
    allowed_kwargs = ('subset',)


class Package(Container):
    _endpoint_path = "packages"
    root_tag = "package"
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


class Patch(Container):
    _endpoint_path = "patches"
    root_tag = "software_title"
    can_post = False
    allowed_kwargs = ('subset',)
    # The /patches/id/{id}/version/{version} variant is not currently
    # implemented.


class Peripheral(Container):
    _endpoint_path = "peripherals"
    search_types = {}
    allowed_kwargs = ('subset',)


class PeripheralType(Container):
    _endpoint_path = "peripheraltypes"
    search_types = {}


# pylint: disable=too-many-instance-attributes
# This class has a lot of convenience attributes. Sorry pylint.
class Policy(Container):
    _endpoint_path = "policies"
    root_tag = "policy"
    search_types = {"name": "name", "category": "category"}
    allowed_kwargs = ('subset',)
    _name_element = "general/name"
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

    def add_object_to_limitations(self, obj):
        """Add an object to the appropriate scope limitations
        block.

        Args:
            obj: JSSObject to add to limitations. Accepted subclasses
                are:
                    User
                    UserGroup
                    NetworkSegment
                    IBeacon

        Raises:
            TypeError if invalid obj type is provided.
        """
        if isinstance(obj, User):
            self.add_object_to_path(obj, "scope/limitations/users")
        elif isinstance(obj, UserGroup):
            self.add_object_to_path(obj, "scope/limitations/user_groups")
        elif isinstance(obj, NetworkSegment):
            self.add_object_to_path(obj, "scope/limitations/network_segments")
        elif isinstance(obj, IBeacon):
            self.add_object_to_path(obj, "scope/limitations/ibeacons")
        else:
            raise TypeError

    def add_package(self, pkg, action_type="Install"):
        """Add a Package object to the policy with action=install.

        Args:
            pkg: A Package object to add.
            action_type (str, optional): One of "Install", "Cache", or
                "Install Cached".  Defaults to "Install".
        """
        if isinstance(pkg, Package):
            if action_type not in ("Install", "Cache", "Install Cached"):
                raise ValueError
            package = self.add_object_to_path(
                pkg, "package_configuration/packages")
            # If there's already an action specified, get it, then
            # overwrite. Otherwise, make a new subelement.
            action = package.find("action")
            if not action:
                action = ElementTree.SubElement(package, "action")
            action.text = action_type
        else:
            raise ValueError("Please pass a Package object to parameter: "
                             "pkg.")

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


class Printer(Container):
    _endpoint_path = "printers"


class RemovableMACAddress(Container):
    _endpoint_path = "removablemacaddresses"


class RestrictedSoftware(Container):
    _endpoint_path = "restrictedsoftware"


class SavedSearch(Container):
    _endpoint_path = "savedsearches"
    can_put = False
    can_post = False
    can_delete = False


class Script(Container):
    _endpoint_path = "scripts"
    root_tag = "script"

    def add_script(self, script_contents):
        """Add script code to the correct tag in the Script object.

        The script content will be XML encoded prior to addition,
        so there's no need to encode prior to addition with this
        method.

        Args:
            script_contents (str, unicode): Script code.
        """
        escaped_script_contents = escape(script_contents)
        script_contents_tag = self.find("script_contents")
        if not script_contents_tag:
            script_contents_tag = ElementTree.SubElement(
                self, "script_contents")
        script_contents_tag.text = escaped_script_contents


class Site(Container):
    _endpoint_path = "sites"
    root_tag = "site"


class SMTPServer(JSSObject):
    _endpoint_path = "smtpserver"
    can_post = False
    can_delete = False


class SoftwareUpdateServer(Container):
    _endpoint_path = "softwareupdateservers"


class UserExtensionAttribute(Container):
    _endpoint_path = "userextensionattributes"


class User(Container):
    _endpoint_path = "users"


class UserGroup(Container):
    _endpoint_path = "usergroups"


class VPPAccount(Container):
    _endpoint_path = "vppaccounts"
    root_tag = "vpp_account"


class VPPAssignment(Container):
    _endpoint_path = "vppassignments"


class VPPInvitation(Container):
    _endpoint_path = "vppinvitations"


class Webhook(Container):
    _endpoint_path = "webhooks"


# pylint: enable=missing-docstring
