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
"""uapi.py

Classes representing UAPI endpoints that are more RPC style than CRUD.
"""


__all__ = 'SystemInitialize',


class SystemInitialize(object):
    _endpoint_path = "system/initialize"
    can_get = False
    can_put = False
    can_delete = False

    def __init__(self, jss):
        """Initialize a new SystemInitialize

        Args:
            jss: JSS object.
        """
        self.jss = jss

    @property
    def url(self):
        """Return the path subcomponent of the url to this object."""
        return self._endpoint_path

    def initialize(self, data):
        r = self.jss.post(self.url, data)


class RecalculateComputerSmartGroups(object):
    _endpoint_path = "computer/obj/computer"
    can_get = False
    can_put = False
    can_delete = False


class RecalculateSmartGroupComputers(object):
    _endpoint_path = "computer/obj/smartgroup"
    can_get = False
    can_put = False
    can_delete = False
