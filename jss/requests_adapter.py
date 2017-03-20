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
"""requests_adapter.py

Adapter object to provide web requests through Requests.

macOS ships with a combination of python and openssl that cannot do TLS,
which is required to work with current JSS versions.

python-jss offers two options:
1. Add the Requests library, along with updating a number of its
   dependencies.
2. Use subprocess to funnel web requests through curl, which is built on
   Macs against the Cocoa networking frameworks.

This module provides the first option, a wrapper around Requests that
basically does nothing except automatically mount a TLSAdapter to meet
the transport requirements of current JSS versions, and allow you to
more directly suppress the warnings from urllib3 when not verifying
SSL traffic.
"""


import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from .tlsadapter import TLSAdapter


class RequestsAdapter(requests.Session):
    """Adapter to use Requests for all Casper API calls"""
    _headers = {"content-type": "text/xml", "Accept": "application/xml"}

    def __init__(self, base_url):
        super(RequestsAdapter, self).__init__()
        self.headers.update(self._headers)
        self.use_tls(base_url)

    def use_tls(self, base_url):
        """Mount the TLSAdapter for SSLv3 communication"""
        self.mount(base_url, TLSAdapter())

    def suppress_warnings(self):
        """Disable urllib3's warning messages"""
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
