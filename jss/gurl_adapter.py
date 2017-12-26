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

    def __init__(self):
        pass

    def _build_manual_authorization(self, username, password):
        return base64.encodestring('%s:%s' % (username, password))
        
    def get(self, url, headers=None, verify=True):
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

    def post(self, url, data=None, headers=None, files=None, verify=True, auth=None):
        out = BytesIO()
        if headers is None:
            headers = {}
            
        opts = {
            'url': url,
            'additional_headers': headers,
            'output': out,
            'data': data,
        }
        if auth is not None and len(auth) == 2:
            opts['username'] = auth[0]
            opts['password'] = auth[1]
            # NSURLSession wont even supply the credentials if the server doesnt challenge us.
            # which the JSS doesn't.
            opts['additional_headers']['Authorization'] = 'Basic %s' % self._build_manual_authorization(opts['username'], opts['password'])
            
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
