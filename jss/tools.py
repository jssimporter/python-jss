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
"""tools.py

Helper functions for python-jss.
"""


from __future__ import absolute_import
import copy
from functools import wraps
import os
import re
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+
from xml.etree import ElementTree


PKG_TYPES = {".PKG", ".DMG", ".ZIP"}


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
    # TODO: Possible rewording
    # return filename.upper().endswith(tuple(PKG_TYPES))
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
    errorlines = response.content.decode("utf-8").split("\n")
    error = []
    pattern = re.compile(r"<p.*>(.*)</p>")
    for line in errorlines:
        content_line = re.search(pattern, line)
        if content_line:
            error.append(content_line.group(1))

    return ". ".join(error) + " {}.".format(response.url)


def error_handler(exception_cls, response):
    """Handle HTTP errors by formatting into strings."""
    # Responses are sent as html. Split on the newlines and give us
    # the <p> text back.
    error = convert_response_to_text(response)
    exception = exception_cls("Response Code: %s\tResponse: %s" %
                              (response.status_code, error))
    exception.status_code = response.status_code
    raise exception


def loop_until_valid_response(prompt):
    """Loop over entering input until it is a valid bool-ish response.

    Args:
        prompt: Text presented to user.

    Returns:
        The bool value equivalent of what was entered.
    """
    responses = {"Y": True, "YES": True, "TRUE": True,
                 "N": False, "NO": False, "FALSE": False}
    response = ""
    while response.upper() not in responses:
        response = raw_input(prompt)

    return responses[response.upper()]


def indent_xml(elem, level=0, more_sibs=False):
    """Indent an xml element object to prepare for pretty printing.

    To avoid changing the contents of the original Element, it is
    recommended that a copy is made to send to this function.

    Args:
        elem: Element to indent.
        level: Int indent level (default is 0)
        more_sibs: Bool, whether to anticipate further siblings.
    """
    i = "\n"
    pad = "    "
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
            indent_xml(kid, level + 1, count < num_kids - 1)
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


def element_str(elem):
    """Return a string with indented XML data."""
    # deepcopy so we don't mess with the valid XML.
    pretty_data = copy.deepcopy(elem)
    indent_xml(pretty_data)
    return ElementTree.tostring(pretty_data, encoding='unicode')


def quote_and_encode(string):
    """Encode a bytes string to UTF-8 and then urllib.quote"""
    return quote(string.encode('UTF_8'))


def triggers_cache(func):
    """Decorator for enabling methods to trigger cache filling."""

    @wraps(func)
    def trigger_cache(self, *args, **kwargs):
        if hasattr(self, 'cached') and not self.cached:
            self.retrieve()
        return func(self, *args, **kwargs)

    return trigger_cache


def decorate_class_with_caching(cls, methods):
    for method_name in methods:
        if hasattr(cls, method_name):  # JSSObject does not have copy ?
            decorated_method = triggers_cache(getattr(cls, method_name))
            setattr(cls, method_name, decorated_method)
