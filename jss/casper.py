#!/usr/bin/env python
"""casper.py

Utility class for getting and presenting information from casper.jxml.

The results from casper.jxml are undocumented and thus quite likely to be
removed. Do not rely on its continued existence!

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


import copy
from .contrib import requests
import urllib
from xml.etree import ElementTree


class Casper(ElementTree.Element):
    def __init__(self, jss):
        """Initialize a Casper object.

        jss:    JSS object.

        """
        self.jss = jss
        self.url = "%s%s" % (self.jss.base_url, '/casper.jxml')
        self.auth = urllib.urlencode({'username': self.jss.user,
                                      'password': self.jss.password})
        super(Casper, self).__init__(tag='Casper')
        self.update()

    def _indent(self, elem, level=0, more_sibs=False):
        """Indent an xml element object to prepare for pretty printing.

        Method is internal to discourage indenting the self._root Element,
        thus potentially corrupting it.

        """
        i = "\n"
        pad = '    '
        if level:
            i += (level - 1) * pad
        num_kids = len(elem)
        if num_kids:
            if not elem.text or not elem.text.strip():
                elem.text = i + pad
                if level:
                    elem.text += pad
            count = 0
            for kid in elem:
                self._indent(kid, level+1, count < num_kids - 1)
                count += 1
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
                if more_sibs:
                    elem.tail += pad
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
                if more_sibs:
                    elem.tail += pad

    def __repr__(self):
        """Make our data human readable."""
        # deepcopy so we don't mess with the valid XML.
        pretty_data = copy.deepcopy(self)
        self._indent(pretty_data)
        elementstring = ElementTree.tostring(pretty_data)
        return elementstring.encode('utf-8')

    def makeelement(self, tag, attrib):
        """Return an Element."""
        # We use ElementTree.SubElement() a lot. Unfortunately, it relies on a
        # super() call to its __class__.makeelement(), which will fail due to
        # the class NOT being Element.
        # This handles that issue.
        return ElementTree.Element(tag, attrib)

    def update(self):
        """Request an updated set of data from casper.jxml."""
        response = requests.post(self.url, data=self.auth)
        response_xml = ElementTree.fromstring(response.text)

        # Remove previous data, if any, and then add in response's XML.
        self.clear()
        for child in response_xml.getchildren():
            self.append(child)
