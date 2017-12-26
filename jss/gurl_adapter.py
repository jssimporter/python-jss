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
        
    def get(self, url, headers=None, verify=True):  # type: (str, Optional[dict], bool) -> GurlResponseAdapter
        out = BytesIO()
        request = Gurl.alloc().initWithOptions_({
            'url': url,
            'additional_headers': headers,
            'output': out,
        })
        request.start()
        while not request.isDone():
            pass

        response = GurlResponseAdapter(url, request.status, out.getvalue())
        out.close()
        return response

    def post(self,
             url,                       # type: str
             data=None,                 # type: Optional[bytes]
             headers=None,              # type: dict
             files=None,                # type: Any
             verify=True,               # type: bool
             auth=None,                 # type: Optional[Tuple[str, str]]
             force_basic_auth=False,    # type: bool
             ):
        # type: (...) -> GurlResponseAdapter
        out = BytesIO()
        if headers is None:
            headers = {}
            
        opts = {
            'url': url,
            'additional_headers': headers,
            'output': out,
            'data': data,
            'method': 'POST',
        }

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
