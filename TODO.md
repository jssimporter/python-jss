*__dict__ is a special class property which allows you to see all instance
variables as a dictionary of k=variable name, v=value. I don't see keeping
anything else there, but the python-gitlab code does, so I want to remember it
as an option if I get stuck and can't figure out how I'm jacking stuff up.
*Add sorting options for listing operations in jss_helper
*Add implementation checks for objects. e.g. _canGet, _canDelete, _calList, etc.
*Come up with a better _get_list_or_object/init that doesn't rely on int/string for id (have to be really careful about NOT passing str id's!
*Test PUT, document in README.
*Figure out how to do README for public release (markdown works on Github?)
*Implement further API features
	*accounts
	*activationcode
	*advancedcomputersearches
	*advancedmobiledevicesearches
	*buildings
	*classes
	*computerextensionattributes
	*computerinventorycollection
	*computerinvitations
	*computerreports
	*departments
	*directorybindings
	*diskencryptionconfigurations
	*distributionpoints
	*dockitems
	*ebooks
	*fileuploads
	*gsxconnection
	*jssuser
	*ldapservers
	*licensedsoftware
	*managedpreferenceprofiles
	*mobiledeviceapplications
	*mobiledevicecommands
	*mobiledeviceenrollmentprofiles
	*mobiledeviceextensionattributes
	*mobiledeviceinvitations
	*mobiledeviceprovisioningprofiles
	*netbootservers
	*networksegments
	*osxconfigurationprofiles
	*packages
	*peripherals
	*peripheraltypes
	*printers
	*restrictedsoftware
	*removablemacaddresses
	*savedsearches
	*scripts
	*sites
	*softwareupdateservers
	*smtpserver
*I don't like how the JSS._get_list_or_object() is the one that checks for can_listiness. See if I can move that out
*JSS.list does a super ugly list comprehension to crappy dict unpacking that could be cleaned up.