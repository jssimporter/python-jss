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


import copy
from xml.etree import ElementTree

import tools


class PrettyElement(ElementTree.Element):
    """Pretty printing element subclass

    Element subclasses xml.etree.ElementTree.Element to pretty print.
    """

    __str__ = tools.element_str

    def makeelement(self, tag, attrib):
        """Return a PrettyElement with tag and attrib."""
        # We have to override Element's makeelement, which uses the
        # class' __init__. Since python-jss objects override this and
        # repurpose it, instantiating a sub element with
        # ElementTree.SubElement or copy will fail.

        # This situation will be resolved when JSSObject stops
        # subclassing Element.
        return PrettyElement(tag, attrib)

