# python-jss

## Introduction:
This project aims to offer simple, elegant, pythonic access to the Jamf Casper JSS API.

Jamf provides access to the JSS and most of its object types through a REST
API. python-jss allows you interact with the API to create new objects, list or
edit the existing ones, and to upload files to configured distribution points.

The level of coverage for convenience methods and properties
is primarily centered on Computer management, and specifically, those aspects
which factor into policy and package management.

Automating policy creation is streamlined; however, class
`MobileDeviceInvitations` provides nothing beyond basic `JSSObject`
methods and properties to the API. Those aspects which I use heavily in our
organization, and in support of
[JSSImporter](https://www.github.com/sheagcraig/JSSImporter), tend
to be more fleshed out, whereas aspects of the JSS API that I never use tend to
be minimalistic. However, based on the code here, it should be easy for anyone
wishing to do so to implement a `new()` method for those objects they're
interested in, and I would be happy to include them. Send me your pull
requests!

## Installing:
The easiest method is to use pip to grab python-jss:
`$ pip install python-jss`

However, if you use JSSImporter, its package installer uses easy_install since that is included on pre-10.10.5 OS X. You may want to use easy_install instead:
`$ easy_install -U python-jss`.

If you don't have pip, you should probably get it: https://pip.pypa.io/en/latest/installing.html

Alternately, download the source and copy the python-jss package wherever you normally install
your packages.

Behind the scenes, python-jss requires the requests, pyasn1, and ndg-httpsclient packages. If you install using easy-install or pip, these dependencies are handled for you. Otherwise, you'll have to acquire them yourself:
`easy_install -U pyasn1 ndg-httpsclient requests`

## Linux:
python-jss on Linux has some extra dependencies if you need to be able to mount distribution points.
- AFP distribution points require the `fuse-afp` package.
- SMB distribution points require the `cifs-utils` package. 

As I'm currently developing on Fedora, these requirements are specific to RedHat-based distros. Feel free to test and comment on Debian so I can update!

## Usage:
Please see [the wiki](https://github.com/sheagcraig/python-jss/wiki) for complete documentation.

Also, [my blog](http://sheagcraig.github.io) has a series of posts about using [python-jss](https://github.com/sheagcraig/python-jss), [JSSImporter](https://github.com/sheagcraig/JSSImporter), and [jss_helper](https://github.com/sheagcraig/jss_helper), and solving unique problems using these tools.
