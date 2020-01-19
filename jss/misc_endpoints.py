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
"""misc_endpoints.py

Classes representing API endpoints that don't subclass JSSObject
"""
from __future__ import print_function

from __future__ import absolute_import
import mimetypes
import os
import sys
from xml.etree import ElementTree

from .exceptions import MethodNotAllowedError, PostError
from .tools import error_handler


__all__ = ('CommandFlush', 'FileUpload', 'LogFlush')

# Map Python 2 basestring type for Python 3.
if sys.version_info.major == 3:
    basestring = str

# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods

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
        return self._endpoint_path

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
            DeleteError if provided url_path has a >= 400 response.
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
            DeleteError if provided url_path has a >= 400 response.
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
                        mobiledeviceenrollmentprofiles
                    Icons:
                        policies
                        ebooks
                        mobiledeviceapplicationsicon
                    Mobile Device Application:
                        mobiledeviceapplicationsipa
                    Disk Encryption
                        diskencryptionconfigurations
                        diskencryptions (synonymous)
                    PPD
                        printers
            id_type:
                String of desired ID type:
                    id
                    name
            _id: Int or String referencing the identity value of the
                resource to add the FileUpload to.
            resource: String path to the file to upload.
        """
        resource_types = ["computers", "mobiledevices", "enrollmentprofiles",
                          "peripherals", "mobiledeviceenrollmentprofiles",
                          "policies", "ebooks", "mobiledeviceapplicationsicon",
                          "mobiledeviceapplicationsipa",
                          "diskencryptionconfigurations", "printers"]
        id_types = ["id", "name"]

        self.jss = j

        # Do some basic error checking on parameters.
        if resource_type in resource_types:
            self.resource_type = resource_type
        else:
            raise TypeError(
                "resource_type must be one of: %s" % ', '.join(resource_types))
        if id_type in id_types:
            self.id_type = id_type
        else:
            raise TypeError("id_type must be one of: %s" % ', '.join(id_types))
        self._id = str(_id)

        basename = os.path.basename(resource)
        content_type = mimetypes.guess_type(basename)[0]
        self.resource = {"name": (basename, open(resource, "rb"),
                                  content_type)}
        self._set_upload_url()

    def _set_upload_url(self):
        """Generate the full URL for a POST."""
        # pylint: disable=protected-access
        self._upload_url = "/".join([
            self.jss._url, self._endpoint_path, self.resource_type,
            self.id_type, str(self._id)])
        # pylint: enable=protected-access

    def save(self):
        """POST the object to the JSS."""
        try:
            response = self.jss.session.post(
                self._upload_url, files=self.resource)
        except PostError as error:
            if error.status_code == 409:
                raise PostError(error)
            else:
                raise MethodNotAllowedError(self.__class__.__name__)

        if response.status_code == 201:
            if self.jss.verbose:
                print("POST: Success")
                print(response.content)
        elif response.status_code >= 400:
            error_handler(PostError, response)


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
        return self._endpoint_path

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
            DeleteError if provided url_path has a >= 400 response.
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
            DeleteError if provided url_path has a >= 400 response.
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
            DeleteError if provided url_path has a >= 400 response.
        """
        if not log_type:
            log_type = "policies"

        # The XML for the /logflush basic endpoint allows spaces
        # instead of "+", so do a replace here just in case.
        interval = interval.replace(" ", "+")

        flush_url = "{}/{}/id/{}/interval/{}".format(
            self.url, log_type, obj_id, interval)

        self.jss.delete(flush_url)


# pylint: enable=missing-docstring
# pylint: enable=too-few-public-methods
