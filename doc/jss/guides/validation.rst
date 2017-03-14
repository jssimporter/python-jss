Data Validation
===============

The wrapper prevents you from trying to delete object types that can't be deleted, and from POSTing to
objects that can't be created.

It does zero validation on any xml prior to POST or PUT operations. However, the JSS handles all of this nicely,
and ElementTree should keep you from creating improperly formatted XML. If you get an exception,
chances are good the structure of the XML is off a bit.

The JSS also handles filling in missing information pretty well. For example, in a policy scope,
if you provide the id of a computer to scope to, it will add the name.