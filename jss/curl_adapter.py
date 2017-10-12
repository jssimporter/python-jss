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

Adapter object to provide the Requests API wrapped around curl.

macOS ships with a combination of python and openssl that cannot do TLS,
which is required to work with current JSS versions.

python-jss offers two options:
1. Add the Requests library, along with updating a number of its
   dependencies.
2. Use subprocess to funnel web requests through curl, which is built on
   Macs against the Cocoa networking frameworks.

This module provides the second option, a wrapper around Curl that uses
the same API as Requests, to facilitate replacing the networking layer
for more advanced users. CurlAdapter is the default when instantiating a
JSS object beginning with python-jss 2.0.0.
"""


import copy
import subprocess

from .exceptions import JSSError, SSLVerifyError


class CurlAdapter(object):
    """Adapter to use Curl for all Casper API calls

    Attributes:
        auth (2-tuple of str): Username and password for making requests.
        ssl_verify (bool): Whether to verify SSL traffic. Defaults to
            True.
        use_tls: Whether to use TLS. Defaults to True.
    """
    base_headers = ['Accept: application/xml']

    def __init__(self):
        self.auth = ('', '')
        self.verify = True
        self.use_tls = True

    def get(self, url, headers=None):
        return self._request(url, headers)

    def post(self, url, data=None, headers=None, files=None):
        content_type = 'text/xml' if not files else 'multipart/form-data'
        header = ['Content-Type: {}'.format(content_type)]
        if headers:
            header += headers

        post_kwargs = {"--request": "POST"}
        return self._request(url, header, data, files, **post_kwargs)

    def put(self, url, data=None, headers=None, files=None):
        content_type = 'text/xml' if not files else 'multipart/form-data'
        header = ['Content-Type: {}'.format(content_type)]
        if headers:
            header += headers
        put_args = {"--request": "PUT"}
        return self._request(url, header, data, files, **put_args)

    def delete(self, url, data=None, headers=None):
        delete_args = {"--request": "DELETE"}
        if data:
            headers += ['Content-Type: text/xml']
            delete_args['--data'] = data
        return self._request(url, headers, **delete_args)

    def _request(self, url, headers=None, data=None, files=None, **kwargs):
        command = self._build_command(url, headers, data, files, **kwargs)

        # Ensure all arguments to curl are encoded. This is the last
        # point of contact, so just do it here and keep it Unicode
        # everywhere else.
        command = [
            item.encode('UTF-8') if isinstance(item, unicode) else item
            for item in command]

        try:
            response = subprocess.check_output(command)
        except subprocess.CalledProcessError as err:
            if err.returncode == 60:
                raise SSLVerifyError(
                    'The JSS\'s certificate cannot be verified.')
            else:
                raise JSSError('Unknown curl error')

        return CurlResponseAdapter(response, url)

    def _build_command(
        self, url, headers=None, data=None, files=None, **kwargs):
        """Construct the argument list for curl.

        Encode all unicode to bytes with UTF-8 on the way out.

        Args:
            url (str): Full URL to request.
            headers (sequence of str): Header strings to use. Defaults to
                None.
            kwargs (str: str): Extra commandline arguments and their
                values to be added to the curl command.

        Returns:
            list of arguments to subprocess for making request via curl.
        """
        # Curl expects auth information as a ':' delimited string.
        auth = '{}:{}'.format(*self.auth)
        command = ["curl", "-u", auth]

        # Remove the progress bar that curl displays in a subprocess.
        command.append("--silent")

        # Add the returncode to the output so we can parse it into
        # the resulting CurlResponseAdapter.
        command += ["--write-out", "|%{response_code}"]

        if self.verify == False:
            command.append("--insecure")

        if self.use_tls:
            command.append("--tlsv1")

        compiled_headers = copy.copy(self.base_headers)
        if headers:
            compiled_headers += headers
        for header in compiled_headers:
            command += ['--header', header]

        if data:
            command += ["--data", data]

        if files:
            path = files['name'][1].name
            content_type = files['name'][2]
            file_data = 'name=@{};type={}'.format(path, content_type)
            command += ["--form", file_data]

        for key, val in kwargs.items():
            command += [key, val]

        command.append(url)

        return command

    def suppress_warnings(self):
        """Included for compatibility with RequestsAdapter"""
        # TODO: Remove
        pass


class CurlResponseAdapter(object):
    """Wrapper for Curl responses"""

    def __init__(self, response, url):
        self.response = response
        self.url = url
        content, _, status_code = response.rpartition("|")
        try:
            self.status_code = int(status_code)
        except ValueError:
            self.status_code = 0
        self.content = content
        # Requests' text attribute returns unicode, so convert curl's
        # returned bytes.
        self.text = content.decode('UTF-8')
