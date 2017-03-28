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

import requests

from .exceptions import (JSSMethodNotAllowedError, JSSPostError,
                         JSSFileUploadParameterError, JSSGetError,
                         JSSDeleteError, JSSUnsupportedSearchMethodError)
from .jssobject import (JSSContainerObject, JSSGroupObject, JSSDeviceObject,
                        JSSObject)
from .tools import error_handler


__all__ = (
    'Account', 'AccountGroup', 'ActivationCode', 'AdvancedComputerSearch',
    'AdvancedMobileDeviceSearch', 'AdvancedUserSearch',
    'AllowedFileExtension', 'Building', 'BYOProfile', 'Category', 'Class',
    'CommandFlush', 'Computer', 'ComputerApplication',
    'ComputerApplicationUsage', 'ComputerCheckIn', 'ComputerCommand',
    'ComputerConfiguration', 'ComputerExtensionAttribute', 'ComputerGroup',
    'ComputerHardwareSoftwareReport', 'ComputerHistory',
    'ComputerInventoryCollection', 'ComputerInvitation', 'ComputerManagement',
    'ComputerReport', 'Department', 'DirectoryBinding',
    'DiskEncryptionConfiguration', 'DistributionPoint', 'DockItem', 'EBook',
    'FileUpload', 'GSXConnection', 'HealthcareListener', 'IBeacon', 'JSSUser',
    'LDAPServer', 'LicensedSoftware', 'LogFlush', 'MacApplication',
    'ManagedPreferenceProfile', 'MobileDevice', 'MobileDeviceApplication',
    'MobileDeviceCommand', 'MobileDeviceConfigurationProfile',
    'MobileDeviceEnrollmentProfile', 'MobileDeviceExtensionAttribute',
    'MobileDeviceInvitation', 'MobileDeviceGroup',
    'MobileDeviceProvisioningProfile', 'NetbootServer', 'NetworkSegment',
    'OSXConfigurationProfile', 'Package', 'Patch', 'Peripheral',
    'PeripheralType', 'Policy', 'Printer', 'RestrictedSoftware',
    'RemovableMACAddress', 'SavedSearch', 'Script', 'Site',
    'SoftwareUpdateServer', 'SMTPServer', 'UserExtensionAttribute', 'User',
    'UserGroup', 'VPPAccount', 'VPPAssignment', 'VPPInvitation')


# pylint: disable=missing-docstring
class Account(JSSContainerObject):
    """JSS account."""
    _endpoint_path = "accounts"
    # TODO: This is pending removal.
    container = "users"
    id_url = "userid"
    search_types = {"userid": "userid", "username": "username",
                    "name": "username"}


class AccountGroup(JSSContainerObject):
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


class AdvancedComputerSearch(JSSContainerObject):
    _endpoint_path = "advancedcomputersearches"


class AdvancedMobileDeviceSearch(JSSContainerObject):
    _endpoint_path = "advancedmobiledevicesearches"


class AdvancedUserSearch(JSSContainerObject):
    _endpoint_path = "advancedusersearches"


class AllowedFileExtension(JSSContainerObject):
    _endpoint_path = "allowedfileextensions"
    can_put = False
    default_search = "extension"
    search_types = {"extension": "extension"}


class Building(JSSContainerObject):
    _endpoint_path = "buildings"
    root_tag = "building"


class BYOProfile(JSSContainerObject):
    _endpoint_path = "byoprofiles"
    root_tag = "byoprofiles"
    can_delete = False
    can_post = False
    search_types = {"sitename": "site/name", "siteid": "site/id",
                    "name": "name"}


class Category(JSSContainerObject):
    _endpoint_path = "categories"
    root_tag = "category"


class Class(JSSContainerObject):
    _endpoint_path = "classes"


class CommandFlush(object):
    _endpoint_path = "commandflush"
    can_get = False
    can_put = False
    can_post = False

    def __init__(self, jss):
        """Initialize a new CommandFlush

        Args:
            jss: JSS object.
        """
        self.jss = jss

    @property
    def url(self):
        """Return the path subcomponent of the url to this object."""
        return self._url

    def command_flush_with_xml(self, data):
        """Flush commands for devices with a supplied xml string.

        From the Casper API docs:
        Status and devices specified in an XML file. Id lists may be
        specified for <computers>, <computer_groups>, <mobile_devices>,
        <mobile_device_groups>. Sample file:
            <commandflush>
              <status>Pending+Failed</status>
              <mobile_devices>
                <mobile_device>
                  <id>1</id>
                </mobile_device>
                <mobile_device>
                  <id>2</id>
                </mobile_device>
              </mobile_devices>
            </commandflush>

        Args:
            data (string): XML string following the above structure or
                an ElementTree/Element.

        Raises:
            JSSDeleteError if provided url_path has a >= 400 response.
        """
        if not isinstance(data, basestring):
            data = ElementTree.tostring(data, encoding='UTF-8')
        self.jss.delete(self.url, data)

    def command_flush_for(self, id_type, command_id, status):
        """Flush commands for an individual device.

        Args:
            id_type (str): One of 'computers', 'computergroups',
                'mobiledevices', or 'mobiledevicegroups'.
            id_value (str, int, list): ID value(s) for the devices to
                flush. More than one device should be passed as IDs
                in a list or tuple.
            status (str): One of 'Pending', 'Failed', 'Pending+Failed'.

        Raises:
            JSSDeleteError if provided url_path has a >= 400 response.
        """
        id_types = ('computers', 'computergroups', 'mobiledevices',
                    'mobiledevicegroups')
        status_types = ('Pending', 'Failed', 'Pending+Failed')
        if id_type not in id_types or status not in status_types:
            raise ValueError("Invalid arguments.")

        if isinstance(command_id, list):
            command_id = ",".join(str(item) for item in command_id)

        flush_url = "{}/{}/id/{}/status/{}".format(
            self.url, id_type, command_id, status)

        self.jss.delete(flush_url)


class Computer(JSSDeviceObject):
    root_tag = "computer"
    _endpoint_path = "computers"
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macaddress",
                    "match": "match"}
    allowed_kwargs = ('subset',)

    @property
    def mac_addresses(self):
        """Return a list of mac addresses for this device.

        Computers don't tell you which network device is which.
        """
        mac_addresses = [self.findtext("general/mac_address")]
        if self.findtext("general/alt_mac_address"):
            mac_addresses.append(self.findtext("general/alt_mac_address"))
            return mac_addresses

    # TODO: Reimplement oddball computers/subset/basic endpoint
    # Needs an extended identity or override of __init__?


class ComputerApplication(JSSContainerObject):
    _endpoint_path = "computerapplications"
    can_delete = False
    can_put = False
    can_post = False
    default_search = "application"
    search_types = {"application": "application"}
    allowed_kwargs = ("version", "inventory")


class ComputerApplicationUsage(JSSContainerObject):
    _endpoint_path = "computerapplicationusage"
    can_delete = False
    can_put = False
    can_post = False
    allowed_kwargs = ('start_date', 'end_date')
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress"}

    @classmethod
    def _handle_kwargs(cls, kwargs):
        """Do nothing. Can be overriden by classes which need it."""
        if not all(key in kwargs for key in ('start_date', 'end_date')):
            raise JSSUnsupportedSearchMethodError(
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


class ComputerCommand(JSSContainerObject):
    _endpoint_path = "computercommands"
    can_delete = False
    can_put = False
    # TODO: You _can_ POST computer commands, but it is not yet
    # implemented
    can_post = False


class ComputerConfiguration(JSSContainerObject):
    _endpoint_path = "computerconfigurations"
    root_tag = "computer_configuration"


class ComputerExtensionAttribute(JSSContainerObject):
    _endpoint_path = "computerextensionattributes"


class ComputerGroup(JSSGroupObject):
    _endpoint_path = "computergroups"
    root_tag = "computer_group"
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
        super(ComputerGroup, self).remove_object_from_list(
            computer, "computers")


class ComputerHardwareSoftwareReport(JSSContainerObject):
    _endpoint_path = "computers"
    can_put = False
    can_post = False
    can_delete = False
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress",
                    "match": "match"}
    allowed_kwargs = ('start_date', 'end_date', 'subset')


class ComputerHardwareSoftwareReport(JSSContainerObject):
    """Unimplemented at this time."""
    _endpoint_path = "computerhardwaresoftwarereports"
    can_delete = False
    can_put = False
    can_post = False


class ComputerHistory(JSSContainerObject):
    _endpoint_path = "computerhistory"
    can_delete = False
    can_put = False
    can_post = False
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress"}


class ComputerInventoryCollection(JSSObject):
    _endpoint_path = "computerinventorycollection"
    can_post = False
    can_delete = False


class ComputerInvitation(JSSContainerObject):
    _endpoint_path = "computerinvitations"
    can_put = False
    search_types = {"name": "name", "invitation": "invitation"}


class ComputerManagement(JSSContainerObject):
    _endpoint_path = "computermanagement"
    can_put = False
    can_post = False
    can_delete = False
    allowed_kwargs = ('patchfilter', 'username', 'subset')
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress"}


class ComputerReport(JSSContainerObject):
    _endpoint_path = "computerreports"
    can_put = False
    can_post = False
    can_delete = False


class Department(JSSContainerObject):
    _endpoint_path = "departments"
    root_tag = "department"


class DirectoryBinding(JSSContainerObject):
    _endpoint_path = "directorybindings"


class DiskEncryptionConfiguration(JSSContainerObject):
    _endpoint_path = "diskencryptionconfigurations"


class DistributionPoint(JSSContainerObject):
    _endpoint_path = "distributionpoints"


class DockItem(JSSContainerObject):
    _endpoint_path = "dockitems"


class EBook(JSSContainerObject):
    _endpoint_path = "ebooks"
    allowed_kwargs = ('subset',)


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
    _endpoint_path = "fileuploads"
    allowed_kwargs = ('subset',)

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
            response = self.jss.session.post(
                self._upload_url, files=self.resource)
        except JSSPostError as error:
            if error.status_code == 409:
                raise JSSPostError(error)
            else:
                raise JSSMethodNotAllowedError(self.__class__.__name__)

        if response.status_code == 201:
            if self.jss.verbose:
                print "POST: Success"
                print response.content
        elif response.status_code >= 400:
            error_handler(JSSPostError, response)


# pylint: enable=too-few-public-methods

class GSXConnection(JSSObject):
    _endpoint_path = "gsxconnection"
    can_post = False
    can_delete = False


class HealthcareListener(JSSContainerObject):
    _endpoint_path = "healthcarelistener"
    can_post = False
    can_delete = False
    default_search = "id"
    search_types = {"id": "id"}


class IBeacon(JSSContainerObject):
    _endpoint_path = "ibeacons"
    root_tag = "ibeacon"


class JSSUser(JSSObject):
    """JSSUser is deprecated."""
    _endpoint_path = "jssuser"
    can_post = False
    can_put = False
    can_delete = False


class LDAPServer(JSSContainerObject):
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
    _endpoint_path = "licensedsoftware"


class LogFlush(object):
    _endpoint_path = "logflush"

    def __init__(self, jss):
        """Initialize a new LogFlush

        Args:
            jss: JSS object.
        """
        self.jss = jss

    @property
    def url(self):
        """Return the path subcomponent of the url to this object."""
        return self._url

    def log_flush_with_xml(self, data):
        """Flush logs for devices with a supplied xml string.

        From the Casper API docs:
            log, log_id, interval, and devices specified in an XML file.
            Sample file:
              <logflush>
                <log>policy</log>
                <log_id>2</log_id>
                <interval>THREE MONTHS</interval>
                <computers>
                  <computer>
                    <id>1</id>
                  </computer>
                  <computer>
                    <id>2</id>
                  </computer>
                </computers>
              </logflush>

        Args:
            data (string): XML string following the above structure or
                an ElementTree/Element.
                Elements:
                    logflush (root)
                    log (Unknown; "policy" is the only one listed in
                         docs).
                    log_id: Log ID value.
                     interval: Combination of "Zero", "One", "Two",
                        "Three", "Six", and "Day", "Week", "Month",
                        "Year". e.g. ("Three+Months")
                        Please note: The documentation for this
                        specifies the singular form (e.g. "Month"),
                        and plural ("Months") at different times, and
                        further the construction is listed as
                        "THREE MONTHS" elsewhere. Limited testing
                        indicates that pluralization does not matter,
                        nor does capitalization. The "+" seems optional
                        as well.
                        Please test!
                    Device Arrays:
                        Again, acceptable values are not listed in the
                        docs, aside from the example ("computers").
                        Presumably "mobiledevices", and possibly
                        "computergroups" and "mobiledevicegroups" work.

        Raises:
            JSSDeleteError if provided url_path has a >= 400 response.
        """
        if not isinstance(data, basestring):
            data = ElementTree.tostring(data, encoding='UTF-8')
        self.jss.delete(self.url, data)

    def log_flush_for_interval(self, log_type, interval):
        """Flush logs for an interval of time.

        Args:
            log_type (str): Only documented type is "policies". This
                will be applied by default if nothing is passed.
            interval (str): Combination of "Zero", "One", "Two",
                "Three", "Six", and "Day", "Week", "Month", "Year". e.g.
                ("Three+Months") Please note: The documentation for this
                specifies the singular form (e.g. "Month"), and plural
                ("Months") at different times, and further the
                construction is listed as "THREE MONTHS" elsewhere.
                Limited testing indicates that pluralization does not
                matter, nor does capitalization.
                Please test!

                No validation is performed on this prior to the request
                being made.

        Raises:
            JSSDeleteError if provided url_path has a >= 400 response.
        """
        if not log_type:
            log_type = "policies"

        # The XML for the /logflush basic endpoint allows spaces
        # instead of "+", so do a replace here just in case.
        interval = interval.replace(" ", "+")

        flush_url = "{}/{}/interval/{}".format(
            self.url, log_type, interval)

        self.jss.delete(flush_url)

    def log_flush_for_obj_for_interval(self, log_type, obj_id, interval):
        """Flush logs for an interval of time for a specific object.

        Please note, log_type is a variable according to the API docs,
        but acceptable values are not listed. Only "policies" is
        demonstrated as an acceptable value.

        Args:
            log_type (str): Only documented type is "policies". This
                will be applied by default if nothing is passed.
            obj_id (str or int): ID of the object to have logs flushed.
            interval (str): Combination of "Zero", "One", "Two",
                "Three", "Six", and "Day", "Week", "Month", "Year". e.g.
                ("Three+Months") Please note: The documentation for this
                specifies the singular form (e.g. "Month"), and plural
                ("Months") at different times, and further the
                construction is listed as "THREE MONTHS" elsewhere.
                Limited testing indicates that pluralization does not
                matter, nor does capitalization.
                Please test!

                No validation is performed on this prior to the request
                being made.

        Raises:
            JSSDeleteError if provided url_path has a >= 400 response.
        """
        if not log_type:
            log_type = "policies"

        # The XML for the /logflush basic endpoint allows spaces
        # instead of "+", so do a replace here just in case.
        interval = interval.replace(" ", "+")

        flush_url = "{}/{}/id/{}/interval/{}".format(
            self.url, log_type, obj_id, interval)

        self.jss.delete(flush_url)


class MacApplication(JSSContainerObject):
    _endpoint_path = "macapplications"
    root_tag = "mac_application"
    allowed_kwargs = ('subset',)


class ManagedPreferenceProfile(JSSContainerObject):
    _endpoint_path = "managedpreferenceprofiles"
    allowed_kwargs = ('subset',)


class MobileDevice(JSSDeviceObject):
    """Mobile Device objects include a "match" search type which queries
    across multiple properties.
    """

    _endpoint_path = "mobiledevices"
    root_tag = "mobile_device"
    search_types = {"name": "name", "serial_number": "serialnumber",
                    "udid": "udid", "macaddress": "macadress",
                    "match": "match"}
    allowed_kwargs = ('subset',)

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
    _endpoint_path = "mobiledeviceapplications"
    allowed_kwargs = ('subset',)


class MobileDeviceCommand(JSSContainerObject):
    _endpoint_path = "mobiledevicecommands"
    can_put = False
    can_delete = False
    search_types = {"name": "name", "uuid": "uuid",
                    "command": "command"}
    # TODO: This object _can_ post, but it works a little differently
    # and is not yet implemented
    can_post = False


class MobileDeviceConfigurationProfile(JSSContainerObject):
    _endpoint_path = "mobiledeviceconfigurationprofiles"
    allowed_kwargs = ('subset',)


class MobileDeviceEnrollmentProfile(JSSContainerObject):
    _endpoint_path = "mobiledeviceenrollmentprofiles"
    search_types = {"name": "name", "invitation": "invitation"}
    allowed_kwargs = ('subset',)


class MobileDeviceExtensionAttribute(JSSContainerObject):
    _endpoint_path = "mobiledeviceextensionattributes"


class MobileDeviceGroup(JSSGroupObject):
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


class MobileDeviceInvitation(JSSContainerObject):
    _endpoint_path = "mobiledeviceinvitations"
    can_put = False
    search_types = {"invitation": "invitation"}


class MobileDeviceProvisioningProfile(JSSContainerObject):
    _endpoint_path = "mobiledeviceprovisioningprofiles"
    search_types = {"name": "name", "uuid": "uuid"}
    allowed_kwargs = ('subset',)


class NetbootServer(JSSContainerObject):
    _endpoint_path = "netbootservers"


class NetworkSegment(JSSContainerObject):
    _endpoint_path = "networksegments"


class OSXConfigurationProfile(JSSContainerObject):
    _endpoint_path = "osxconfigurationprofiles"
    allowed_kwargs = ('subset',)


class Package(JSSContainerObject):
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


class Patch(JSSContainerObject):
    _endpoint_path = "patches"
    root_tag = "software_title"
    can_post = False
    allowed_kwargs = ('subset',)
    # The /patches/id/{id}/version/{version} variant is not currently
    # implemented.


class Peripheral(JSSContainerObject):
    _endpoint_path = "peripherals"
    search_types = {}
    allowed_kwargs = ('subset',)


class PeripheralType(JSSContainerObject):
    _endpoint_path = "peripheraltypes"
    search_types = {}


# pylint: disable=too-many-instance-attributes
# This class has a lot of convenience attributes. Sorry pylint.
class Policy(JSSContainerObject):
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

    @property
    def general(self):
        return self.find("general")

    # TODO: The below experiment FAILED. It blows up with current
    # architecture. The assignments are evaluated at instantiation time,
    # not everytime they're looked up. Audit and fix.
    # def __init__(self, jss, name, **kwargs):
    #     """Init a Policy from scratch.

    #     Adds convenience attributes to assist in configuring.

    #     Args:
    #         name: String name of the object to use as the
    #             object's name property.
    #         kwargs:
    #             Accepted keyword args can be viewed by checking the
    #             "data_keys" class attribute. Typically, they include all
    #             top-level keys, and non-duplicated keys used elsewhere.

    #             Values will be cast to string. (Int 10, bool False
    #             become string values "10" and "false").

    #             Ignores kwargs that aren't in object's keys attribute.
    #     """
    #     super(Policy, self).__init__(jss, name, **kwargs)

    #     # Set convenience attributes.
    #     # This is an experiment. If it prooves to be more cumbersome
    #     # than it is worth, they may come out.
    #     # General
    #     self.general = self.find("general")
    #     self.enabled = self.general.find("enabled")
    #     self.frequency = self.general.find("frequency")
    #     self.category = self.general.find("category")

    #     # Scope
    #     self.scope = self.find("scope")
    #     self.computers = self.find("scope/computers")
    #     self.computer_groups = self.find("scope/computer_groups")
    #     self.buildings = self.find("scope/buildings")
    #     self.departments = self.find("scope/departments")
    #     self.exclusions = self.find("scope/exclusions")
    #     self.excluded_computers = self.find("scope/exclusions/computers")
    #     self.excluded_computer_groups = self.find(
    #         "scope/exclusions/computer_groups")
    #     self.excluded_buildings = self.find("scope/exclusions/buildings")
    #     self.excluded_departments = self.find("scope/exclusions/departments")

    #     # Self Service
    #     self.self_service = self.find("self_service")
    #     self.use_for_self_service = self.find("self_service/"
    #                                           "use_for_self_service")
    #     # Package Configuration
    #     self.pkg_config = self.find("package_configuration")
    #     self.pkgs = self.find("package_configuration/packages")
    #     # Maintenance
    #     self.maintenance = self.find("maintenance")
    #     self.recon = self.find("maintenance/recon")


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


class Printer(JSSContainerObject):
    _endpoint_path = "printers"


class RemovableMACAddress(JSSContainerObject):
    _endpoint_path = "removablemacaddresses"


class RestrictedSoftware(JSSContainerObject):
    _endpoint_path = "restrictedsoftware"


class SavedSearch(JSSContainerObject):
    _endpoint_path = "savedsearches"
    can_put = False
    can_post = False
    can_delete = False


class Script(JSSContainerObject):
    _endpoint_path = "scripts"
    root_tag = "script"


class Site(JSSContainerObject):
    _endpoint_path = "sites"
    root_tag = "site"


class SMTPServer(JSSObject):
    _endpoint_path = "smtpserver"
    can_post = False
    can_delete = False


class SoftwareUpdateServer(JSSContainerObject):
    _endpoint_path = "softwareupdateservers"


class UserExtensionAttribute(JSSContainerObject):
    _endpoint_path = "userextensionattributes"


class User(JSSContainerObject):
    _endpoint_path = "users"


class UserGroup(JSSContainerObject):
    _endpoint_path = "usergroups"


class VPPAccount(JSSContainerObject):
    _endpoint_path = "vppaccounts"
    root_tag = "vpp_account"


class VPPAssignment(JSSContainerObject):
    _endpoint_path = "vppassignments"


class VPPInvitation(JSSContainerObject):
    _endpoint_path = "vppinvitations"
# pylint: enable=missing-docstring
