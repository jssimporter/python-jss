Notes: SSL, TLS, Binary plists, Etc
===================================

Advanced Arguments for the JSS object
-------------------------------------

The complete list of arguments for the jss can always be seen by dir(jss.JSS) in the interpreter.

The "extra" arguments are:

- **ssl_verify**: *Bool* indicating whether to verify SSL traffic. See below.
- **verbose**: *Bool*. At the moment doesn't do much more than add in HTML responses to actual API calls.
- **jss_migrated**: *Bool*. Indicates whether the JSS has been "migrated".
  This primarily effects whether scripts are copied like files, or posted to the JSS' database.
  For this to work, ``jss_migrated=True`` must be set, and you must have a configured SMB/AFP DP(s).
  See the Configuration section for more info.
- **suppress_warnings**: *Bool*. Defaults to True. Disables urllib3 warnings. Enable if you would like to see!

SSL/TLS Errors
--------------

SSL is a mess in python 2.

If you are having issues with your SSL or TLS setup, there are a few things you may want to experiment with.

First, Jamf is now disabling SSL entirely in versions of Casper greater than 9.61 in favor of TLS.

If you'd prefer to stop verifying SSL traffic, use the **JSS()** parameter ``ssl_verify``, set to False, to disable.

FoundationPlist, binary plists, and Python
------------------------------------------

python-jss should handle all plist operations correctly. However, you may see a warning about FoundationPlist
not importing.

OS X converts plists to binary these days, which will make the standard library plistlib fail,
claiming that the plist is "badly formed." Thus, python-jss includes FoundationPlist. However,
if you have installed python from a non-Apple source (i.e. python.org), FoundationPlist's dependencies will not be met,
and python-jss will fall back to using plistlib.
This will also happen on non-OS X machines, where it should not be a problem,
since they shouldn't be secertly converting preferences to binary when you aren't looking.

To include binary plist support, you will need to ensure that python-jss/FoundationPlist has access
to the PyObjC package, and specifically the Foundation module.
In some circumstances, it can be as easy as adding the path to the Apple-installed PyObjC
to your ``PYTHONPATH``. On my machine::

    export PYTHONPATH=$PYTHONPATH:/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python/PyObjC:/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python

This won't work for Python3.x, and may not work for some setups of 2.x.
You should either try to install PyObjC ``sudo pip install pyobjc``, create a plist file by hand rather than by using
defaults (you could create the file as described above and then ``plutil -convert xml1 plist_filename`` , or just use
the username and password arguments to the JSS constructor and avoid using the JSSPrefs object.
