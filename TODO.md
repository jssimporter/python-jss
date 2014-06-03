*Fix TODO!

!Project Level
*Figure out how to do README for public release (markdown works on Github?)
*Update readme with new interface
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
*Add in permissions tests
*Write tests for search methods
*Add a cleanup or something to setup to clean out test Policy so I don't have to clicky clicky delete it.
*Audit existing tests
*Tests for all remaining to be implemented API features (do this before writing them)
	**Perhaps a more meaninful test for each would be to confirm that it has a top-level
	element, like <computer>.
	**Should test correct ID and name, since we rely on that.
		***Should ensure correct type.
*Devise a test for the rather complicated overload of data in JSSObject.__init__()

!JSS.py
*Have JSSObject inherit from Element
*JSSPolicyTemplates
	**Build them with a composite pattern, only implement the ones I'll need
	**Not sure about the back and forth between string and xml for this
*Implement container behavior.
	**Researching...
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

!JSS HELPER
*Needs a lot of work after major jss.py changes
*Add sorting options for listing operations in jss_helper