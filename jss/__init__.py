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
"""python-jss

Python wrapper for the JAMF Casper JSS API.

"import jss" to import all public classes.

Public package contents include:
    casper: Class using the Casper private API call to casper.jxml.
    distribution_point: Classes for AFP, SMB, CDP, and JDS DPs.
    distribution_points: Class for managing distribution point classes.
        distribution points, JDS, and CDP distribution servers, and
        copying, deleting, and testing for files, as well as a
        controller class for abstracting all configured DPs.
    exceptions: python-jss custom exceptions.
    jamf_software_server: Class for representing a JSS, and for
        preference files to configure one.
    jssobject: Base class used for JSS objects. Useful for testing
        (e.g. isinstance(obj, JSSObject)
    jssobjects: Represents each of the objects the JSS supports
        (packages, computers, etc).
    jss_prefs: Class for loading python-jss configuration via a plist
        file, and for use as an argument to JSS. Includes an
        interactive setup helper.

Private package contents include:
    contrib: Code from other authors used in python-jss.
    jssobjectlist: Classes for representing lists of objects returned
        from the JSS' GET searches.
    tlsadapter: Adapter to allow python HTTP requests to use TLS, and
        with the correct ciphers to match current JAMF recommendations.
    tools: Assorted functions for common tasks used throughout the
        package.
"""


from .casper import Casper
from .distribution_point import (AFPDistributionPoint, SMBDistributionPoint,
                                 JDS, CDP, LocalRepository)
from .distribution_points import DistributionPoints
from .exceptions import (
    JSSPrefsMissingFileError, JSSPrefsMissingKeyError, JSSGetError,
    JSSPutError, JSSPostError, JSSDeleteError, JSSMethodNotAllowedError,
    JSSUnsupportedSearchMethodError, JSSFileUploadParameterError,
    JSSUnsupportedFileType, JSSError)
from .jamf_software_server import JSS
from .jssobject import JSSObject
from .jssobjectlist import JSSObjectList
from .jssobjects import (
    Account, AccountGroup, ActivationCode, AdvancedComputerSearch,
    AdvancedMobileDeviceSearch, AdvancedUserSearch, Building, BYOProfile,
    Category, Class, Computer, ComputerCheckIn, ComputerCommand,
    ComputerConfiguration, ComputerExtensionAttribute, ComputerGroup,
    ComputerInventoryCollection, ComputerInvitation, ComputerReport,
    Department, DirectoryBinding, DiskEncryptionConfiguration,
    DistributionPoint, DockItem, EBook, FileUpload, GSXConnection, IBeacon,
    JSSUser, LDAPServer, LicensedSoftware, MacApplication,
    ManagedPreferenceProfile, MobileDevice, MobileDeviceApplication,
    MobileDeviceCommand, MobileDeviceConfigurationProfile,
    MobileDeviceEnrollmentProfile, MobileDeviceExtensionAttribute,
    MobileDeviceInvitation, MobileDeviceGroup, MobileDeviceProvisioningProfile,
    NetbootServer, NetworkSegment, OSXConfigurationProfile, Package,
    Peripheral, PeripheralType, Policy, Printer, RestrictedSoftware,
    RemovableMACAddress, SavedSearch, Script, Site, SoftwareUpdateServer,
    SMTPServer, UserExtensionAttribute, User, UserGroup, VPPAccount)
from .jss_prefs import JSSPrefs
from .tools import is_osx, is_linux


__version__ = "1.4.0"
