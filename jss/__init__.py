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
"""python-jss

Python wrapper for the JAMF Casper JSS API.

"import jss" to import all public classes.

Public package contents include:
    casper: Class using the Casper private API call to casper.jxml.
    curl_adapter: Networking adapter to use the curl command with the
        Requests API.
    distribution_point: Classes for AFP, SMB, CDP, and JDS DPs.
    distribution_points: Class for managing distribution point classes.
        distribution points, JDS, and CDP distribution servers, and
        copying, deleting, and testing for files, as well as a
        controller class for abstracting all configured DPs.
    exceptions: python-jss custom exceptions.
    jamf_software_server: Class for representing a JSS, and for
        preference files to configure one.
    jssobject: Base class used for JSS objects. Useful for testing
        (e.g. "isinstance(obj, JSSObject)").
    jssobjects: Represents each of the objects the JSS supports
        (packages, computers, etc).
    jss_prefs: Class for loading python-jss configuration via a plist
        file, and for use as an argument to JSS. Includes an
        interactive setup helper.
    requests_adapter: Networking adapter to use the Requests library.
    response_adapter: Adapter for wrapping Curl response objects with the
        Requests API.

Private package contents include:
    contrib: Code from other authors used in python-jss.
    jssobjectlist: Classes for representing lists of objects returned
        from the JSS' GET searches.
    tlsadapter: Adapter to allow Requests to use TLS, and
        with the correct ciphers to match current JAMF recommendations.
    tools: Assorted functions for common tasks used throughout the
        package.
"""


from .casper import Casper
from .curl_adapter import CurlAdapter
from .distribution_point import (AFPDistributionPoint, SMBDistributionPoint,
                                 JDS, CDP, LocalRepository)
from .distribution_points import DistributionPoints
from .exceptions import (
    JSSPrefsMissingFileError, JSSPrefsMissingKeyError, JSSGetError,
    JSSPutError, JSSPostError, JSSDeleteError, JSSMethodNotAllowedError,
    JSSSSLVerifyError, JSSUnsupportedSearchMethodError,
    JSSFileUploadParameterError, JSSUnsupportedFileType, JSSError)
from .jamf_software_server import JSS
from .jssobject import JSSObject
from .jssobjects import *
from .jss_prefs import JSSPrefs
from .queryset import QuerySet
from .pretty_element import PrettyElement

# If a system doesn't have the required dependencies for requests, do
# nothing.
try:
    from .requests_adapter import RequestsAdapter
except ImportError:
    RequestsAdapter = None

from .tools import is_osx, is_linux, element_str

# ElementTree doesn't give very helpful string representations. This
# package is intended to be used interactively, and just defaulting to
# the Object.__repr__ method is not very helpful, so we override __str__
# at the class level. This means _all_ instances of Element will have
# the indenting __str__ method, including ones created before importing
# this package. Extensive attempts were made to patch Elements if and
# when they were added as children of a PrettyElement in python-jss,
# but it didn't work. Ultimately, JSSObject will not be a subclass of
# ElementTree, so this is not going to be a problem forever.

# Consider this guerilla warfare against ElementTree.
import xml.etree.ElementTree
xml.etree.ElementTree.Element.__str__ = element_str

# Deprecated
from .jssobjectlist import JSSObjectList


__version__ = "2.0.0"
