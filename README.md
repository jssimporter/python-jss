python-jss Introduction:
=================
This project aims to offer simple, elegant, pythonic access to the Jamf Casper JSS API.

Jamf provides access to the JSS and most of its object types through a REST
API. python-jss allows you interact with the API to create new objects, list or
edit the existing ones, and to upload files to configured distribution points.

The level of coverage for convenience methods and properties
is primarily centered on Computer management, and specifically, those aspects
which factor into policy and package management.

Automating policy creation is streamlined; however, class
```MobileDeviceInvitations``` provides nothing beyond basic ```JSSObject```
methods and properties to the API. Those aspects which I use heavily in our
organization, and in support of
[jss-autopkg-addon](https://www.github.com/sheagcraig/jss-autopkg-addon), tend
to be more fleshed out, whereas aspects of the JSS API that I never use tend to
be minimalistic. However, based on the code here, it should be easy for anyone
wishing to do so to implement a ```new()``` method for those objects they're
interested in, and I would be happy to include them. Send me your pull
requests!

Usage:
=================
Please see [the wiki](https://github.com/sheagcraig/python-jss/wiki) for complete documentation.

Also, [my blog](http://www.sheacraig.com) has a series of posts about using python-jss, jss-autopkg-addon, and jss-helper, and solving unique problems using these tools.

Installing:
=================
The easiest method is to use pip to grab python-jss:
```
$ pip install python-jss
```

If you don't have pip, you should probably get it: https://pip.pypa.io/en/latest/installing.html

Alternately, download the source and copy the python-jss package wherever you normally install
your packages.

Behind the scenes, python-jss uses requests and Greg Neagle's FoundationPlist.
Check them out at:
requests: http://docs.python-requests.org/en/latest/
FoundationPlist is part of Munki: https://code.google.com/p/munki/

Data Validation:
=================
The wrapper prevents you from trying to delete object types that can't be
deleted, and from POSTing to objects that can't be created. It does zero
validation on any xml prior to POST or PUT operations. However, the JSS handles
all of this nicely, and ElementTree should keep you from creating improperly
formatted XML. If you get an exception, chances are good the structure of the
XML is off a bit.

The JSS also handles filling in missing information pretty well. For example,
in a policy scope, if you provide the id of a computer to scope to, it will add
the name.

Basics-Connecting to the JSS:
=================
Prior to doing anything else, you need a JSS object, representing one server.
Note, it's quite possible to have active connections to multiple servers for
transferring data between them!

```
# Connect to the JSS
>>> import jss
>>> jss_prefs = jss.JSSPrefs()
>>> j = jss.JSS(jss_prefs)
```

Supplying Credentials to the JSSPrefs object:
=================
You need a user account with API privileges on your JSS to connect and do anything useful. It is recommended that you create a user specifically for API access, with only the privileges required for the task at hand. For testing purposes, a fully-enabled admin account is fine, but for production, permissions should be finely controlled.

These settings are in the JSS System Settings=>JSS User Accounts & Groups panel.

The preferred method for specifying credentials is to create a preferences file
at "~/Library/Preferences/com.github.sheagcraig.python-jss.plist".  Required
keys include:
- jss_user
- jss_pass
- jss_url (Should be full URL with port, e.g. "https://myjss.domain.org:8443"
and can be set with:
```
defaults write ~/Library/Preferences/com.github.sheagcraig.python-jss.plist jss_user <username>
defaults write ~/Library/Preferences/com.github.sheagcraig.python-jss.plist jss_pass <password>
defaults write ~/Library/Preferences/com.github.sheagcraig.python-jss.plist jss_url <url>
```

If you want to work with File Share Distribution Points, or a JDS, to upload packages and scripts, see the section below on the DistributionPoints class.

If you are working on a non-OS X machine, the JSSPrefs object falls back to
using plistlib, although it's up to you to create the proper xml file.

Interacting with the JSS:
=================
In general, you should use the following workflow:
- To query for existing objects, use the factory methods on the server
  instance. For each object type listed in the API reference, there is a
  corresponding method: JSS.Package, JSS.MobileDeviceConfigurationProfile, etc.
  If the query is successful, it will return an object of the appropriate class,
  or for listing operations (no argument), it will return a list of objects.

  After careful consideration, I decided to do it this way rather than by using
  the composite pattern to treat lists and single objects similarly. In thinking
  about what operations I would want to perform, deleting ALL computers at once,
  or updating all policies at once, for example, seemed both dangerous and
  unnecessary.

  Also, the JSS returns different data structures for an object type
  depending on the context. A "full" object listing is _not_ the same thing as
  the greatly abbreviated data returned by a listing operation or a "match"
  search.  Likewise, trying to PUT a new object by just editing the full XML
  retrieved from an already existing object would fail. (For example, the ID
  property is assigned by the JSS, not you.)

  Therefore, there are a couple of object classes for each type of data:
  * JSSObject: All data on a single object, like a single computer, the activation
  code, or a policy.
  * JSSObjectList: A list of JSSListData objects, containing only the most
  important information on an object.

  I.e.:

  ```
  >>> # To query, provide a search argument:
  >>> existing_policy = j.Policy("Install Adobe Flash Player-14.0.0.125")
  >>> # To list, don't provide any arguments:
  >>> all_policies = j.Policy()
  ```

- For creating new objects (of classes which allow it) instantiate an object of
  the desired type directly. I.e.:

  ```
  >>> # This creates a new Policy object with the basic required XML.
  >>> new_policy = jss.Policy(j, "Al Pastor")
  >>> # When you are ready to add it to the server, perform a save...
  >>> new_policy.save()
  ```

  Notice that with _new_ objects you have to pass a reference to the server
  object to the object constructor. Think of this as associating this new
  object, in this case a Policy, with a server.

- Any time you want to save changes to an existing policy or upload a new one,
  call the .save() method on it. Continuing from above...

  ```
  >>> existing_policy.find('general/name').text = "Install Adobe Flash Player 202.0.0.14"
  >>> existing_policy.save()
  ```

- Deleting an object is a method on the object for those types which support it.

  ```
  >>> new_policy.delete()
  ```

Querying for Objects:
=================

Different objects allow different kinds of searches. Most objects allow you to
search by ID or by name.

```
>>> # Find a computer (returns a Computer object, which prints itself if not
>>> # assigned
>>> j.Computer('my-computer')
<computer>
	<general>
		<id>42</id>
		<name>my-computer</name>
		...
	</general>
	... # Tons of information removed for example's sake
</computer

>>> # Most JSSObjects have a name and id property.
>>> mycomputer = j.Computer('my-computer')
>>> mycomputer.name
'my-computer'
>>> mycomputer.id
'42'
>>> # ...as well as some extra properties on devices
>>> mycomputer.serial_number
'WXXXXXXXXXXX'
>>> mycomputer.udid
'1F38EB0B-XXXX-XXXX-XXXX-XXXXXXXXXXXX'

>>> # Computers have a list of addresses, since you can't be sure
>>> # what network devices they have
>>> mycomputer.mac_addresses
['3C:07:54:XX:XX:XX', '04:54:53:XX:XX:XX']

>>> # Mobile devices have wifi and bluetooth mac properties:
>>> myipad = j.MobileDevice('my-ipad')
>>> myipad.wifi_mac_address
'C3:PO:XX:XX:XX:X1'
>>> myipad.bluetooth_mac_address
'C3:PO:XX:XX:XX:X2'

>>> # Providing no arguments to the factory method returns a list.
>>> # (Some object types return only a set of data, like ActivationCode).
>>> computers = j.Computer()
>>> computers
--------------------------------------------------
List index: 	437
id:		453
name:		my-mbp
--------------------------------------------------
List index: 	438
id:		454
name:		my-imac
--------------------------------------------------
List index: 	439
id:		455
name:		USLab-test
--------------------------------------------------
... # Results go on...
```

Working with JSSObjectList(s):
=================

You can sort lists of objects, which by default uses the ID property. You can
also sort by name. Also, objects referenced in a list can be "converted" to full
objects by using the retrieve method.

Again, listing operations don't retrieve full information. A list of computers
returns only their names and ID's. A list of mobile devices returns a bit more
info: Serial number, mac addresses, UDID, and a few others. Obviously, the JSS
stores a lot more information on these devices, and indeed, pulling the "full"
object allows you to access that information.

```
>>> # Objects can be retrieved from this list by specifying an id or list index:
>>> myimac = computers.retrieve(438) # same as computers.retrieve_by_id(454)

>>> # The entire list can be "convertd" into a list of objects, although this
>>> # can be slow.
>>> full_computers_list = computers.retrieve_all()
```

The available object types can be found in the JSS API documentation. They are
named in the singular, with CamelCase, e.g. MobileDeviceConfigurationProfiles
for mobiledeviceconfigurationprofiles.

Of course, you can get a list like this as well:
```
>>> help(jss)
>>> help(jss.JSS) # For factory method names...
```

Manipulating JSSObjects:
=================
The JSS works with data as XML, and as such, python-jss's objects all inherit
from xml.etree.ElementTree. Users familiar with Elements will find manipulating
the data very easy. Those unfamiliar with ElementTree should check out
https://docs.python.org/2/library/xml.etree.elementtree.html and
http://effbot.org/zone/element-index.htm for great introductions to this useful
module.

python-jss adds a better __repr__ method to its JSSObjects and, however. Simply
print() or call an object in the interpretor to see a nicely indented
representation of the Element. This aids in quickly experimenting with and
manipulating data in the interpretor.

In addition to the various methods of Element, JSSObjects also provides helper
methods to wrap some of the more common tasks. Policies, for example, includes
methods for add_object_to_scope(), add_object_to_exclusions(), set_recon(),
set_set_service(), etc.

To see a full list of methods available for an object type, as well as their
signatures and docstrings:
```
Help on class Policy in module jss.jss:

class Policy(JSSContainerObject)
 |  Method resolution order:
 |      Policy
 |      JSSContainerObject
 |      JSSObject
 |      xml.etree.ElementTree.Element
 |      __builtin__.object
 |  
 |  Methods defined here:
 |  
 |  add_object_to_exclusions(self, obj)
 |      Add an object 'obj' to the appropriate scope exclusions block.
 |
 |      obj should be an instance of Computer, ComputerGroup, Building,
 |      or Department.
 |  
 |  add_object_to_scope(self, obj)
 |      Add an object 'obj' to the appropriate scope block.
 |  
 |  add_package(self, pkg)
 |      Add a jss.Package object to the policy with action=install.
 |  
 |  clear_scope(self)
 |      Clear all objects from the scope, including exclusions.
#...more methods and properties
```

Note: All data in the objects are strings! True/False values, int values, etc,
are all string unless you cast them yourself. The id properties of the various
objects are strings!

Example: Creating, Updating, and Deleting Objects:
=================
To create a new object, you need to instantiate the desired object type with a
reference to the JSS server you plan to upload to, and a name. Some object
types include extra keyword arguments to speed up initial setup.

Next, modify the object to your needs and then call the ```save()``` method.

```
>>> new_policy = jss.Policy(j, "New Policy")

>>> # Manipulate with Element methods
>>> new_policy.find('enabled').text = 'false'

>>> # Add a computer to the scope (accepts Computer objects, or ID or name)
>>> # First, let's grab a computer to scope to...
>>> myIIGS = j.Computer("myIIGS")
>>> # ...and add it to our policy's scope:
>>> new_policy.add_object_to_scope(myIIGS)
>>> # Up to this point, the object is not on the server. To upload it...
>>> new_policy.save()

>>> # Subsequent changes must also be saved:
>>> new_policy.find('general/name').text = 'Install Taco Software'
>>> new_policy.save()

>>> # ...and to delete it:
>>> new_policy.delete()
```

Distribution Points and Distribution Servers:
=================
Casper supports a few different means for handling package and script files:
- "File Share Distribution Points" corresponds to AFP and SMB mountable shares.
- "JDS Instances" are Jamf Distribution Servers, which store files in a database, and are not mountable (i.e., must be interacted with via HTML POSTs)
- "Cloud Distribution Point", which is currently unsupported by python-jss. (Coming as soon as I can set up a testing situation).

The JSS stores all of the information about your "File Share Distribution Points" in an API object named, appropriately "DistributionPoints". These repositories contain the packages and scripts that are deployed with policies, and are normally managed with the Casper Admin application.

JDS types have no corresponding API object, and are usually managed with the web-based "Packages" and "Scripts" pages of the web interface's "Computer Management" section.

python-jss includes classes to help work with these different repositories. When you create a JSS object, it includes a DistributionPoints object to delegate, named .distribution_points. e.g. ```my_jss.distribution_points```, to delegate file operations to. While you can always instantiate a DistributionPoints object (made up of DistributionPoint objects), or even set up individual DP's, it's probably easiest to use this delegated approach.

For this to be useful, you'll have to include some extra information in your ```com.github.sheagcraig.python-jss.plist``` file. Add a key ```repos```, with an array as its value. The array should contain dictionaries containing connection information for each DP you wish to include. It should look simlar to this: 
```
	<key>repos</key>
	<array>
		<dict>
			<key>name</key>
			<string>Repo1</string>
			<key>password</key>
			<string>xyzzy</string>
		</dict>
		<dict>
			<key>name</key>
			<string>Repo2</string>
			<key>URL</key>
			<string>repo.mydomain.org</string>
			<key>domain</key>
			<string>SCHWARTZ</string>
			<key>type</key>
			<string>SMB</string>
			<key>share_name</key>
			<string>Jamf</string>
			<key>username</key>
			<string>DarthHelmet</string>
			<key>password</key>
			<string>abc123</string>
		</dict>
	</array>
```

Notice two alternate forms for defining distribution points. The first uses just a name and a password. For SMB and AFP shares, the remaining connection information can be pulled from the JSS. ```name``` corresponds to the name field on the JSS Computer Management->File Share Distribution Points->Display Name field.

However, you may also specify the complete set of connection information. If you only specify ```name``` and ```password```, python-jss will assume you want to auto-configure an AFP or SMB share. All other DP types must be fully-configured. 

At this time, if you are not using the auto-configuration method, the following keys are required:
- AFP
	- name (optional)
	- URL
	- type='AFP'
	- port (optional)
	- share_name
	- username (rw user)
	- password
- SMB
	- name (optional)
	- URL
	- domain
	- type='SMB'
	- port (optional)
	- share_name
	- username (rw user)
	- password
- JDS
	- URL
	- type='JDS'
	- username (rw user)
	- password

Please see the Repository subclass' docstrings for a list of required arguments and information for you using them.

Once this is in place, the JSS object can be used to copy files to the distribution points with the copy methods. In general, ```copy()``` should be used, as it will enforce putting pkg and dmg files into Packages, and everything else into Scripts automatically. There are ```copy_pkg()``` and ```copy_script()``` methods too, however.

For mountable DP types, if the DP isn't mounted, the copy operation will mount it automatically. If it's important to keep the mount from appearing in the GUI, you can use the ```nobrowse=True``` parameter to the mount methods on the individual DP's. There are ```mount()``` and ```umount()``` methods to do this manually.

There are some differences between how the AFP/SMB shares work, and a JDS that you should be familiar with.

First, when you copy a file to an AFP or SMB share, the file just gets copied to the mounted directory. This does not create a ```jss.Package``` or ```jss.Script``` object. You must also use the python-jss ```Package.new()``` and ```Script.new()``` to create the objects in the database.

The Packages and Scripts directories must be flat, meaning no subdirectories (although technically, bundle-style packages are directories, but this is not an issue). When specifying the filename, the JSS will assume a package is in the Packages directory, and a script in the Scripts directory, so only specify the basename of the file (i.e. Correct: 'my_package.pkg' Incorrect: 'jamf/Packages/my_package.pkg').

It's not really important which order you do this in, with the only real side effect being that Casper Admin will report missing files if the Package/Script object has been created before it has been copied to the file shares.

On a JDS, when you ```JDS.copy()```, if you don't specify an ```id_``` number as a parameter, it will assume you want to create a new ```jss.Package``` ```jss.Script``` object. If, instead, you are trying to upload a file to correspond to an existing object, you must pass the id number to the ```id_``` parameter. ('id' is a reserved word in Python, so throughout python-jss, I use id_).

The second difference is in the ```exists()``` method. For AFP/SMB, it is pretty simple to just see if the file is present. On a JDS, it becomes more complicated. There is no officially documented way to see if a file is present. So the ```exists()``` method looks for a ```jss.Package``` or ```jss.Script``` object with a matching filename and assumes that the associated file is in the database. Of course, this isn't necessarily true, especially if you're monkeying around with python-jss, so there's an ```exists_using_casper``` method that uses the casper module of python-jss to check the undocumented casper.jxml results for proof of a file's existence and whether it has synced to all JDS children.

Finally, the ```mount``` and ```umount``` methods obviously don't apply to JDS'.

SSL Errors:
=================
Requests is in the process of integrating changes to urllib3 to support Server
Name Indication ('SNI') for python 2.x versions. If you are requesting SSL
verification (which is on by default in python-jss), _and_ your JSS uses SNI,
you will probably get Tracebacks that look like this:

```
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "requests/api.py", line 55, in get
    return request('get', url, **kwargs)
  File "requests/api.py", line 44, in request
    return session.request(method=method, url=url, **kwargs)
  File "requests/sessions.py", line 461, in request
    resp = self.send(prep, **send_kwargs)
  File "requests/sessions.py", line 567, in send
    r = adapter.send(request, **kwargs)
  File "requests/adapters.py", line 399, in send
    raise SSLError(e, request=request)
requests.exceptions.SSLError: hostname 'testssl-expire.disig.sk' doesn't match 'testssl-valid.disig.sk'
```

Installing and/or upgrading the following packages should solve the problem:
- pyOpenSSL
- ndg-httpsclient
- pyasn1

Supposedly, requests with py3.x does not have this problem, so developing with that environment may be a possibility for you as well.

Hopefully this is temporary, although requests' changelog does claim to have "Fix(ed) previously broken SNI support." at version 2.1.0 (Current included version is 2.4.0).

FoundationPlist, binary plists, and Python:
=================
python-jss should handle all plist operations correctly. However, you may see a
warning about FoundationPlist not importing.

OS X converts plists to binary these days, which will make the standard library
plistlib fail, claiming that the plist is "badly formed." Thus, python-jss
includes FoundationPlist. However, if you have installed python from a
non-Apple source (i.e. python.org), FoundationPlist's dependencies will not be
met, and python-jss will fall back to using plistlib. This will also happen on
non-OS X machines, where it should not be a problem, since they shouldn't be
secertly converting preferences to binary when you aren't looking.

To include binary plist support, you will need to ensure that
python-jss/FoundationPlist have access to the PyObjC package, and specifically
the Foundation module. In some circumstances, it can be as easy as adding the
path to the Apple-installed PyObjC to your PYTHONPATH. On my machine:

```
export PYTHONPATH=$PYTHONPATH:/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python/PyObjC:/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python
```

This won't work for Python3.x, and may not work for some setups of 2.x. You
should either try to install PyObjC ```sudo pip install pyobjc```, create a
plist file by hand rather than by using ```defaults``` (you could create the
file as described above and then ```plutil -convert xml1 plist_filename``` , or
just use the username and password arguments to the JSS constructor and avoid
using the JSSPrefs object.
