Basic Usage
===========

Connecting to the JSS
---------------------

Prior to doing anything else, you need a JSS object, representing one server.

.. note:: It's quite possible to have active connections to multiple servers for transferring data between them!

Connect to the JSS::

    >>> import jss
    >>> jss_prefs = jss.JSSPrefs()
    >>> j = jss.JSS(jss_prefs)

Interacting with the JSS
------------------------

In general, you should use the following workflow:

To query for existing objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To query for existing objects, use the factory methods on the server instance.

For each object type listed in the API reference, there is a corresponding method:
``JSS.Package``, ``JSS.MobileDeviceConfigurationProfile``, etc.
If the query is successful, it will return an object of the appropriate class,
or for listing operations (no argument), it will return a list of objects [1]_.

There are a couple of object classes for each type of data:

JSSObject
    All data on a single object, like a single computer, the activation code, or a policy.
JSSObjectList
    A list of JSSListData objects, containing only the most important information on an object.

Example::

    >>> # To query, provide a search argument:
    >>> existing_policy = j.Policy("Install Adobe Flash Player-14.0.0.125")
    >>> # To list, don't provide any arguments:
    >>> all_policies = j.Policy()

Creating new objects
^^^^^^^^^^^^^^^^^^^^

For creating new objects (of classes which allow it) instantiate an object of the desired type directly::

    >>> # This creates a new Policy object with the basic required XML.
    >>> new_policy = jss.Policy(j, "Al Pastor")
    >>> # When you are ready to add it to the server, perform a save...
    >>> new_policy.save()

Notice that with *new* objects you have to pass a reference to the server object to the object constructor.
Think of this as associating this new object, in this case a Policy, with a server.

Updating objects
^^^^^^^^^^^^^^^^

Any time you want to save changes to an existing policy or upload a new one, call the .save() method on it::

    >>> existing_policy.find('general/name').text = "Install Adobe Flash Player 202.0.0.14"
    >>> existing_policy.save()

Deleting objects
^^^^^^^^^^^^^^^^

Deleting an object is a method on the object for those types which support it::

    >>> new_policy.delete()


Querying for Objects
--------------------

Different objects allow different kinds of searches. Most objects allow you to search by ID or by name.

Example::

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
    List index:     437
    id:     453
    name:       my-mbp
    --------------------------------------------------
    List index:     438
    id:     454
    name:       my-imac
    --------------------------------------------------
    List index:     439
    id:     455
    name:       USLab-test
    --------------------------------------------------
    ... # Results go on...

Manipulating JSSObjects
-----------------------

The JSS works with data as XML, and as such, python-jss's objects all inherit from xml.etree.ElementTree.
Users familiar with Elements will find manipulating the data very easy.
Those unfamiliar with ElementTree should check out
`The official documentation <https://docs.python.org/2/library/xml.etree.elementtree.html>`_ and
http://effbot.org/zone/element-index.htm for great introductions to this useful module.

python-jss adds a better repr method to its JSSObjects.
Simply **print()** or call an object in the interpreter to see a nicely indented representation of the Element.
This aids in quickly experimenting with and manipulating data in the interpreter.

In addition to the various methods of Element, JSSObjects also provides helper methods to wrap some of the more common
tasks. Policies, for example, includes methods for **add_object_to_scope()**, **add_object_to_exclusions()**, **set_recon()**,
**set_set_service()**, etc.

To see a full list of methods available for an object type, as well as their signatures and docstrings, use pythons
built in **help()** function::

    >>> help(jss.Policy)

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

.. tip:: All data in the objects are strings! True/False values, int values, etc, are all string unless you cast
    them yourself. The id properties of the various objects are strings!

Example: Creating, Updating and Deleting Objects
------------------------------------------------

To create a new object, you need to instantiate the desired object type with a reference to the JSS server
you plan to upload to, and a name. Some object types include extra keyword arguments to speed up initial setup.

Next, modify the object to your needs and then call the **save()** method::

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


.. [1] After careful consideration, I decided to do it this way rather than by using the composite pattern to treat lists
   and single objects similarly. In thinking about what operations I would want to perform, deleting ALL computers at
   once, or updating all policies at once, for example, seemed both dangerous and unnecessary.
   Also, the JSS returns different data structures for an object type depending on the context.
   A "full" object listing is not the same thing as the greatly abbreviated data returned by a listing operation or
   a "match" search. Likewise, trying to PUT a new object by just editing the full XML retrieved from an already
   existing object would fail. (For example, the ID property is assigned by the JSS, not you.)