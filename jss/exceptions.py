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
"""exceptions.py

Custom Exceptions for python-jss.
"""


class JSSError(Exception):
    """Base python-jss exception class."""
    pass


class RequestError(JSSError):

    def __init__(self, *args, **kwargs):
        super(RequestError, self).__init__(*args, **kwargs)
        self.status_code = None


class GetError(RequestError):
    """GET exception."""
    pass


class PutError(RequestError):
    """PUT exception."""
    pass


class PostError(RequestError):
    """POST exception."""
    pass


class DeleteError(RequestError):
    """DEL exception."""
    pass


class MethodNotAllowedError(JSSError):
    """JSSObject is not allowed to use HTTP method."""
    pass


class SSLVerifyError(JSSError):
    """Server's certificate could not be verified."""
    pass
