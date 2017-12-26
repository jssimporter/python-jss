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
from .exceptions import JSSError, SSLVerifyError
from .contrib.gurl import Gurl


class GurlAdapter(object):

    def __init__(self):
        pass

    def get(self, url, headers=None):
        request = Gurl().initWithOptions_({
            'url': url,
            'additional_headers': headers,
        })
        request.start()
        while not request.isDone():
            pass

        
