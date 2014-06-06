This project provides a python wrapper for the Jamf JSS API.

Designing a wrapper for the JSS API allowed me to solve some of the issues I
was facing in administering our macs in more efficient ways. Increased use of
autopkg to automate our software deployment also led to an interest in the API
that Jamf provides. While this project aims to offer simple, elegant, pythonic
access to the JSS, the level of data construction and validation that may be
required of a full-featured wrapper will probably lag behind that which I
actually use.

A concrete example is the template system. While I use this for
automating policy creation frequently, in my day-to-day usage, I will not need
implementations for MobileDeviceInvitations. However, based on the code here,
it should be easy for anyone wishing to do so to implement a subclass of
JSSObjectTemplate for those objects, and I would be happy to include them. Send
me your pull requests!

Installing:
The python-jss module can be put wherever you normally install your modules. At
some point I may get around to making a pip install.

It has one non-included dependency, the requests HTTP module, which you can
usually obtain by:
$ pip install requests

(It also uses Greg Neagle's FoundationPlist module to eliminate binary plist issues.)

SSL Errors:
Warning: Due to SSL bugs, requests can fail with an SSL exception:
requests.exceptions.SSLError "error:14094410:SSL routines:SSL3_READ_BYTES:sslv3
alert handshake failure"

This usually isn't a problem for single calls, but when rapidly making multiple
calls, is nearly inevitable. Planning for failure is prudent, and when
anticipating large numbers of api requests, the best solution I have come up
with is to wrap these sorts of situations in a while, with a try/except block
to handle the exception.

Data Validation:
The wrapper prevents you from trying to delete object types that can't be
deleted, and from POSTing to objects that can't be created. It does zero
validation on any JSSObjectTemplate or JSSObject xml prior to POST or PUT
operations. However, the JSS handles all of this nicely, and ElementTree should
keep you from creating improperly formatted XML.

Basics-Connecting to the JSS:
# Connect to the JSS
>>> import jss
>>> jss_prefs = jss.JSSPrefs()
>>> j = jss.JSS(jss_prefs)

Supplying Credentials to the JSSPrefs object:
The preferred method for specifying credentials is to create a preferences file
at "~/Library/Preferences/org.da.python-jss.plist".  Required keys include:
jss_user
jss_pass
jss_url (Should be full URL with port, e.g. "https://myjss.domain.org:8443"
and can be set with:
"defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_user <username>"
"defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_password <password>"
"defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_url <url>"

If you are working on a non-OS X machine, the JSSPrefs object falls back to
using plistlib, although it's up to you to create the proper xml file.

Interacting with the JSS:
In general, you should use the constructor methods on the JSS object to query
for existing objects and create new objects. The JSS object will return an
object subclassed from JSSObject.

Updating existing objects and deleting objects should be handled through the
object's methods.

I.e.:

To GET an existing object (JSS constructor)
>>> computers = j.Computer()
>>> computer = j.Computer(25)
Create a new object (JSS constructor)
>>> j.Computer(computer_template)

Once you have the JSSObject you can update/delete it. In this example, the
objects are of type Computer.
>>> computer.update()
POST: Success
>>> computer.delete()
DEL: Success

Querying for Objects:
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
42
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

The available object types can be found in the JSS API documentation. They are
named in the singular, with CamelCase, e.g. MobileDeviceConfigurationProfiles
for mobiledeviceconfigurationprofiles.

Of course, you can get a list like this as well:
>>> dir(jss.JSS)

Manipulating JSSObjects:
JSSObject inherits xml.etree.ElementTree, so all xml data can be manipulated
per that module. Simply print() the object or call it in the interpretor to
print a nicely indented representation of the internal xml. This can be very
helpful in sorting out find() paths and elements of the object's data.

Note: All data in the objects are strings! True/False values, int values, etc,
are all string unless you cast them yourself. The id properties of the various
objects _do_ convert to int, but otherwise you are on your own.

Creating, Updating, and Delete Objects:
To create a new object, you need to pass an instance of a JSSObjectTemplate.
JSSObjectTemplate is also an ElementTree, so you can manipulate their data in
the same way.  

Modify the template to your needs and then call the method
constructor on the JSS instance.  

>>> new_policy_data = jss.JSSPolicyTemplate()
>>> new_policy_data.find['enabled'].text = 'false'
>>> # The constructor will return your new object...
>>> new_policy = j.Policy(new_policy_data)
POST: Success

>>> # To change and update this object:
>>> new_policy.find('general/name').text = 'Install Taco Software'
>>> new_policy.update()
PUT: Success

>>> # ...and to delete it:
>>> new_policy.delete()
DEL: Success
