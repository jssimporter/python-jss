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


from __future__ import absolute_import
import copy
import subprocess
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

from .exceptions import JSSError, SSLVerifyError

CURL_RETURNCODE = {
    1: 'Unsupported protocol. This build of curl has no support for this protocol.',
    2: 'Failed to initialize.',
    3: 'URL malformed. The syntax was not correct.',
    4: 'A feature or option that was needed to perform the desired request was not enabled or was explicitly disabled '
       'at build-time. To make curl able to do this, you probably need another build of libcurl!',
    5: 'Couldn\'t resolve proxy. The given proxy host could not be resolved.',
    6: 'Couldn\'t resolve host. The given remote host was not resolved.',
    7: 'Failed to connect to host.',
    8: 'Weird server reply. The server sent data curl couldn\'t parse.',
    22: 'HTTP page not retrieved. The requested url was not found or returned another error with the HTTP error '
        'code being 400 or above.',
    23: 'Write error. Curl couldn\'t write data to a local filesystem or similar.',
    27: 'Out of memory. A memory allocation request failed.',
    28: 'Operation timeout. The specified time-out period was reached according to the conditions.',
    33: 'HTTP range error. The range "command" didn\'t work.',
    35: 'SSL connect error. The SSL handshaking failed.',
    47: 'Too many redirects. When following redirects, curl hit the maximum amount.',
    60: 'Peer certificate cannot be authenticated with known CA certificates.'
}

# Map Python 2 unicode type for Python 3.
if sys.version_info.major == 3:
    unicode = str

class CurlAdapter(object):
    """Adapter to use Curl for all Casper API calls

    Attributes:
        auth (2-tuple of str): Username and password for making requests.
        ssl_verify (bool): Whether to verify SSL traffic. Defaults to
            True.
        use_tls: Whether to use TLS. Defaults to True.
    """
    base_headers = ['Accept: application/xml']

    def __init__(self, verify=True):
        self.auth = ('', '')
        self.verify = verify
        self.use_tls = True

    def get(self, url, headers=None):
        return self._request(url, headers)

    def post(self, url, data=None, headers=None, files=None):
        content_type = 'text/xml' if not files else 'multipart/form-data'
        header = ['Content-Type: {}'.format(content_type)]
        if headers:
            [header.append('{}: {}'.format(k, headers[k])) for k in headers]

        post_kwargs = {"--request": "POST"}
        return self._request(url, header, data, files, **post_kwargs)

    def put(self, url, data=None, headers=None, files=None):
        content_type = 'text/xml' if not files else 'multipart/form-data'
        header = ['Content-Type: {}'.format(content_type)]
        if headers:
            [header.append('{}: {}'.format(k, headers[k])) for k in headers]

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

        logger.debug(' '.join(command))

        try:
            response = subprocess.check_output(command).decode()
        except subprocess.CalledProcessError as err:
            if err.returncode in CURL_RETURNCODE:
                raise JSSError('CURL Error: {}'.format(CURL_RETURNCODE[err.returncode]))
            else:
                raise JSSError('Unknown curl error: {}'.format(err.returncode))

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
            if isinstance(data, file):
                command += ["--data-binary", "@{}".format(data.name)]
            elif isinstance(data, dict):
                [command.extend(["-F", "{}={}".format(k, data[k])]) for k in data]
            else:
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
