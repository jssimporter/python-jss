### 0.3 (UNRELEASED)

CHANGES:

- Removed Templates and XMLEditor classes.
  - All editor behaviors / methods moved into appropriate JSSObject subclasses.
  - For example, Policies gain all of their previously inherited PolicyEditor methods.
  - Templates' __init__ methods have become the new() method on objects.
  - Only implemented the existing set of: Category, ComputerGroup, MobileDeviceGroup, Package, Policy
  - SearchCriteria remains an object, although no longer inherits from a template.
- Creating new objects has changed as a result
  - To create an object now, use the class constructor with the string argument "name", configure as before, and then update().
  - i.e.
    ```
	policy = Policy(jss_instance, "Install Adventure")  
	policy.update()  
	```

### 0.2.2 (UNRELEASED)

ADDITIONS:

- jss_helper now has a promotion feature... Except see CHANGES below.

CHANGES:

- XMLEditor.add_object_to_list() now returns the element added.
- JSSObject.update() now accepts a template as a parameter (defaults to None) to replace instance's data from a template.
- Removing jss_helper to its own project, here: https://github.com/sheagcraig/jss_helper

FIXES:

- XMLEditor.add_object_to_list() fixed.
- PolicyEditor.add_package() fixed.
- JSSObject.update() did not properly update instance's data.

### 0.2.1 (June 25, 2014)

ADDITIONS:

- Adds TemplateFromFile and TemplateFromString objects for using external template files and strings. 
- Adds batch_scope feature to jss_helper.

CHANGES:

- Added requests and FoundationPlist to contrib folder of package. No longer need separate installation.
- Should now "just work" even if PyObjC/Foundation are not available. (See end of README).
- Renamed the default preferences file to reference github.

FIXES:

- Should not see SSL handshake errors now. JSS object now has a requests.Session object which prevents having to continually renegotiate. Bonus: It seems to be significantly faster as a result.

ISSUES:

- Requests does not automatically handle SNI out of the box for python 2.x. README describes necessary steps to work around this if needed. Thanks to Greg Neagle for pointing this out.

### 0.2.0 (June 18, 2014)

FEATURES:

- Initial release.