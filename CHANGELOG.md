### 0.2.2 (UNRELEASED)

ADDITIONS:

- jss_helper now has a promotion feature.

CHANGES:

- XMLEditor.add_object_to_list() now returns the element added.
- JSSObject.update() now accepts a template as a parameter (defaults to None) to replace instance's data from a template.

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