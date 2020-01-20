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
"""jssobjectlist.py

Deprecated in favor of QuerySet.
"""


from __future__ import absolute_import
import warnings

from .queryset import QuerySet


class JSSObjectList(QuerySet):
    """Deprecated in favor of QuerySet."""

    def __init__(self, factory, obj_class, objects=None):
        super(JSSObjectList, self).__init__(objects)
        warnings.warn(
            'JSSObjectList is deprecated and will be removed in the future. '
            'Please update code to use jss.QuerySet.', FutureWarning,
            stacklevel=2)
