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
"""curl_adapter.py

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


import subprocess

from .exceptions import JSSError, JSSSSLVerifyError


class CurlAdapter(object):
    """Adapter to use Curl for all Casper API calls

    Attributes:
        auth (2-tuple of str): Username and password for making requests.
        ssl_verify (bool): Whether to verify SSL traffic. Defaults to
            True.
        use_tls: Whether to use TLS. Defaults to True.
        headers (dict): Request header to use for requests.
    """
    headers = {"content-type": "text/xml", "Accept": "application/xml"}

    def __init__(self):
        self.auth = ('', '')
        self.ssl_verify = True
        self.use_tls = True

    def get(self, url):
        return self._request(url)

    def post(self, url, data):
        post_args = {
            "--header": "Content-Type: text/xml", "--request": "POST",
            "--data": data}
        return self._request(url, post_args)

    def put(self, url, data):
        put_args = {
            "--header": "Content-Type: text/xml", "--request": "PUT",
            "--data": data}
        return self._request(url, put_args)

    def delete(self, url, data=None):
        delete_args = {"--request": "DELETE"}
        return self._request(url, delete_args)

    def _request(self, url, args=None):
        if not args:
            args = {}
        command = self._build_command(url, **args)
        try:
            response = subprocess.check_output(command)
        except subprocess.CalledProcessError as err:
            if err.returncode == 60:
                raise JSSSSLVerifyError(
                    'The JSS\'s certificate cannot be verified.')
            else:
                raise JSSError('Unknown curl error')

        return CurlResponseAdapter(response)

    def suppress_warnings(self):
        """Included for compatibility with RequestsAdapter"""
        # TODO: Remove
        pass

    def _build_command(self, url, **kwargs):
        command = ["curl", "-u", '{}:{}'.format(*self.auth)]
        # Remove the progress bar that curl displays in a subprocess.
        command.append("--silent")
        command += ["--write-out", "|%{response_code}"]

        if self.ssl_verify == False:
            command.append("--insecure")

        if self.use_tls:
            command.append("--tlsv1")

        for key, val in kwargs.items():
            command += [key.encode('UTF-8'), val.encode('UTF-8')]

        command.append(url)

        return command


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
