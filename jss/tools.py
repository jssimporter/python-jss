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
"""tools.py

Helper functions for python-jss.
"""


import os
import re


PKG_TYPES = [".PKG", ".DMG", ".ZIP"]


def is_osx():
    """Convenience function for testing OS version."""
    result = True if os.uname()[0] == "Darwin" else False
    return result


def is_linux():
    """Convenience function for testing OS version."""
    result = True if os.uname()[0] == "Linux" else False
    return result


def is_package(filename):
    """Return True if filename is a package type.

    Args:
        filename: String filename with no path.
    """
    return os.path.splitext(filename)[1].upper() in PKG_TYPES


def is_script(filename):
    """Return True if a filename is NOT a package.

    Because there are so many script types, it's easier to see if
    the file is a package than to see if it is a script.

    Args:
        filename: String filename with no path.
    """
    return not is_package(filename)


def convert_response_to_text(response):
    """Convert a JSS HTML response to plaintext."""
    # Responses are sent as html. Split on the newlines and give us
    # the <p> text back.
    errorlines = response.text.encode("utf-8").split("\n")
    error = []
    pattern = re.compile(r"<p.*>(.*)</p>")
    for line in errorlines:
        content_line = re.search(pattern, line)
        if content_line:
            error.append(content_line.group(1))

    return ". ".join(error)
