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

Adapter object to provide the Requests API wrapped around an instance of Gurl,
which is part of the munki project.

macOS ships with a combination of python and openssl that cannot do TLS,
which is required to work with current JSS versions.

This adapter uses Gurl, which uses PyObjC to implement NSURLConnection and NSURLSession API's.
"""

from io import BytesIO
import base64
from .exceptions import JSSError, SSLVerifyError
from .contrib.gurl import Gurl


class GurlAdapter(object):

    def __init__(self, auth=None):
        self.auth = auth
        
    def get(self, url, **kwargs):
        return self._request(url, method='GET', **kwargs)

    def post(self, url, **kwargs):
        return self._request(url, method='POST', **kwargs)

    def put(self, url, **kwargs):
        return self._request(url, method='PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._request(url, method='DELETE', **kwargs)

    def _request(
            self,
            url,                     # type: str
            method='GET',            # type: str
            headers=None,            # type: Optional[dict]
            data=None,               # type: Optional[bytes]
            files=None,              # type: Any
            verify=False,            # type: bool
            auth=None,               # type: Optional[Tuple[str, str]]
            force_basic_auth=False,  # type: bool
            **kwargs
        ):
        # type: (...) -> GurlResponseAdapter
        out = BytesIO()
        if headers is None:
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml',
            }

        opts = {
            'url': url,
            'additional_headers': headers,
            'output': out,
            'method': method,
        }

        if (method == 'POST' or method == 'PUT') and data is not None:
            opts['data'] = data

        use_auth = auth if auth is not None else self.auth
        
        if use_auth is not None:
            # NSURLSession won't even supply the credentials if the server doesnt challenge us.
            # which the JSS doesn't in the case of UAPI tokens.
            if force_basic_auth:
                auth_value = 'Basic {}'.format(base64.encodestring('%s:%s' % auth)[:-1])
                opts['additional_headers']['Authorization'] = auth_value

            # But if it does
            opts['username'], opts['password'] = use_auth

        request = Gurl.alloc().initWithOptions_(opts)
        request.start()
        while not request.isDone():
            pass

        response = GurlResponseAdapter(url, request.status, out.getvalue())
        out.close()
        return response


class GurlResponseAdapter(object):
    """Wrapper for Gurl responses"""

    def __init__(self, url, status_code, content):
        self.url = url

        try:
            self.status_code = int(status_code)
        except ValueError:
            self.status_code = 0
            
        self.content = content
        self.text = content.decode('UTF-8')
