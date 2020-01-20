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
"""pretty_element.py

Pretty-printing xml.etree.ElementTree.Element subclass
"""
from __future__ import absolute_import
import importlib
import re
import sys

from jss import tools


_DUNDER_PATTERN = re.compile(r'__[a-zA-Z]+__')
_RESERVED_METHODS = ('cached',)

# ElementTree monkey patch borrowed with love from Matteo Ferla.
# https://blog.matteoferla.com/2019/02/uniprot-xml-and-python-elementtree.html
sys.modules.pop('xml.etree.ElementTree', None)
sys.modules['_elementtree'] = None
ElementTree = importlib.import_module('xml.etree.ElementTree')


class PrettyElement(ElementTree.Element):
    """Pretty printing element subclass

    Element subclasses xml.etree.ElementTree.Element to pretty print.
    """

    def __init__(self, tag, attrib={}, **extra):
        if isinstance(tag, ElementTree.Element):
            super(PrettyElement, self).__init__(tag.tag, tag.attrib, **extra)
            self.text = tag.text
            self.tail = tag.tail
            self._children = [PrettyElement(child) for child in tag]
        else:
            super(PrettyElement, self).__init__(tag, attrib, **extra)

    # Replace standard Element.__str__ with our cache-aware
    # pretty-printing one.
    __str__ = tools.element_str

    def __getattr__(self, name):
        # Any dunder methods should be passed as is to the superclass.
        # There are also some method names which need to be assumed to
        # be from the superclass, lest we endlessly loop.
        if re.match(_DUNDER_PATTERN, name) or name in _RESERVED_METHODS:
            return super(PrettyElement, self).__getattr__(name)
        result = super(PrettyElement, self).find(name)
        if result is not None:
            return result
        else:
            raise AttributeError(
                'There is no element with the tag "{}"'.format(name))

    # TODO: This can be removed once `JSSObject.__init__` signature is fixed.
    def makeelement(self, tag, attrib):
        """Return a PrettyElement with tag and attrib."""
        # We have to override Element's makeelement, which uses the
        # class' __init__. Since python-jss objects override this and
        # repurpose it, instantiating a sub element with
        # ElementTree.SubElement or copy will fail.

        # This situation will be resolved when JSSObject stops
        # subclassing Element.
        return PrettyElement(tag, attrib)

    def append(self, item):
        super(PrettyElement, self).append(self._convert(item))

    def insert(self, index, item):
        super(PrettyElement, self).insert(index, self._convert(item))

    def extend(self, items):
        super(PrettyElement, self).extend(self._convert(item) for item in items)

    def _convert(self, item):
        """If item is not a PrettyElement, make it one"""
        return item if isinstance(item, PrettyElement) else PrettyElement(item)
