#!/usr/bin/env python
# Copyright (C) 2014-2016 Shea G Craig
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
"""response_adapter.py

Adapter object to wrap responses from different request adaptors.

This primarily exists to work around the somewhat broken python
environment provided by Apple. python-jss initially used the requests
package to perform secure communications, but after macOS 10.11 stopped
making it easy for downstream python-jss projects to install without
user site-package installs (JSSImporter in AutoPkgr...), it was decided
that an adapter should be created. Then, curl could be offered as a
an easier default networking layer. At some point, it would be nice
to also add an NSURLSession adapter.
"""


class RequestsResponseAdapter(object):
    """Wrapper for requests response objects

    This API is based on requests, so this is very minimal.
    """

    def __init__(self, response):
        self.response = response
        self.status_code = response.status_code
        self.text = response.text


class CurlResponseAdapter(object):
    """Wrapper for Curl responses"""

    def __init__(self, response):
        self.response = response
        content, _, status_code = response.rpartition("|")
        try:
            self.status_code = int(status_code)
        except ValueError:
            self.status_code = 0
        self.content = content
        # Requests' text attribute returns unicode, so convert curl's
        # returned bytes.
        self.text = content.decode('UTF-8')


