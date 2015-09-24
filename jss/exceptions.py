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
"""exceptions.py

Custom Exceptions for python-jss.
"""


class JSSError(Exception):
    """Base python-jss exception class."""
    pass


class JSSPrefsMissingFileError(JSSError):
    """Missing preference file exception."""
    pass


class JSSPrefsMissingKeyError(JSSError):
    """Incomplete preferences file exception."""
    pass


class JSSGetError(JSSError):
    """GET exception."""
    pass


class JSSPutError(JSSError):
    """PUT exception."""
    pass


class JSSPostError(JSSError):
    """POST exception."""
    pass


class JSSDeleteError(JSSError):
    """DEL exception."""
    pass


class JSSMethodNotAllowedError(JSSError):
    """Casper object not allowed to use that method."""
    pass


class JSSUnsupportedSearchMethodError(JSSError):
    """Unrecognized or unsupported GET search argument."""
    pass


class JSSFileUploadParameterError(JSSError):
    """FileUpload parameter poorfly formed exception."""
    pass


class JSSUnsupportedFileType(JSSError):
    """Unsupported file type exception."""
    pass
