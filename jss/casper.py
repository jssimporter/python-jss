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
"""casper.py

Utility class for getting and presenting information from casper.jxml.

The results from casper.jxml are undocumented and thus quite likely to be
removed. Do not rely on its continued existence!
"""
from __future__ import unicode_literals

from __future__ import absolute_import
try:
    # Python 2
    from __builtin__ import str as text
except ImportError:
    # Python 3
    from builtins import str as text

# 2 and 3 compatible
try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

from xml.etree import ElementTree

from .pretty_element import PrettyElement


class Casper(ElementTree.Element):
    """Interact with the JSS through its private casper endpoint.

    The API user must have the Casper Admin privileges "Use Casper
    Admin" and "Save With Casper Admin".
    """

    def __init__(self, jss):
        """Initialize a Casper object.

        Args:
            jss: A JSS object to request the casper page from.
        """
        self.jss = jss
        self.url = "%s/casper.jxml" % self.jss.base_url

        # This may be incorrect, but the assumption here is that this
        # request wants the auth information as urlencoded data; and
        # urlencode needs bytes.
        # TODO: If we can just pass in bytes rather than
        # urlencoded-bytes, we can remove this and let the request
        # adapter handle the outgoing data encoding.
        user = text(self.jss.user)
        password = text(self.jss.password)
        self.auth = urlencode(
            {"username": user, "password": password})
        super(Casper, self).__init__("Casper")
        self.update()

    def update(self):
        """Request an updated set of data from casper.jxml."""
        response = self.jss.session.post(
            self.url, data=self.auth)
        response_xml = ElementTree.fromstring(response.content)

        # Remove previous data, if any, and then add in response's XML.
        self.clear()
        self.extend(response_xml)

