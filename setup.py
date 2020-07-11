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
from __future__ import print_function
import os
from setuptools import setup, find_packages

from jss import __version__

# http://stackoverflow.com/questions/10718767/have-the-same-readme-both-in-markdown-and-restructuredtext
try:
    from pypandoc import convert

    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("Warning: pypandoc module not found, could not convert md to rst")
    read_md = lambda f: open(os.path.join(os.path.dirname(__file__), f), 'r').read()

setup(name='python-jss',
      version=__version__,
      packages=find_packages(),
      description='Python wrapper for JSS API.',
      long_description=read_md('README.md'),
      author='Shea G. Craig',
      url='https://github.com/JSSImporter/python-jss/',
      license='GPLv3',
      install_requires=['requests>=2.24.0'],
      extras_require={
          'reST': [
              "Sphinx>=3.1.2", "docutils>=0.16"]
      },
      setup_requires=['pytest-runner'],
      tests_require=[
          'pytest', 'coverage', 'pytest-docker'
      ],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)']
      )
