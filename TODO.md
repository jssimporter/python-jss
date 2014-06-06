*Fix TODO!

!Project Level
*Figure out how to do README for public release (markdown works on Github?)
*Update readme with new interface
	**Talk about why NOT composite
	**Strategy
	**Factory
	**Much validation occurs through JSS
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
*JSSObjectTemplate tests

!JSS.py
*match searches return a list type.
*Groups should be a container type or list type. Then you can retrieve elements.
*JSSPolicyTemplates
*Implement container behavior.
	**Researching...
*Implement further API features
	**accounts
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