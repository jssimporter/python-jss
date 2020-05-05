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
"""abc.py

This module describes abstract base classes used throughout python-jss.
Shea would call this non-pythonic but i'd like to verify exactly which subclasses are conforming 100% to
a declared interface - mosen.
"""

from __future__ import absolute_import
import abc


class AbstractRepository(object):

    # If these attributes arent supplied in the constructor, Repository raises a JSSError
    #required_attrs = set()

    # connection arguments
    # connection

    @abc.abstractmethod
    def copy_pkg(self, filename, id_=-1):  # type: (str, Optional[int]) -> None
        """Copy a package to the repo's Package subdirectory.

        Args:
            filename: Path for file to copy.
            id_: ID of Package object to associate with, or -1 for new
                packages (default). Only required for JDS
        """
        pass

    @abc.abstractmethod
    def delete(self, filename):  # type: (str) -> None
        """Delete a file from the repository.

        Args:
            filename: String filename only (i.e. no path) of file to
                delete.
        """
        pass

    @abc.abstractmethod
    def exists(self, filename):  # type: (str) -> bool
        """Report whether a file exists on the distribution point.

        Determines file type by extension.

        Args:
            filename: Filename you wish to check. (No path! e.g.:
                "AdobeFlashPlayer-14.0.0.176.pkg")
        """
        pass
