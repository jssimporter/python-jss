Configuration
=============

Introduction
------------

The JSS class represents a Casper JSS, and provides methods to delegate access to all of the API classes.
Before you can use it, you need to provide a few pieces of connection information.

The JSS class can be hand-configured, supplying all of the information as parameters to the constructor,
but it also can pull information from a preferences file to greatly simplify connecting.
The recommended means for configuring a JSS object in python-jss is to instantiate a JSSPrefs object.

.. warning:: Note that there are a number of additional parameters for a JSS object that must be passed as arguments.
   Please see `Notes: SSL, TLS, SNI, Binary Plists, Etc`_.

Supplying Credentials to the JSSPrefs object
--------------------------------------------

You need a user account with API privileges on your JSS to connect and do anything useful.
It is recommended that you create a user specifically for API access,
with only the privileges required for the task at hand.

For testing purposes, a fully-enabled admin account is fine, but for production, permissions should be finely controlled.

These settings are in the JSS System Settings=>JSS User Accounts & Groups panel.
The preferred method for specifying credentials is to create a preferences file at
``~/Library/Preferences/com.github.sheagcraig.python-jss.plist``.

Required keys include:

- jss_user
- jss_pass
- jss_url (Should be full URL with port, e.g. "https://myjss.domain.org:8443")

These preferences can be set with::

    defaults write ~/Library/Preferences/com.github.sheagcraig.python-jss.plist jss_user <username>
    defaults write ~/Library/Preferences/com.github.sheagcraig.python-jss.plist jss_pass <password>
    defaults write ~/Library/Preferences/com.github.sheagcraig.python-jss.plist jss_url <url>

If you want to work with File Share Distribution Points, or a JDS, to upload packages and scripts,
see the section below on the DistributionPoints class.

If you are working on a non-OS X machine, the JSSPrefs object falls back to using
`plistlib <https://docs.python.org/2.7/library/plistlib.html>`_, although it's up to you to create the proper xml file.

Configure Distribution Points and Distribution Servers
------------------------------------------------------

Casper supports a few different means for handling package and script files:

File Share Distribution Points
    corresponds to AFP and SMB mountable shares.

JDS Instances
    Jamf Distribution Servers, which store files in a database, and are not mountable
    (i.e., must be interacted with via HTML POSTs to the JSS).

Cloud Distribution Point
    which is currently unsupported by python-jss. (Coming as soon as I can set up a testing situation).

Local Repositories
    File shares mounted on your system. They can be on the actual drive, or mounted through some other means,
    as long as you can access them through the file system.

The JSS stores all of the information about your "File Share Distribution Points" in an API object named,
appropriately "DistributionPoints". These repositories contain the packages and scripts that are deployed with policies,
and are normally managed with the Casper Admin application.

JDS types have no corresponding API object, and are usually managed with the web-based "Packages" and "Scripts"
pages of the web interface's "Computer Management" section.

python-jss includes classes to help work with these different repositories.
When you create a JSS object, it includes a DistributionPoints object to delegate, named .distribution_points. e.g.
``my_jss.distribution_points``, to delegate file operations to. While you can always instantiate a DistributionPoints
object (made up of DistributionPoint objects), or even set up individual DP's, it's probably easiest to use
this delegated approach.

For this to be useful, you'll have to include some extra information in your
``com.github.sheagcraig.python-jss.plist`` file.
Add a key **repos**, with an array as its value. The array should contain dictionaries containing connection information
for each DP you wish to include. Here are examples of each type of repo::

    <key>repos</key>
    <array>
        <dict>
            <!-- Auto-configured AFP or SMB repo -->
            <key>name</key>
            <string>Repo1</string>
            <key>password</key>
            <string>xyzzy</string>
        </dict>
        <dict>
            <!-- Explicitly configured SMB repo -->
            <key>name</key>
            <string>Repo2</string>
            <key>URL</key>
            <string>repo.mydomain.org</string>
            <key>domain</key>
            <string>SCHWARTZ</string>
            <key>type</key>
            <string>SMB</string>
            <key>share_name</key>
            <string>Jamf</string>
            <key>username</key>
            <string>DarthHelmet</string>
            <key>password</key>
            <string>abc123</string>
        </dict>
        <dict>
            <!-- Explicitly configured AFP repo -->
            <key>name</key>
            <string>Repo2</string>
            <key>URL</key>
            <string>repo.mydomain.org</string>
            <key>type</key>
            <string>AFP</string>
            <key>share_name</key>
            <string>Jamf</string>
            <key>username</key>
            <string>DarthHelmet</string>
            <key>password</key>
            <string>abc123</string>
        </dict>
        <dict>
            <!-- JDS -->
            <key>type</key>
            <string>JDS</string>
        </dict>
        <dict>
            <!-- CDP -->
            <key>type</key>
            <string>CDP</string>
        </dict>
        <dict>
            <!-- Locally available directory -->
            <key>type</key>
            <string>Local</string>
            <key>mount_point</key>
            <string>/Users/Shared/my_local_repo</string>
            <key>share_name</key>
            <string>LocalRepo</string>
        </dict>
        <dict>
            <!-- AWS S3 via boto -->
            <key>type</key>
            <string>AWS</string>
            <key>aws_access_key_id</key>
            <string>Access Key ID from IAM</string>
            <key>aws_secret_access_key</key>
            <string>Secret key</string>
            <key>bucket</key>
            <string>Bucket Name</string>
        </dict>
    </array>

Notice two alternate forms for defining distribution points. The first uses just a name and a password.
For SMB and AFP shares, the remaining connection information can be pulled from the JSS.
**name** corresponds to the name field on the
JSS Computer Management->File Share Distribution Points->Display Name field.
This is the preferred means for configuring things, as it is resilient to changes at the JSS level.

However, you may also specify the complete set of connection information.
If you only specify **name** and **password**, python-jss will assume you want to auto-configure an AFP or SMB share.
All other DP types must be fully-configured.

At this time, if you are not using the auto-configuration method, the following keys are required:

- AFP
   - name *(optional)*
   - URL
   - type: ``AFP``.
   - port *(optional)*
   - share_name
   - username *(rw user)*
   - password
- SMB
   - name *(optional)*
   - URL
   - domain
   - type: ``SMB``.
   - port *(optional)*
   - share_name
   - username *(rw user)*
   - password
- JDS
   - type: ``JDS``.
- CDP
   - type: ``CDP``.
- LocalRepository
   - type: ``Local``
   - mount_point
   - share_name

Please see the Repository subclass' docstrings for a list of required arguments and information for you using them.

Once this is in place, the JSS object can be used to copy files to the distribution points with the copy methods.
In general, **copy()** should be used, as it will enforce putting pkg and dmg files into Packages,
and everything else into Scripts automatically. There are **copy_pkg()** and **copy_script()** methods too, however.

For mountable DP types, if the DP isn't mounted, the copy operation will mount it automatically.
If it's important to keep the mount from appearing in the GUI, you can use the ``nobrowse=True`` parameter to the mount
methods on the individual DP's. There are **mount()** and **umount()** methods to do this manually.

There are some differences between how the AFP/SMB shares work, and a JDS that you should be familiar with.

First, when you copy a file to an AFP or SMB share, the file just gets copied to the mounted directory.
This does not create a **jss.Package** or **jss.Script** object. You must also use the python-jss Package.new() and
Script.new() to create the objects in the database.

The Packages and Scripts directories must be flat, meaning no subdirectories (although technically, bundle-style
packages are directories, but this is not an issue). When specifying the filename,
the JSS will assume a package is in the Packages directory, and a script in the Scripts directory,
so only specify the basename of the file (i.e. Correct: 'my_package.pkg' Incorrect: 'jamf/Packages/my_package.pkg').

It's not really important which order you do this in, with the only real side effect being that Casper Admin
will report missing files if the Package/Script object has been created before it has been copied to the file shares.

On a JDS, when you **JDS.copy()**, if you don't specify an ``id_`` number as a parameter,
it will assume you want to create a new jss.Package jss.Script object. If, instead, you are trying to upload a file
to correspond to an existing object, you must pass the id number to the ``id_`` parameter.
('id' is a reserved word in Python, so throughout python-jss, I use ``id_``).

The second difference is in the **exists()** method. For AFP/SMB, it is pretty simple to just see if the file is present.
On a JDS, it becomes more complicated. There is no officially documented way to see if a file is present.
So the **exists()** method looks for a jss.Package or jss.Script object with a matching filename and assumes that the
associated file is in the database. Of course, this isn't necessarily true,
especially if you're monkeying around with python-jss, so there's an **exists_using_casper** method that uses the casper
module of python-jss to check the undocumented casper.jxml results for proof of a file's existence and whether it has
synced to all JDS children.

Finally, the mount and umount methods obviously don't apply to JDS'.

JSS "Migration" and Scripts
---------------------------

Casper can be "migrated", meaning all of the scripts previously existing as files on File Share Distribution Points
are migrated into the database. The files are no longer kept, and future scripts will be records in the database.
This also enables the web script editor. python-jss' default behavior is to assume that your JSS has not been migrated,
meaning specifically that Scripts copied to an AFP or SMB distribution point are literally files copied
to those mounted shares.

However, if you use an AFP or SMB distribution point and wish to copy scripts, and you have migrated your JSS,
you need to specify that migration has occurred.

There are two ways to do this:

- When creating a **jss.JSS()** object, specify the parameter ``jss_migrated=True``.
- After creation, toggle the value as needed. eg::

   >>> j = jss.JSS(jssPrefs)
   >>> j.jss_migrated = True




