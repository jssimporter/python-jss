python-jss Introduction:
=================
This project provides a python wrapper for the Jamf JSS API.

Designing a wrapper for the JSS API allowed me to solve some of the issues I
was facing in administering our macs in more efficient ways. Increased use of
autopkg to automate our software deployment also led to an interest in the API
that Jamf provides. While this project aims to offer simple, elegant, pythonic
access to the JSS, the level of data construction and validation that may be
required for tasks beyond policy, package, and computer management may be
lacking.

A concrete example is the template system. While I rely heavily on automating
policy creation, I will not need implementations for MobileDeviceInvitations.
However, based on the code here, it should be easy for anyone wishing to do so
to implement a subclass of XMLEditor for those objects, and I would be
happy to include them. Send me your pull requests!

Installing:
=================
The easiest method is to use pip to grab python-jss:
```
$ pip install python-jss
```

Alternately, the python-jss package can be put wherever you normally install your modules.

Behind the scenes, python-jss uses requests and Greg Neagle's FoundationPlist.
Check them out at:
requests: http://docs.python-requests.org/en/latest/
FoundationPlist is part of Munki: https://code.google.com/p/munki/

Data Validation:
=================
The wrapper prevents you from trying to delete object types that can't be
deleted, and from POSTing to objects that can't be created. It does zero
validation on any JSSObjectTemplate or JSSObject xml prior to POST or PUT
operations. However, the JSS handles all of this nicely, and ElementTree should
keep you from creating improperly formatted XML.

The JSS also handles filling in missing information pretty well. For example,
in a policy scope, if you provide the id of a computer to scope to, it will add
the name.

Basics-Connecting to the JSS:
=================
```
# Connect to the JSS
>>> import jss
>>> jss_prefs = jss.JSSPrefs()
>>> j = jss.JSS(jss_prefs)
```

Supplying Credentials to the JSSPrefs object:
=================
The preferred method for specifying credentials is to create a preferences file
at "~/Library/Preferences/org.da.python-jss.plist".  Required keys include:
jss_user
jss_pass
jss_url (Should be full URL with port, e.g. "https://myjss.domain.org:8443"
and can be set with:
```
defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_user <username>
defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_password <password>
defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_url <url>
```
If you are working on a non-OS X machine, the JSSPrefs object falls back to
using plistlib, although it's up to you to create the proper xml file.

Interacting with the JSS:
=================
In general, you should use the constructor methods on the JSS to query
for existing objects and create new objects. The JSS will return either an
object subclassed from JSSObject, or a list of JSSListData objects.

Updating existing objects and deleting objects should be handled through the
methods.

After careful consideration, I decided to do it this way rather than by using
the composite pattern to treat lists and single objects similarly. In thinking
about what operations I would want to perform, deleting ALL computers at once,
or updating all policies at once, for example, seemed both dangerous and
unnecessary.

Also, the JSS returns different data structures for an object type
depending on the context. A "full" object listing is _not_ the same thing as the
greatly abbreviated data returned by a listing operation or a "match" search.
Likewise, trying to PUT a new object by just editing the full XML retrieved
from an already existing object would fail. (For example, the ID is assigned by
the JSS, not you.)

Therefore, there are a few object classes for each type of data:
* JSSObject: All data on a single object, like a single computer, the activation
code, or a policy.
* JSSObjectList: A list of JSSListData objects, containing only the most
important information on an object.
* JSSObjectTemplate: An snippet of XML sufficient to create a new object of that
class

I.e.:

To GET an existing object (JSS constructor)
```
>>> computers = j.Computer()
>>> computer = j.Computer(25)
```
Create a new object (JSS constructor)
```
>>> j.Computer(computer_template)
```
Once you have the JSSObject you can update/delete it. In this example, the
objects are of type Computer.
```
>>> computer.update()
POST: Success
>>> computer.delete()
DEL: Success
```

Querying for Objects:
=================
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

>>> # Providing no arguments to the method constructor returns a list.
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
>>> dir(jss.JSS)
```

Manipulating JSSObjects:
=================
The JSS works with data as XML, and as such, python-jss's objects all inherit
from xml.etree.ElementTree. Users familiar with Elements will find manipulating
the data very easy. Those unfamiliar with ElementTree should check out
https://docs.python.org/2/library/xml.etree.elementtree.html and
http://effbot.org/zone/element-index.htm for great introductions to this useful
module.

python-jss adds a better __repr__ method to its JSSObjects and
JSSObjectTemplates, however. Simply print() or call an object in the
interpretor to see a nicely indented representation of the Element. This aids
in quickly experimenting with and manipulating data in the interpretor.

In addition the various methods of Element, JSSObjects and JSSObjectTemplates
also inherit methods of XMLEditor, a class which adds helper methods to wrap
some of the more common tasks. Policies, for example, include a PolicyEditor,
which adds methods for add_object_to_scope(), add_object_to_exclusions(),
set_recon(), set_set_service(), etc.

To see a full list of methods available for an object type, as well as their
signatures and docstrings:
```
>>> help(jss.Policy)
class Policy(PolicyEditor, JSSContainerObject)
 |  Method resolution order:
 |      Policy
 |      PolicyEditor
 |      XMLEditor
 |      JSSContainerObject
 |      JSSObject
 |      xml.etree.ElementTree.Element
 |      __builtin__.object
 |
 |  Methods inherited from PolicyEditor:
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
 |      obj should be an instance of Computer, ComputerGroup, Building,
 |      or Department.
#...more methods and properties
```

Note: All data in the objects are strings! True/False values, int values, etc,
are all string unless you cast them yourself. The id properties of the various
objects are strings!

Note: At the moment I'm using multiple-inheritence to add the XMLEditor
methods. This leaves me uneasy. The benefit is that you can avoid a
"middle-man" dot reference to editor (e.g.
policy.editor.add_object_to_scope()), but the downside is that it's ugly, and
as the Zen of Python states, "Beautiful is better than ugly" ```import this```.

Creating, Updating, and Deleting Objects:
=================
To create a new object, you need to pass an instance of a JSSObjectTemplate.
JSSObjectTemplate is also an ElementTree Element, so you can manipulate its data in
the same way.

Modify the template to your needs and then call the method
constructor on the JSS instance.

```
>>> new_policy_data = jss.JSSPolicyTemplate()
>>>
>>> # Manipulate with Element methods
>>> new_policy_data.find('enabled').text = 'false'

>>> # Add a computer to the scope (accepts Computer objects, or ID or name)
>>> # First, let's grab a computer to scope to...
>>> myIIGS = j.Computer("myIIGS")
>>> # ...and add it to our policy's scope:
>>> new_policy_data.add_object_to_scope(myIIGS)
>>> # The constructor will return your new object, so assign it to a variable
>>> # if you want to further manipulate it.
>>> new_policy = j.Policy(new_policy_data)

>>> # To change and update this object:
>>> new_policy.find('general/name').text = 'Install Taco Software'
>>> new_policy.update()

>>> # ...and to delete it:
>>> new_policy.delete()
```

SSL Errors:
=================
Requests is in the process of integrating changes to urllib3 to support Server Name Indication ('SNI') for python 2.x versions. If you are requesting SSL verification (which is on by default in python-jss), _and_ your JSS uses SNI, you will probably get Tracebacks that look like this:
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

Hopefully this is temporary, although requests' changelog does claim to have "Fix(ed) previously broken SNI support." at version 2.1.0 (Current included version is 2.3.0).
