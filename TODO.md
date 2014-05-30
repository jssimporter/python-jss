!Project Level
*Figure out how to do README for public release (markdown works on Github?)
*Document changes in README.
	**add put/update
	**add list/get procedure
	**mention id/name property/methods (need to fix...)
*Pylint
*Research whether there will need to be any container JSSObjects
	**In python-gitlab, a project then has commits, files, members, etc.
	**Not sure if it is going overboard to be able to manipulate objects this way-
		***Group membership
		***Scope
	**Not sure that it's as simple as just popping a <computer><id>5</id></computer into the scope
	**How can we be sure that it's valid for all cases to take a full object's xml representation
	and pop it into a scope, for example? Or the other way around?
	**On the other hand, for very common operations, where you just add an ID to a list, it might
	be pretty easy to write a generic method that can handle any child class using it to generate
	simple <object><id> pairs and insert them.
	**At least, it could be set up for the ones I intend on using, and examples of how to do it
	yourself put into the README.

!test/jss_test.py
*Add a cleanup or something to setup to clean out test Policy so I don't have to clicky clicky delete it.
*Audit existing tests
*Tests for all remaining to be implemented API features (do this before writing them)
	**Perhaps a more meaninful test for each would be to confirm that it has a top-level
	element, like <computer>.
	**Should test correct ID and name, since we rely on that.
		***Should ensure correct type.
*Devise a test for the rather complicated overload of data in JSSObject.__init__()

!JSS.py
*I set up searching for strings. However, after thinking about it, I think I
would rather have one data argument like before. I would need a helper method
to parse strings, but I could override computer and mobile device to default to
match searches (which just searches udid, sn, mac, name), and everything else
could be passed a string like this: "udid=134123409dfad09u23234r" and the string
parser would seperate out the type of search from the data. This would involve
some case sanitization, and whatnot, but pretty simple. = should be an acceptable
delimiter. And honestly, I do not think that many other objects even have a search
feature beyond name, so this may just be moot.
	**I think I can override __init__ like:

class Computer(JSSObject):
	def __init__(self, jss, data):
		search_type, data = self.string_parser(data)
		if isinstance(data, str) and search_type is None:
			data = '%s%s' % ('/match/', data)
			super(Computer, self).__init__(self, jss, data)

All others would probably have '/name/' as the search type default. Probably just need to
run down the list and see.
*The overloading algorithm seems overly complicated. This should be cleaned up.
	**There are two ways to create an object:
		***JSS.Computer()
		***Computer()
	**I am tempted to just make the JSSObjects private, or at least discourage people from
	using them in the readme.
	**What's the need for separating get_request() from get()?
	**Concerned about logic errors that can allow you to post to non-postable objects, etc
	**In one place we have the url_suffix='/id/' default, and in another search='/name/'.
		***This either needs to be cleared up so there's only one, or documented appropriately
		so it's not such a mystery.
*Decide whether I wnat to keep in the crazy list() code where I instantiate a class as part
of a list comprehension with a dict comprehension inside of it. Yee haw!

*Double check implementation checks for objects. e.g. _canGet, _canDelete, _canList, etc.
	**Do I cover the full range?
	**Do they work
*Implement container behavior.
	**Researching...
*Should .data have getters/setters as a safety net?
*Sort out id/name method on JSSObject.
	**Should there be more? (UDID, SN, MAC)
	**Should they be @property
*Implement further API features
	**accounts
	**activationcode
	**advancedcomputersearches
	**advancedmobiledevicesearches
	**buildings
	**classes
	**computerextensionattributes
	**computerinventorycollection
	**computerinvitations
	**computerreports
	**departments
	**directorybindings
	**diskencryptionconfigurations
	**distributionpoints
	**dockitems
	**ebooks
	**fileuploads
	**gsxconnection
	**jssuser
	**ldapservers
	**licensedsoftware
	**managedpreferenceprofiles
	**mobiledeviceapplications
	**mobiledevicecommands
	**mobiledeviceenrollmentprofiles
	**mobiledeviceextensionattributes
	**mobiledeviceinvitations
	**mobiledeviceprovisioningprofiles
	**netbootservers
	**networksegments
	**osxconfigurationprofiles
	**packages
	**peripherals
	**peripheraltypes
	**printers
	**restrictedsoftware
	**removablemacaddresses
	**savedsearches
	**scripts
	**sites
	**softwareupdateservers
	**smtpserver
*JSS.list does a super ugly list comprehension to crappy dict unpacking that could be cleaned up.

!JSS HELPER
*Add sorting options for listing operations in jss_helper
*Revert to using id/name method instead of dict access for a few functions
*Add ability to search using name or ID, and for some objects, SN, UDID, MAC, etc.
*Use Element.findtext(path) rather than if Element.find(path).text ==