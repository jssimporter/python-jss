Introduction
============

This project aims to offer simple, elegant, pythonic access to the Jamf Casper JSS API.

`JAMF <https://www.jamf.com>`_ provides access to the JSS and most of its object types through a REST API.
**python-jss** allows you interact with the API to create new objects, list or edit the existing ones,
and to upload files to configured distribution points.

The level of coverage for convenience methods and properties is primarily centered on Computer management,
and specifically, those aspects which factor into policy and package management.

Automating policy creation is streamlined; however, class MobileDeviceInvitations provides nothing beyond basic
JSSObject methods and properties to the API.

Those aspects which I use heavily in our organization, and in support of
`JSSImporter <https://github.com/sheagcraig/JSSImporter>`_, tend to be more fleshed out,
whereas aspects of the JSS API that I never use tend to be minimalistic.

However, based on the code here, it should be easy for anyone wishing to do so to implement a **new()** method for
those objects they're interested in, and I would be happy to include them. Send me your pull requests!