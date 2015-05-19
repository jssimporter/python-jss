#!/usr/bin/env python
"""
tools.py
Helper functions for python-jss.

Copyright (C) 2014, 2015 Shea G Craig <shea.craig@da.org>

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


import os


def is_osx():
    """Convenience function for testing OS version."""
    result = False
    if os.uname()[0] == "Darwin":
        result = True
    return result


def is_linux():
    """Convenience function for testing OS version."""
    result = False
    if os.uname()[0] == "Linux":
        result = True
    return result
