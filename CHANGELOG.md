### 0.3.9 (September 3, 2014) Chorizo

FIXES:

- Fix resource name when using FileUpload. Previous behavior was to give resource the full upload path as a name. Switched to just os.path.basename()

ADDITIONS:

- Add method ```DistributionPoints.exists()``` for testing for the existence of a script/pkg across all distribution points.

### 0.3.7 (August 29, 2014) Hot Dog Sundae

ADDITIONS:

- Add module ```distribution_points```. Provides:
  - ```DistributionPoints``` to handle copying packages and scripts across all configured repositories.
	- Distribution points are automatically configured (except for password until I can figure out the hashing) based on your JSS's data.
	- copy copies a file to the directory indicated by the file extension (.pkg, .dmg to Packages, everything else to Scripts) of all distribution points.
	- copy_pkg copies a .pkg or .dmg to the Packages directory of all distribution points.
	- copy_script copies a script to the Scripts directory of all distribution points.
	- Distribution points are mounted prior to copy operations if they aren't already.
  - ```AFPRepository```, ```SMBRepository```, ```HTTPRepository```, ```HTTPSRepository```, and ```JDSRepository```. (Only AFP and SMB implemented currently-HTTP(S) and JDS coming soon.)
	- mount (Has option to mount -o nobrowse, so disk doesn't appear in GUI)
	- umount

CHANGES:

- Add handling of ```repos``` preference key in com.github.sheagcraig.python-jss.plist. See README.
- JSS objects now have a DistributionPoint property included at init time, so you don't need to instantiate one. Just delegate!

### 0.3.5 (August 21, 2014) Retcon Cheese Sauce

CHANGES:

- Implemented FileUpload. They are kind of unique in the way they operate, so check the docstring for more info.

### 0.3.4 (August 8, 2014)

NOTES:

- The interface will stay the same now. Only new features and fixes from here on out.

CHANGES:

- Add ```__version__``` property to module. Use for version checking if needed.

### 0.3.3 (July 31, 2014)

CHANGES:

- Reorganized ```JSSObject.save()``` logic to try to update first. Trying to create a new object first with existing objects results in a name conflict exception, which you then have to catch. But when you DO have a name conflict, you really would like to know. This saves the need to wrap save calls in a try/except for updating existing objects. E.g. batch_scope verb of jss_helper.

### 0.3.2 (July 29, 2014)

FIXES:

- Fixed error where pypi packages did not include the cacert.pem file included with requests.

### 0.3.1 (July 17, 2014)

CHANGES:

- ```JSS._error_handler()``` now adds a ```status_code``` attribute to exceptions.

FIXES:

- ```JSSObject.save()``` was confusing. If you created a new object with
  ```JSSObject()``` that conflicted with an existing object on the JSS, the save
  would fail with a ```JSSPutError```. Now we check for conflicts and instead return
  a ```JSSPostError``` with a more helpful error message.
- I mistakenly listed the preference key as ```jss_password``` in the README. Now the code and README agree: ```jss_pass``` is the correct key.

### 0.3 (July 3, 2014)

CHANGES:

- Removed Templates and XMLEditor classes.
  - All editor behaviors / methods moved into appropriate JSSObject subclasses.
  - For example, Policies gain all of their previously inherited PolicyEditor methods.
  - Templates' __init__ methods have become the new() method on objects.
  - Only implemented the existing set of: Category, ComputerGroup, MobileDeviceGroup, Package, Policy
  - SearchCriteria remains an object, although no longer inherits from a template.
- Renamed ```JSSObject.update()``` to ```JSSObject.save()``` to represent its added responsibilities (it can now post new objects as well)
- Creating new objects has changed as a result
  - To create an object now, use the class constructor with the string argument "name", configure as before, and then save().
  - i.e.
    ```
	policy = Policy(jss_instance, "Install Adventure")  
	policy.save()
    ```

### 0.2.2 (July 2, 2014)

ADDITIONS:

- ```jss_helper``` now has a promotion feature... Except see CHANGES below.

CHANGES:

- ```XMLEditor.add_object_to_list()``` now returns the element added.
- ```JSSObject.update()``` now accepts a template as a parameter (defaults to None) to replace instance's data from a template.
- Removing ```jss_helper``` to its own project, here: https://github.com/sheagcraig/jss_helper

FIXES:

- ```XMLEditor.add_object_to_list()``` fixed.
- ```PolicyEditor.add_package()``` fixed.
- ```JSSObject.update()``` did not properly update instance's data.

### 0.2.1 (June 25, 2014)

ADDITIONS:

- Adds ```TemplateFromFile``` and ```TemplateFromString``` classes for using external template files and strings.
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
