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
"""queryset.py

Class that adds some extra functionality to a basic list. Used as the
result of all queries in python-jss.
"""


from __future__ import absolute_import
from collections import defaultdict
try:
    import cPickle  # Python 2.X
except ImportError:
    import _pickle as cPickle  # Python 3+
import datetime
import os

from .jssobject import DATE_FMT, Identity


STR_FMT = "{0:>{1}} | {2:>{3}} | {4:>{5}}"


class QuerySet(list):
    """A list style collection of JSSObjects.

    Listing operations retrieve minimal or overview information for most
    object types. For example, we may want to see all the Computers on
    the JSS but that does not mean we want to do a full object GET for
    each one.

    QuerySets hold instances of a single type of JSSObject, and use the
    python list API, while adding some extra helper-methods on top.
    """

    def __init__(self, objects):
        """Construct a list of JSSObjects.

        Args:
            objects (sequence of JSSObjects):
                Sequences must be of a single class.
        """
        if objects and not len({i.__class__ for i in objects}) == 1:
            raise ValueError
        super(QuerySet, self).__init__(objects)
        self.sort()
        self.contained_class = objects[0].__class__ if objects else None

    def __str__(self):
        """Make data human readable."""
        # Make ID, Name first, no matter what.
        sort_keys = ["id", "name"]
        if self:
            sort_keys.extend([
                key for key in self[0]._basic_identity.keys() if
                key not in sort_keys])

        # Build a dict of max lengths per column for table output.
        lengths = defaultdict(int)
        for item in self:
            for key in sort_keys:
                val = item._basic_identity[key] or ""
                length = max(len(key), len(val))
                if length > lengths[key]:
                    lengths[key] = length

        # Build a format string for row output.
        format_strings = []
        for key in sort_keys:
            length = lengths[key]
            format_strings.append("{{data[{}]:>{}}}".format(key, length))

        cached = 'cached'
        cached_format = '| {{cached:>{}}} |'.format(len(cached))

        fmt = "| " + " | ".join(format_strings) + cached_format

        # Begin building output with header lines.
        # Contained class can be None
        contained_name = self.contained_class.__name__ if self.contained_class is not None else "Empty"
        results = ["{} QuerySet".format(contained_name)]
        headers = {key: key for key in lengths}
        header_line = fmt.format(data=headers, cached="cached")
        bar = len(header_line) * '-'
        results.extend([bar, header_line, bar])

        str_cached = (
            lambda i: str(i.cached) if isinstance(i.cached, bool) else 'True')

        table = [
            fmt.format(data=item._basic_identity, cached=str_cached(item)) for
            item in self]
        results.extend(table)

        results.append(bar)
        return "\n".join(results)

    def __repr__(self):
        """Make data human readable."""
        return "QuerySet({})".format(super(QuerySet, self).__repr__())

    def sort(self, **kwargs):
        """Sort list elements by ID.
        """
        super(QuerySet, self).sort(key=lambda k: int(k.id))

    def sort_by_name(self):
        """Sort list elements by name."""
        super(QuerySet, self).sort(key=lambda k: k.name.upper())

    def retrieve_all(self):
        """Tell each contained object to retrieve its data from the JSS

        This can take a long time given a large number of objects,
        and depending on the size of each object.

        Returns:
            self (QuerySet) to allow method chaining.
        """
        for obj in self:
            if not obj.cached:
                obj.retrieve()

        return self

    def save_all(self):
        """Tell each contained object to save its data to the JSS

        This can take a long time given a large number of objects,
        and depending on the size of each object.

        Returns:
            self (QuerySet) to allow method chaining.
        """
        for obj in self:
            obj.save()

        return self

    def invalidate(self):
        """Clear the cache datetime for all contents.

        This causes objects to retrieve their data again when accessed.
        """
        for i in self: i.cached = False

    def names(self):
        """Return a generator of contents names"""
        return (item.name for item in self)

    def ids(self):
        """Return a generator of contents ids"""
        return (item.id for item in self)

    @classmethod
    def from_response(cls, obj_class, response, jss=None, **kwargs):
        """Build a QuerySet from a listing Response."""
        response_objects = (
            i for i in response if i is not None and i.tag != "size")

        dicts = (
            {child.tag: child.text for child in item} for item in
            response_objects)
        identities = (Identity(d) for d in dicts)

        objects = [obj_class(jss, data=i, **kwargs) for i in identities]

        return cls(objects)
