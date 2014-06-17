#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup
setup(name='python-jss',
      version='0.2',
      py_modules=['jss', 'FoundationPlist'],
      description='Python wrapper for JSS API.',
      author='Shea G. Craig',
      author_email='shea.craig@da.org',
      url='https://github.com/sheagcraig/python-jss/',
      scripts=['jss_helper'],
      license='LICENSE.txt',
      install_requires=["requests"],)
