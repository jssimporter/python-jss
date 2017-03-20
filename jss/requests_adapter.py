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

Adapter objects to provide an API for drop-in replacements
for http requests.

These classes primarily exists to work around the somewhat broken python
environment provided by Apple. python-jss initially used the requests
package to perform secure communications, but after macOS 10.11 stopped
making it easy for downstream python-jss projects to install without
user site-package installs (JSSImporter in AutoPkgr...), it was decided
that an adapter should be created. Then, curl could be offered as a
an easier default networking layer. At some point, it would be nice
to also add an NSURLSession adapter.
"""


import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from .tlsadapter import TLSAdapter


class RequestsAdapter(object):
    """Adapter to use Requests for all Casper API calls"""
    headers = {"content-type": "text/xml", "Accept": "application/xml"}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    @property
    def auth(self):
        return self.session.auth

    @auth.setter
    def auth(self, auth):
        self.session.auth = auth

    @property
    def ssl_verify(self):
        """Boolean value for whether to verify SSL traffic is valid."""
        return self.session.verify

    @ssl_verify.setter
    def ssl_verify(self, value):
        """Boolean value for whether to verify SSL traffic is valid.

        Args:
            value: Boolean.
        """
        self.session.verify = value

    def use_tls(self, base_url):
        """Mount the TLSAdapter for SSLv3 communication"""
        self.session.mount(base_url, TLSAdapter())

    def get(self, url, headers=None):
        if not headers:
            headers = {}
        return self.session.get(url, headers=headers)

    def post(self, url, data, headers=None):
        if not headers:
            headers = {}
        return self.session.post(url, data=data, headers=headers)

    def put(self, url, data, headers=None):
        if not headers:
            headers = {}
        return self.session.put(url, data=data, headers=headers)

    def delete(self, url, data=None, headers=None):
        if not headers:
            headers = {}
        if data:
            return self.session.delete(url, data=data)
        else:
            return self.session.delete(url)

    def suppress_warnings(self):
        """Disable urllib3's warning messages"""
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
