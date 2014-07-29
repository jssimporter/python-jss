#!/usr/bin/env python

from setuptools import setup, find_packages

#http://stackoverflow.com/questions/10718767/have-the-same-readme-both-in-markdown-and-restructuredtext
try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("Warning: pypandoc module not found, could not convert md to rst")
    read_md = lambda f: open(f, 'r').read()

setup(name='python-jss',
      version='0.3.2',
      #py_modules=['jss', 'FoundationPlist'],
      packages=find_packages(),
      package_data = {
          # Make sure to include Requests cacert.cer file
          '': ['*.pem', '*.md'],
      },
      description='Python wrapper for JSS API.',
      long_description=read_md('README.md'),
      author='Shea G. Craig',
      author_email='shea.craig@da.org',
      url='https://github.com/sheagcraig/python-jss/',
      license='GPLv3',
      #install_requires=["requests"],
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)']
     )
