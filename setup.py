#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='python-jss',
      version='0.2',
      #py_modules=['jss', 'FoundationPlist'],
      packages=find_packages(),
      description='Python wrapper for JSS API.',
      long_description=open('README.md').read(),
      author='Shea G. Craig',
      author_email='shea.craig@da.org',
      url='https://github.com/sheagcraig/python-jss/',
      scripts=['jss_helper'],
      license='GPLv3',
      install_requires=["requests"],
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)']
     )
