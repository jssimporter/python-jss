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
*Audit existing tests
*Tests for all remaining to be implemented API features (do this before writing them)
	**Perhaps a more meaninful test for each would be to confirm that it has a top-level
	element, like <computer>.
	**Should test correct ID and name, since we rely on that.
		***Should ensure correct type.
*Devise a test for the rather complicated overload of data in JSSObject.__init__()

!JSS.py
*Double check implementation checks for objects. e.g. _canGet, _canDelete, _canList, etc.
	**Do I cover the full range?
	**Do they work
*__dict__ is a special class property which allows you to see all instance
variables as a dictionary of k=variable name, v=value. I don't see keeping
anything else there, but the python-gitlab code does, so I want to remember it
as an option if I get stuck and can't figure out how I'm jacking stuff up.
*Should .data have getters/setters?
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