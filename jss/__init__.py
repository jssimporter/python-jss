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

Public package contents include:
    casper: Class using the Casper private API call to casper.jxml.
    distribution_points: Classes for configuring file share
        distribution points, JDS, and CDP distribution servers, and
        copying, deleting, and testing for files, as well as a
        controller class for abstracting all configured DPs.
    exceptions: python-jss custom exceptions.
    jss: Main module containing classes for representing a JSS, and
        each of the objects the JSS supports (packages, computers, etc).

Private package contents include:
    contrib: Code from other authors used in python-jss.
    tlsadapter: Adapter to allow python HTTP requests to use TLS, and
        with the correct ciphers to match current JAMF recommendations.
    tools: Assorted functions for common tasks used throughout the
        package.
"""


from casper import Casper
from distribution_points import DistributionPoints
from exceptions import (
    JSSPrefsMissingFileError, JSSPrefsMissingKeyError, JSSGetError,
    JSSPutError, JSSPostError, JSSDeleteError, JSSMethodNotAllowedError,
    JSSUnsupportedSearchMethodError, JSSFileUploadParameterError,
    JSSUnsupportedFileType, JSSError)
from jss import *
from tools import is_osx, is_linux


__version__ = "1.3.1"
