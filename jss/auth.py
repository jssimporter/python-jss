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

from __future__ import absolute_import
from datetime import datetime
import logging
import sys

sys.path.insert(0, '/Library/AutoPkg/JSSImporter')
import requests

logger = logging.getLogger(__name__)


class UAPIAuth(requests.auth.AuthBase):

    def __init__(self, username, password, fetch_url='/uapi/auth/tokens', token=None, expires=None):
        self.username = username
        self.password = password
        self.token = token
        self.expires = expires if expires else datetime.now()
        self.fetch_url = fetch_url

    def __call__(self, r):  # type: (requests.PreparedRequest) -> requests.PreparedRequest
        if self.expires is not None and self.expires < datetime.now():
            logger.debug("Token expiry has passed, fetching a new token.")
            self._get_token()

        r.headers['Authorization'] = 'jamf-token {}'.format(self.token)
        r.register_hook('response', self.handle_401)
        return r

    def _get_token(self):
        r = requests.post(self.fetch_url, auth=(self.username, self.password), verify=False)
        r.raise_for_status()
        data = r.json()

        self.token = data['token']
        #self.expires = datetime.utcfromtimestamp(data['expires'])

    def handle_401(self, r, **kwargs):  # type: (requests.Response, dict) -> requests.Response
        """
        Takes the given response, fetches a new token, and retries
        :param r:
        :param kwargs:
        :return:
        """
        if r.status_code is not 401:
            return r

        logger.debug("Server returned HTTP 401, getting a new token")
        self._get_token()
