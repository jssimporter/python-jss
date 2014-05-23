*__dict__ is a special class property which allows you to see all instance
variables as a dictionary of k=variable name, v=value. I don't see keeping
anything else there, but the python-gitlab code does, so I want to remember it
as an option if I get stuck and can't figure out how I'm jacking stuff up.
*Add sorting options for listing operations in jss_helper
*Add implementation checks for objects. e.g. _canGet, _canDelete, _calList, etc.
*Come up with a better _get_list_or_object/init that doesn't rely on int/string for id (have to be really careful about NOT passing str id's!
*For objects like ActivationCode, xml property needs to get set correctly-there is no "list" happening here; it just returns data.
	*This is the point of the (not implemented) can_list or possibly an return type attribute. Some objects return xml rather than a list.