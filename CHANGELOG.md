# python-jss Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased][unreleased]
## [2.0.0] - 2017-03-19 - Start Choppin'

### Added
- Added `CurlAdapter`, `ResponseAdapter`, and `RequestsAdapter` to wrap curl in
  requests' API. This is primarily to deal with the fact that Apple's shipped
  OpenSSL is extremely out of date (requests uses pyopenssl, which uses the
  out-of-date OpenSSL). Since current recommendations from Jamf are to run the
  Casper server using only TLS1.2, this puts us in a bind. So, by default,
  python-jss will now use curl for networking. Developers seeking the
  advantages of using requests can replace the networking adapter they want to
  use (see `jss.jamf_software_server.JSS`).
- @mosen really stepped up and provided Sphinx documentation! This is a great
  motivator for getting some improved documentation going for this project.
- `JSSObject` and all of its subclasses can now be used as a context manager
  (the python `with` statement). All this does is automatically tries to save
  the object automatically on the way out of the with context.
- Added `Container.__contains__` magic method, which allows you to do things
  like `if some_pkg in some_policy:`. Please note, this will find *any*
  reference to that object contained within. This may not be what you want, for
  example, if a computer is in a group's exclusions list but you want to know
  if it's in the inclusion list. Thankfully, there's a method for that
  (`JSSGroupObject.has_member()`).
- Added `JSSObject` magic methods for equality and hash. This means you can
  test whether two `Computer` objects are the same, for example. You can also
  now use the objects as keys in a dictionary, or other mapping.
- Implemented new endpoints and their corresponding objects:
  `AllowedFileExtension`, `ComputerApplicationUsage`, `ComputerApplication`,
  `ComputerHardwareSoftwareReport`, `ComputerManagement`, `HealthcareListener`,
  `HealthcareListerRule`, `JSONWebTokenConfigurations`,
  `InfrastructureManager`, `MobileDeviceHistory`, `Webhook`.
- Added compression argument to `JSS.pickle_all()` (defaults to `True`) to
  compress pickle output. A lot.
- Tag access through the `.` operator for `JSSObject`s. For example, you can
  now do `computer.configuration_profiles.size.text` to reach all the way down
  the tree to that value.
- All `JSSObject`s have a `tree()` method which will return a nicely indented
  representation of the tag structure of the object. Use it like this: `print
  a_computer_group.tree()`.
- Automatic `match` search detection for object types that support it. Now you
  can do `j.Computer("MacBook*")` instead of `j.Computer("match=MacBook*")`.
  Match searches will _always_ return a QuerySet.
- `JSS.version()` method now returns the server's version (using the jssuser
  endpoint.
- Made the `DistributionPoints` collection class iterable, so if you do need to
  operate on individual DPs within, you don't need to fool around with the
  private collection. (See JSSImporter for an example).
- Added `Script.add_script()` to handle XML escaping and adding a script
  payload to a `Script` object.

### Changed
- Moved the `suppress_warnings` preference out of `JSS` and into the requests
  adapter. The `JSS` initialization will accept that keyword argument to ease
  the (sudden) deprecation, but it just won't do anything. Use the
  `RequestsAdapter.suppress_warnings()` method if you need it.
- Instantiating a `JSS` object will now default to using the `CurlAdapter` for
  networking. Use `JSS.mount_networking_adapter()` to replace it with the
  `RequestsAdapter` and gain things like sessions.
- The requests library is now not a required dependency. You only need it if
  you want to import/use the `RequestsAdapter`.
- Through some metaprogramming shenanigans, jss.JSS is now about 500 lines
  shorter, from dynamically creating all of the object search methods. This
  makes maintenance of this code significantly easier.
- All object search methods _accept_ keyword arguments (instead of a `subset`
  positional argument). Whether the JSS is considered to work with subsetting
  is recorded as a new attribute on the class (`jss.Computer.allowed_kwargs =
  True` for example). This, again, makes it easier to maintain as JAMF adds or
  removes query features. The search methods docstrings all reflect the level
  of (considered) support.
- `JSSObjectList` is now called a `QuerySet`, inspired by Django. The old
  behavior was that the contents were just id/name for each contained object,
  until you used the "retrieve" method. Now all objects contained within are
  full JSSObjects.
- python-jss was using `repr` and `str` too casually. Throughout, class' `repr`
  has been rewritten to provide a very basic marker of the type, and `str` has
  been written to provide the pretty-printing of XML functionality that it had
  previously. In practice, this means that in the interpreter, developers will
  have to `print x` instead of just entering `x` to see what they have.
  However, it also means that simply doing `x` gives easier to read information
  for QuerySets of items without dumping their entire contents to screen (e.g.
  `j.Computer()` results in thousands of lines vomited into your terminal).
- Renamed some internal classes (`JSSContainerObject` -> `Container`,
  `JSSGroupObject` -> `Group`)
- `Container` and all of its subclasses (most types of data from the JSS) now
  use lazy-loading to defer sending a GET method until you actually need the
  data.
- All `Element` objects added to a `JSSObject` will get converted to the
  `PrettyElement` type to enable dot access and pretty printing.
- Renamed all of the request-failure exceptions by dropping the `JSS`:
	- `JSSGetError` -> `GetError`
	- `JSSPutError` -> `PutError`
	- `JSSPostError` -> `PostError`
	- `JSStDeleteError` -> `DeleteError`

### Deprecated
- `JSSObjectList` has been renamed to QuerySet and now inherits from it. While
  it is unlikely that any client code directly references this class, it is
  worth checking for in your code. It will be remmoved entirely in a future
  release. Please update code to use the QuerySet API and signature.

### Removed
- All references to the `jss_migrated` preference has been removed. This is no
  longer an issue with current and future JSS versions.
- Scripts stopped being stored on distribution points with the conclusion
  of version 8, so all distribution point code that did script copying,
  deletion, existence testing, etc, has been removed.
- `JSSObjectList.retrieve()` has been removed as it's no longer needed.
- `JSSObjectList.pickle()` and `from_pickle()`. This code is just cruft; it's
  just about the same amount of work to pickle it on your own.
- `JSSObjectFactory` was removed as it is no longer needed. Client code should
  use `getattr` if it needs to dynamically choose which class to use.
- `JSSDeviceObject` was removed as it was no longer needed. It only added a
  `udid` and `serial_number` method to two subclasses, `Computer` and
  `MobileDevice`. You can access these through `.` notation now:
  `computer.general.serial_number.text`
- As a result of `.` access to subelements, all properties doing the same thing
  have been removed. The vast majority of these were in `Policy` (e.g.
  `a_policy.computers` is now accessed through `a_policy.scope.computers`).
- Removed a bunch of spurious internal-use-only exceptions and used the builtin
  ones that make more sense.

### Fixed
- Made `JSS.user` and `JSS.password` proper properties, that will set the
  attached network adapter appropriately.
- Unicode and bytes usage throughout has been audited and fixed. For the most
  part, developers can pass either to classes or methods and when they need to
  get converted, python-jss will do the right thing.
- Removed pretty-printing injection from `ElementTree`.

## [1.5.0] - 2016-09-12 - Brick House

### Added
- Added optional `action` argument to `Policy.add_package`. Now you can specify that you want to "Cache", "Install Cached", or "Install". Uses "Install" by default. (#48)
- Added `CommandFlush` object (new endpoint in JSS API).
- Added `LogFlush` object (new endpoint in JSS API).
- Added `Patch` object.
- Added `VPPAssignment` object (untested at this time).
- Added `VPPInvitation` object (untested at this time).
- Added `JSSObject.to_string` and `JSSObject.to_file` methods to JSSObject.
- Added `JSSObject.pickle` and `JSSObject.from_pickle` methods.
- Added `JSSObjectList.pickle` and `JSSObjectList.from_pickle`.
- Added category search to `Policy`. (#50 Thanks @jlrgraham)
- Added stub objects. With these new endpoints, the Casper API now allows multiple parameters in a single URL (aside from the `subset` param). As I have limited development time for this project, these endpoints have stub objects added, but no `JSS` helper method, testing, or easy import with `import jss`. The TODO list has an item to add an ability to handle an arbitrary number of keyword arguments to a a GET request to support these new endpoints. Until then, the following objects serve as placeholders:
	- Added `ComputerApplication` object (untested at this time).
	- Added `ComputerApplicationUsage` object.
	- Added `ComputerHardwareSoftwareReport` object (untested at this time).
	- Added `ComputerHistory` object (untested at this time).

### Changed
- `JSSObjectList.retrieve_all` now returns a `JSSObjectList` instead of a list. This is to support being able to pickle/unpickle the contained objects all at once.
- `JSSObject.from_string` encodes input to utf-8 now. ElementTree.fromstring doesn't accept unicode, so anything outside of ascii throws an exception. (#44 Thanks @systemheld!)
- SMB now defaults to port 445 (#51 #53 Thanks @ChrOst)

### Fixed
- Fix file type constants in `distribution_point.py` to satisfy Requests' requirement for string-type headers (#55 thanks @ftiff!)

## [1.4.0] - 2015-09-30 - The Final Countdown

### Added
- Added retrieve method to `JSSListData`, making the retrieval of individual `JSSObjectList` elements more flexible.
- Added some argument type checking.
- Added lots of documentation.
- Re-enabled the ability to create new objects with the JSS convenience methods (e.g. `jss.JSS.Computer`)
- Added and improved the verbose output for HTTP requests.
- Added a __repr__ to `JSSListData` so you can now better interact with them.
- Added the `suppress_warnings` key to the preference domain and `JSSPrefs` object.
- Added an interactive configuration procedure to the JSSPrefs class. If you don't already have a plist file, on instantiation it will prompt your for all configuration information.
- Added a `pre_callback` and `post_callback` parameter to `DistributionPoints.copy`. This allows you to provide some feedback for long copying operations. In the future, if desired, more may be added to long-running methods like `JSSObjectList.retrieve_all()`.
- Added a LocalRepository repo type for paths either local or already mounted. Required connection args are "mount_point", "share_name", and if migrated, "jss".
- Added some public methods to `JSSObjectFactory` if you're into doing some lower-level object searching and creation.

### Changed
- Optimized `JSSObjectList.retrieve_all`.
- Reorganized `JSSObject.save` method. It was very convoluted. Now it reads better, is more error resistant, and should work exactly the same. Specifically, it assumes that if your JSSObject has no ID, then it is a new object (because only the JSS can assign one) and thus needs to PUT. If it _does_ have an ID, then it POSTs it. Potentially this could be an issue where if you retrieved an object, and then wanted to completely replace it with different data, and then tried to save, it would then be missing the ID and would PUT, creating a new object (or fail because of the name conflict); I don't see that as a real issue though.
- Removed `JSSObject.search` since it implements a deprecated Element
  method that wasn't being used anywhere.
- Restored requests method of posting FileUploads. Now uses mimetypes to
  detect file type and uses it in header.
- JAMF fixed D-008180, where the JSS rejected Packages and policies with
  a category of "No Category Assigned", even though that's what the JSS
  supplied in GET requests. This was fixed in JSS v9.7. Therefore,
  python-jss removed its overriden methods `Package.save` and
  `Policy.save`. It's likely this was broader than just Packages and
  Policies, but python-jss hadn't implemented or tested other objects.
- Internal package structure drastically changed to make modules smaller and more manageable.
- Improved the formatting of `JSSObjectList` objects.
- Replaced the Element.__repr__ method with the indenting pretty-printing one that has been in python-jss for awhile now. This allows all non-assigned results from Element subclass methods to pretty-print the XML.
- Removed the recently added `JSSObject.pretty_find` as it's no longer needed.
- Changed the method for creating "new" JSSObjects. Now, generating a blank XML for JSSObjects uses a class attribute `data_keys` to generate the structure. It allows for setting default values.
	- Now, the `__init__` and `_new` methods accept any of the `data_keys` as keyword args to be set during creation.
- Renamed `JSSObject.new` to `JSSObject._new` to discourage client use.

### Fixed
- `JSSObject.set_bool` improved to not have broken string behavior.

## [1.3.0] - 2015-08-19 - Two Men Enter, One Man Leaves

### Added

- Added the subset feature to object queries that support it. For example Computers allow you to do `jss_connection.Computer(None, "basic") for extended list information or `jss_connection.Computer("computer-name", "general&purchasing")` or `jss_connection.Computer("computer-name", ["general", "purchasing"])` for subsection retrieval. This should allow you to speed up big `retrieve_all` runs significantly.
- Added Cloud Distribution Point support. Thanks to @beckf for packet analysis help, and @homebysix for testing. (#22)
- Added `JSSObject.pretty_find`. Pretty prints sub-elements of a JSSObject for use in interactive exploration of the JSS.
- Added option `verify` to `JSSPrefs` and the com.github.sheagcraig.python-jss preference domain. If not specified in the preferences, it will assume `True`.
- Added property to `JSSGroupObject` and subclasses for `is_smart`. Now you can have a regular boolean property and setter for groups.
- Added method `is_member` to `JSSGroupObject`. This allows you to test whether a Computer or MobileDevice object is a member of a group.

### Changed

- New mount technique uses PyObjC rather than subprocess to mount. Thanks to @pudquick for this slick implementation!
	- Solves some Kerberos issues some users were experiencing.
	- For OS X users who are not using the Apple Python, continue to use subprocess to mount.
	- The nobrowse argument to mount is now deprecated, and will do nothing. It will be removed entirely in the future.
	- Verbose prints mount arguments.
- When viewing object data interactively, the `__repr__` now displays simply `*data*` instead of the full binary data for things like icons and app binaries.

### Fixed

- Encode data arguments to `JSS` object's get method.
- Quote data arguments to `JSS` object's get method, since apparently requests doesn't do this for us.

### Removed

- Removed `JSSGroupObject.set_is_smart`. (Replaced with `@property`)

## [1.2.1] - 2015-07-28 - U0001F49A

### Fixed

- Restated cipher list to solve #42 and sheagcraig/jss-autopkg-addon#44. Thanks to @rtrouton for extensive testing patience.

## [1.2.0] - 2015-07-21 - Your Cipher is all Over my Necktie

### Changed

- `jss.ComputerGroup`s that are made with the `new` method now include the `computers` subelement. Strangely, even smart groups include a computers tag. If previously populated with computer objects, it will retain them!
- Removed bundled copy of python requests.
- Using setuptools `setup.py` property `install_requires` to specify dependencies:
	- requests
	- pyasn1
	- ndg-httpsclient
	- Previous two required for cipher change support.
- Updated documentation to describe this requirement for developer (i.e. anyone who does not use the egg or wheel files to install).
- `JSS.base_url` (Get and Set) and `JSS._url` (Read only) are now proper properties.

### Fixed

- Changes the default cipher list for requests/urllib3 to work with recommended changes in JSS >= v9.73.
- `jss.JSS.ssl_verify` is now a computed property and will properly update the requests session if changed after instantiation.
- casper package's `Casper` class did not use the requests session on the JSS object passed to it.
- JSS URL's with a trailing slash will be sanitized to remove that slash upon JSS instantiation or `base_url` update.

## [1.1.0] - 2015-06-10 - Velvet Nachos

### Changed

- `Package.new` now sets the `boot_volume_required` property to `true` by default.

## [1.0.2] - 2015-06-10 - When Doves Cry

### Fixed

- `MobileDeviceGroup` now correctly inherits from `JSSGroupObject`.

## [1.0.1] - 2015-05-28 - Blink Dogs Ate My Homework

### Fixed

- Regression in AFP mount failing on OSX when nobrowse=False. (#38) Thanks for the heads up @galenrichards!

## [1.0.0] - 2015-05-20 - It's a Catapult

### Added

- Adds FileUploads defect number to comments.
- Add `jss.exceptions.JSSError`, and all exceptions now subclass it.
- Add `jss.tools` for misc. tools. (Right now, shorthand os detection functions).
- Add `Policy.add_object_to_limitations` and `Policy.add_object_to_exclusions`. Thanks to @MScottBlake

### Changed

- Basic interface is in place; Calling this 1.0.0 now.
- Begin working on Linux functionality.
	- Preferences plist on Linux should be: `~/.com.github.sheagcraig.python-jss.plist` and should be a non-binary plist.
	- Mount on OS X has different output format than Linux. Thus, regex searches need to be os-specific.
	- Mounting a share is also different.
- As this is largely stable code, set major version to 1.

### Fixed

- Copy methods now make use of the `is_mounted` method for dynamic mount point reconfiguration.
- Typo in policy scope for `building`.
- `ComputerGroup.add_criterion` fails with `AttributeError` with pre-existing computer groups. (#34)

## [0.5.9] - 2015-03-26 - The Pricing is the Message

### Changed

- Passes JSS error messages through when it returns 409: Conflict. Previously thought to be helpful, not passing along the response from the JSS was obfuscating the cause of the conflict. 409 Post and PUT Exceptions will now report back on the (first) error in the XML.


## [0.5.8] - 2015-03-19 - Echo Sierra Xray India

### Fixed

- Safer regexes present unpredictable mount output from tanking `is_mounted` method. (sheagcraig/JSSImporter#35). Thanks for the heads up @rtrouton!


## [0.5.7] - 2015-03-17 - Corned Beef and Cabbage

### Added

- Adds `tlsadapter.py` to subclass `requests.HTTPAdapter` into using `PROTOCOL_TLSv1`. Removes need for manually editing each requests release.
- Adds in extra LDAPServer methods.
    - `search_users()` searches for users.
    - `search_groups()` searches for groups.
    - `is_user_in_group()` tests for group membership by user.

### Fixed

- Mounted distribution points `is_mounted` method now looks for mounted shares by server, and updates mount point dynamically if it is different than configured. This prevents issues when multiple shares have the same name, or when Casper Admin is open and has mounted them already, with different-than-expected share names. Thanks @eahrold!
- Mounted distribution points `__repr__` corrected to make use of `is_mounted`.

### Changed

- Updates requests to 2.5.3
- Mounted repositories' `umount` now has a `forced` argument which defaults to `True`.
- Mounted repositories' `mount_point`, due to the dynamic handling above, is no longer made by concatenating the repo name or "JSS" and share name. Thanks @eahrold!

### Removed

- Remove unused requests import in distribution_points.


## [0.5.6] - 2015-03-06 - Tonkatsu

### Fixed

- Solve regression in JSS >= 9.64 FileUpload API call failing on icon upload with Tomcat Java exception by shelling out to curl.
- Add `list_type` for `jss.Site` so it will properly add itself to other objects. Thanks @MScottBlake. (#29)


## [0.5.5] - 2015-02-02 - Sanpo Shimasu

### Added

- Added `jss.distribution_points.DistributionPoints.delete()` and `jss.distribution_points.MountedRepository.delete()`
- Added `jss.distribution_points.JDS.delete()` and `jss.distribution_points.JDS.delete_with_casperAdminSave()`. The latter is the method used by the Casper Admin app, and is included mostly for reference.

### Fixed

- Automatically configured distribution points (AFP and SMB shares using just name and password) need to pass jss object so `jss_migrated` is handled correctly. (sheagcraig/JSSImporter#19)

### Changed

- Refactored redundent filetype checking to `jss.distribution_points.is_package()` and `jss.distribution_points.is_script()`.


## [0.5.4] - 2015-01-29 - Apex Predator

### Fixed

- `distribution_points.DistributionPoint` did not have `id_` arguments.
- Whitespace cleanup.
- Migrated JSS with AFP or SMB shares now correctly copies scripts to DB instead of fileshare.
- AFP and SMB distribution points should require `share_name` argument.
- Standardized `id_`'s in `distribution_points` to be ints.


## [0.5.3] - 2014-12-09 - Dress For Success

### Added

- Added script testing to `jss.distribution_points.JDS.exists`.
- Added an exception for attempting to upload non-flat packages.
- Added '.ZIP' as a package file type.
- Added `suppress_warnings` parameter to `jss.JSS` objects to disable urllib3 warnings. Use at your own risk. (sheagcraig/jss-autopkg-addon#18)

### Fixed

- Non-flat packages cannot be uploaded to JDS'. Now there is a warning message and documentation. (#20)
- If you haven't configured any DP's through the `repo_prefs` parameter to the `JSS`, we shouldn't attempt `DistributionPoints.retrieve_all()`. Reordered slightly to avoid problems. (#21)
	- No need (unnecessary work)
	- Your API user may not have permissions to do so! Thanks @arubdesu

### Changed

- Tests updated.
- Moved all exceptions to their own module.


## [0.5.2] - 2014-12-05 - Brass Monkey

### Fixed

- JDS copy methods were not utilizing the same session as everything else and did not honor SSL settings. Corrected. (#18)

### Changed

- Started working on the nosetests again. This doesn't directly affect users; however, it should help me prevent regressions and should help automate testing things across a variety of different JSS/DistributionPoint types.


## [0.5.1] - 2014-12-04 - Gold Soundz

### Fixed

- Finally implementing @ocoda suggestions for solving the disabling of SSL in >= JSS  v9.61. (sheagcraig/jss-autopkg-addon#9, #16) #Further behind-the-scenes-measures are being investigated to streamline this edit for the future.
- Fixed `list_type` for `ActivationCode` regression.
- Fixed DistributionPoints __init__ mistake.

### Changed

- Configuration for a JDS has changed. Now it only requires key: type, value: JDS. See the [wiki](https://github.com/sheagcraig/python-jss/wiki/Configuration) for complete examples.
	- Old configuration was misleading and/or redundent. Uploading to a JDS actually involves POSTing to the *JSS*, using the JSS' URL, and a correctly privileged API user, NOT the JDS' URL or WebDAV R/W accounts.
- Implemented missing API objects:
	- BYOProfile
	- ComputerConfiguration
	- IBeacon. PEP8 wins over Apple 'iFoolishness' for naming.
	- MacApplication
	- VPPAccount


## [0.4.4] - 2014-12-03 - Welcome to the Terrordome

### Fixed

- Included submodules should now properly handle TLS for JSS v9.6.1 or later. (sheagcraig/jss-autopkg-addon#9, #16)
- `JSSObject.save()` has been reworked to safely handle all permutations of PUT and POST abilities on objects. For example, `ComputerInvitations` can only POST, not PUT, and did not work correctly.
- All tests in the test suite are passing again. This is of course set up to work on our testing server only.

### Changed

- `JSS` objects will now have a `DistributionPoint` property `JSS.distribution_points` even if no repos are configured. This makes it easier to add in after the fact.
- Updated [requests](http://docs.python-requests.org/en/latest/) to 2.5.0.
- `JSSObject.save()` now has better error reporting.

### Known issues

- See #15. Objects that can potentially have a category, but have none, fail to save. This is almost certainly related to how the JSS interprets the changed value of nil categories (was "Unknown", now "No category assigned"). This has been solved by overriding the `save` method on Policies and Packages until they fix it. Please let me know if you come across others.


## [0.4.3] - 2014-12-01 - Anti-Corruption Sauce

### Fixed

- JDS repos can now upload packages and scripts. Thanks to @beckf for sorting out the dark magic in the packets. (#5)

### Changed

- Identified eBooks as file type 1 and in mobile apps as file type 2 for dbfileupload parameters. This may not be the appropriate place to house these functions, but for those who need it, the JDS._copy() method can now upload eBooks and mobile apps. Please feel free to experiment and clue me in to how to make it work better.
- Research also showed that there are two viable methods for uploading to a JDS. We will stick with the existing method for the time being.


## [0.4.2] - 2014-11-25 - Eyebrow Floss

I did a quick update to include an egg installer on pypi.org. This was needed to support the jss-autopkg-addon installer.

### Changed

- AFP and SMB shares' URL variable should not include a prefixed protocol. Now, python-jss removes any preceding afp:// or smb:// from URL preferences just to be safe. Thanks @eahrold. (#13)

### Fixed

- Repos input variables `port` and `domain` were incorrectly pulled from preferences. This has been corrected. Thanks @eahrold. (sheagcraig/jss-autopkg-addon#11)


## [0.4.1] - 2014-11-25 - Postpartum Fixapalooza

### Changed

- Updates bundled Requests to 2.4.3.
- Mounted repositories now use the force flag to unmount. If this troubles anyone, let me know and I'll make it an option. (#10)

### Fixed

- AFP and SMB file shares did not properly escape password characters. Thanks @eahrold for the fix. (#4)
- AFP shares were defaulting to the incorrect port (139). Now defaults to 548. Thanks @eahrold again! (#8)
- Requests module not properly referenced in jss.py and distribution_points.py. Big props to @eahrold. (#7)
- SSLv3 support was dropped in JSS v9.61 to avoid the Poodle attack. Thanks to @ocoda for a solution while we waited for urllib3 (part of requests) to update to solve this problem. (#6)
- Explicitly configured AFP and SMB sharepoints, despite the documentation, needed a `name`. This is now properly set as optional. If left out, a generic name with an incremented numeric suffix will be used.

### Known issues

- JDS distribution points can upload scripts and packages, but they are getting corrupted with HTML multipart boundaries because the requests are not being made quite right. This should be solved soon.


## [0.4] - 2014-11-02 - Mayonnaise-Olive Parfait

### Added

- Adds class `casper`. This class pulls the information returned from POSTing to the undocumented casper.jxml. At some point I would like this to allow for automatic configuration of all repository information (provided an authentication by a privileged user). However, due to its undocumented nature, I don't want to rely on it until I can get some confirmation from JAMF that this is 'OK'.
- Adds class `JDS` to module `distribution_points`. (#1)
	- Can copy packages/DMG's.
	- Can copy scripts, although it is currently broken.
		- Scripts include HTML form boundaries... Working on this.
	- Has a limited .exists() method.
	- Has a more thorough .exists_with_casper() method that uses the undocumented casper.jxml/casper-module.
- class `DistributionPoints` now adds `JDS` type DP's.
- `DistributionPoints` now have helper methods to add and remove a `DistributionPoint`.

### Known issues

- JDS distribution points can upload scripts and packages, but they are getting corrupted with HTML multipart boundaries because the requests are not being made quite right. This should be solved soon.

### Changed

- `DistributionPoints.__repr__` factored into `DistributionPoint` and children.
- New option to fully declare distribution point connection information in the preference file or at JSS or DistributionPoints instantiation time.
	- Shares will now only be included if they are defined in the list of `repos`. (Previously, it would try to match all DP's from .distributionpoints to a config option).
	- AFP or SMB shares declared in the previous style, with just a `name` and `password` will still get the rest of the information from the server.
	- You may now specify these connection properties explictly.
	- JDS' must be configured with explicit properties.
	- See docstrings for the different types of DistributionPoint for required keys.
- DistributionPoint subclasses will now let you know what config information you left out.
- DistributionPoints and DistributionPoint subclasses now have an optional argument id_ for supporting JDS copy methods.
	- Ignored by non-JDS DP's.
	- Can be used to copy a package/script to an existing package object rather than creating a new one (the default, of -1 makes a new object).
- Moved documentation from README to wiki.


## [0.3.11] - 2014-10-08 - Offal Sliders 2

### Fixed

- Except I screwed it up. *Now* `FileUploads` is squared away.


## [0.3.10] - 2014-10-08 - Offal Sliders

### Fixed

- `FileUploads` were sent using a non-session request because I couldn't get it working with a session. I got it working with a session.
- `FileUploads` non-session request lacked the verify parameter, thus, even if SSL verification was turned off in the JSS object, it still tried to verify SSL.


## [0.3.9] - 2014-09-03 - Chorizo

### Fixed

- Fix resource name when using `FileUpload`. Previous behavior was to give resource the full upload path as a name. Switched to just os.path.basename()

### Added

- Add method `DistributionPoints.exists()` for testing for the existence of a script/pkg across all distribution points.


## [0.3.7] - 2014-08-29 - Hot Dog Sundae

### Added

- Add module `distribution_points`. Provides:
  - `DistributionPoints` to handle copying packages and scripts across all configured repositories.
	- Distribution points are automatically configured (except for password until I can figure out the hashing) based on your JSS's data.
	- copy copies a file to the directory indicated by the file extension (.pkg, .dmg to Packages, everything else to Scripts) of all distribution points.
	- copy_pkg copies a .pkg or .dmg to the Packages directory of all distribution points.
	- copy_script copies a script to the Scripts directory of all distribution points.
	- Distribution points are mounted prior to copy operations if they aren't already.
  - `AFPRepository`, `SMBRepository`, `HTTPRepository`, `HTTPSRepository`, and `JDSRepository`. (Only AFP and SMB implemented currently-HTTP(S) and JDS coming soon.)
	- mount (Has option to mount -o nobrowse, so disk doesn't appear in GUI)
	- umount

### Changed

- Add handling of `repos` preference key in com.github.sheagcraig.python-jss.plist. See README.
- JSS objects now have a DistributionPoint property included at init time, so you don't need to instantiate one. Just delegate!


## [0.3.5] - 2014-08-21 - Retcon Cheese Sauce

### Changed

- Implemented FileUpload. They are kind of unique in the way they operate, so check the docstring for more info.


## [0.3.4] - 2014-08-08

### Notes

- The interface will stay the same now. Only new features and fixes from here on out.

### Added

- Add `__version__` property to module. Use for version checking if needed.


## [0.3.3] - 2014-07-31

### Changed

- Reorganized `JSSObject.save()` logic to try to update first. Trying to create a new object first with existing objects results in a name conflict exception, which you then have to catch. But when you DO have a name conflict, you really would like to know. This saves the need to wrap save calls in a try/except for updating existing objects. E.g. batch_scope verb of jss_helper.


## [0.3.2] - 2014-07-29

### Fixed

- Fixed error where pypi packages did not include the cacert.pem file included with requests.


## [0.3.1] - 2014-07-17

### Changed

- `JSS._error_handler()` now adds a `status_code` attribute to exceptions.

### Fixed

- `JSSObject.save()` was confusing. If you created a new object with
  `JSSObject()` that conflicted with an existing object on the JSS, the save
  would fail with a `JSSPutError`. Now we check for conflicts and instead return
  a `JSSPostError` with a more helpful error message.
- I mistakenly listed the preference key as `jss_password` in the README. Now the code and README agree: `jss_pass` is the correct key.


## [0.3] - 2014-07-03

### Changed

- Renamed `JSSObject.update()` to `JSSObject.save()` to represent its added responsibilities (it can now post new objects as well)
- Creating new objects has changed as a result
  - To create an object now, use the class constructor with the string argument "name", configure as before, and then save().
  - i.e.
    ```
	policy = Policy(jss_instance, "Install Adventure")
	policy.save()
    ```

### Removed

- Removed Templates and XMLEditor classes.
  - All editor behaviors / methods moved into appropriate JSSObject subclasses.
  - For example, Policies gain all of their previously inherited PolicyEditor methods.
  - Templates' __init__ methods have become the new() method on objects.
  - Only implemented the existing set of: Category, ComputerGroup, MobileDeviceGroup, Package, Policy
  - SearchCriteria remains an object, although no longer inherits from a template.


## [0.2.2] - 2014-07-02

### Added

- `jss_helper` now has a promotion feature... Except see CHANGES below.

### Changed

- `XMLEditor.add_object_to_list()` now returns the element added.
- `JSSObject.update()` now accepts a template as a parameter (defaults to None) to replace instance's data from a template.

### Fixed

- `XMLEditor.add_object_to_list()` fixed.
- `PolicyEditor.add_package()` fixed.
- `JSSObject.update()` did not properly update instance's data.

### Removed

- Removing `jss_helper` to its own project, here: https://github.com/sheagcraig/jss_helper


## [0.2.1] - 2014-06-25

### Added

- Adds `TemplateFromFile` and `TemplateFromString` classes for using external template files and strings.
- Adds batch_scope feature to jss_helper.
- Added requests and FoundationPlist to contrib folder of package. No longer need separate installation.

### Changed

- Should now "just work" even if PyObjC/Foundation are not available. (See end of README).
- Renamed the default preferences file to reference github.

### Fixed

- Should not see SSL handshake errors now. JSS object now has a requests.Session object which prevents having to continually renegotiate. Bonus: It seems to be significantly faster as a result.

### Known issues

- Requests does not automatically handle SNI out of the box for python 2.x. README describes necessary steps to work around this if needed. Thanks to Greg Neagle for pointing this out.


## [0.2.0] - 2014-06-18

### Added

- Initial release.


[unreleased]: https://github.com/sheagcraig/python-jss/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/sheagcraig/python-jss/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/sheagcraig/python-jss/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/sheagcraig/python-jss/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/sheagcraig/python-jss/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/sheagcraig/python-jss/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/sheagcraig/python-jss/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/sheagcraig/python-jss/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/sheagcraig/python-jss/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/sheagcraig/python-jss/compare/v0.5.9...v1.0.0
[0.5.9]: https://github.com/sheagcraig/python-jss/compare/v0.5.8...v0.5.9
[0.5.8]: https://github.com/sheagcraig/python-jss/compare/v0.5.7...v0.5.8
[0.5.7]: https://github.com/sheagcraig/python-jss/compare/v0.5.6...v0.5.7
[0.5.6]: https://github.com/sheagcraig/python-jss/compare/v0.5.5...v0.5.6
[0.5.5]: https://github.com/sheagcraig/python-jss/compare/v0.5.4...v0.5.5
[0.5.4]: https://github.com/sheagcraig/python-jss/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/sheagcraig/python-jss/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/sheagcraig/python-jss/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/sheagcraig/python-jss/compare/v0.4.4...v0.5.1
[0.4.4]: https://github.com/sheagcraig/python-jss/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/sheagcraig/python-jss/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/sheagcraig/python-jss/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/sheagcraig/python-jss/compare/v0.4...v0.4.1
[0.4]: https://github.com/sheagcraig/python-jss/compare/v0.3.11...v0.4
[0.3.11]: https://github.com/sheagcraig/python-jss/compare/v0.3.10...v0.3.11
[0.3.10]: https://github.com/sheagcraig/python-jss/compare/v0.3.9...v0.3.10
[0.3.9]: https://github.com/sheagcraig/python-jss/compare/v0.3.7...v0.3.9
[0.3.7]: https://github.com/sheagcraig/python-jss/compare/v0.3.5...v0.3.7
[0.3.5]: https://github.com/sheagcraig/python-jss/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/sheagcraig/python-jss/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/sheagcraig/python-jss/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/sheagcraig/python-jss/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/sheagcraig/python-jss/compare/v0.3...v0.3.1
[0.3]: https://github.com/sheagcraig/python-jss/compare/v0.2.2...v0.3
[0.2.2]: https://github.com/sheagcraig/python-jss/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/sheagcraig/python-jss/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/sheagcraig/python-jss/compare/v0.0.7...v0.2.0
