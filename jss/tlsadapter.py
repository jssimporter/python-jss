#!/usr/bin/env python
"""tlsadapter.py

TLS Adapter to work with JSS.
Copyright (C) 2014 Shea G Craig <shea.craig@da.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import ssl

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.contrib import pyopenssl


# This is the list JAMF specifies here:
# https://jamfnation.jamfsoftware.com/article.html?id=384
# Plus the exclusions from
# https://wiki.mozilla.org/Security/Server_Side_TLS
# Plus the cipher known to work with test setup.
CIPHER_LIST = ":".join(["ECDHE-RSA-AES256-GCM-SHA384",
                        "ECDHE-ECDSA-AES256-GCM-SHA384",
                        "ECDH-RSA-AES256-GCM-SHA384",
                        "ECDH-ECDSA-AES256-GCM-SHA384",
                        "ECDHE-RSA-AES128-GCM-SHA256",
                        "ECDHE-ECDSA-AES128-GCM-SHA256",
                        "ECDH-RSA-AES128-GCM-SHA256",
                        "ECDH-ECDSA-AES128-GCM-SHA256",
                        "ECDHE-RSA-AES256-SHA384",
                        "ECDHE-ECDSA-AES256-SHA384",
                        "ECDHE-RSA-AES256-SHA",
                        "ECDHE-ECDSA-AES256-SHA",
                        "ECDH-RSA-AES256-SHA384",
                        "ECDH-ECDSA-AES256-SHA384",
                        "ECDH-RSA-AES256-SHA",
                        "ECDH-ECDSA-AES256-SHA",
                        "ECDHE-RSA-AES128-SHA256",
                        "ECDHE-ECDSA-AES128-SHA256",
                        "ECDHE-RSA-AES128-SHA",
                        "ECDHE-ECDSA-AES128-SHA",
                        "ECDH-RSA-AES128-SHA256",
                        "ECDH-ECDSA-AES128-SHA256",
                        "ECDH-RSA-AES128-SHA",
                        "ECDH-ECDSA-AES128-SHA",
                        "AES128-SHA",
                        "!aNULL",
                        "!eNULL",
                        "!EXPORT",
                        "!DES",
                        "!RC4",
                        "!3DES",
                        "!MD5",
                        "!PSK"])
# Ciphers provided from
# https://wiki.mozilla.org/Security/Server_Side_TLS
# CIPHER_LIST = ":".join(["ECDHE-RSA-AES128-GCM-SHA256",
#                         "ECDHE-ECDSA-AES128-GCM-SHA256",
#                         "ECDHE-RSA-AES256-GCM-SHA384",
#                         "ECDHE-ECDSA-AES256-GCM-SHA384",
#                         "DHE-RSA-AES128-GCM-SHA256",
#                         "DHE-DSS-AES128-GCM-SHA256",
#                         "kEDH+AESGCM",
#                         "ECDHE-RSA-AES128-SHA256",
#                         "ECDHE-ECDSA-AES128-SHA256",
#                         "ECDHE-RSA-AES128-SHA",
#                         "ECDHE-ECDSA-AES128-SHA",
#                         "ECDHE-RSA-AES256-SHA384",
#                         "ECDHE-ECDSA-AES256-SHA384",
#                         "ECDHE-RSA-AES256-SHA",
#                         "ECDHE-ECDSA-AES256-SHA",
#                         "DHE-RSA-AES128-SHA256",
#                         "DHE-RSA-AES128-SHA",
#                         "DHE-DSS-AES128-SHA256",
#                         "DHE-RSA-AES256-SHA256",
#                         "DHE-DSS-AES256-SHA",
#                         "DHE-RSA-AES256-SHA",
#                         "!aNULL",
#                         "!eNULL",
#                         "!EXPORT",
#                         "!DES",
#                         "!RC4",
#                         "!3DES",
#                         "!MD5",
#                         "!PSK"])


class TLSAdapter(HTTPAdapter):
    """Transport adapter that uses TLS vs. default of SSLv23."""
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)
        pyopenssl.DEFAULT_SSL_CIPHER_LIST = CIPHER_LIST
