This project provides an (at the moment) sparsely implemented, dangerously
unlimited, python wrapper for the Jamf JSS API. Sparesely implemented in the
sense that I have at this time no desire to thoroughly cover all features of
the JSS API, since I don't plan on using them all, and dangerously unlimited in
the sense that you can POST/GET/PUT to objects that don't actually implement
those methods. This, at least, I plan on solving in the near future.

The preferred method for specifying credentials is to create a preferences file at "~/Library/Preferences/org.da.jss_helper.plist".
Required keys include:
jss_user
jss_pass
jss_url (Should be full URL with port, e.g. "https://myjss.domain.org:8443"
and can be set with:
"defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_user <username>"
"defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_password <password>"
"defaults write ~/Library/Preferences/org.da.jss_helper.plist jss_url <url>"

Warning: Due to SSL bugs, requests can fail with an SSL exception:
requests.exceptions.SSLError "error:14094410:SSL routines:SSL3_READ_BYTES:sslv3
alert handshake failure"

This usually isn't a problem for single calls, but when rapidly making multiple
calls, is nearly inevitable. Planning for failure is prudent, and when
anticipating large numbers of api requests, the best solution I have come up
with is to wrap these sorts of situations in a while, with a try/except block
to handle the exception.

Example:

# Import the module
>>> import jss

# Create a JSS object with the preferences object
>>> jss_prefs = jss.JSSPrefs()
>>> j = jss.JSS(jss_prefs)

# Return a list of all computer objects
>>> computers = j.Computer()
>>> computers
[<jss.Computer object at 0x111390c10>, <jss.Computer object at 0x111390c50>, ...<many more in a giant list>


# Objects returned as part of a listing operation only provide id and name information
>>> computers[0]
<jss.Computer object at 0x111390c10>
>>> computers[0].name()
'US820-09'
>>> computers[0].id()
'4'

# To look at the full data, create a new object through the JSS object's interface
>>> computer = j.Computer(4)
>>> computer.pprint()
<computer>
    <general>
        <id>4</id>
        <name>US820-09</name>
		...
		<Tons more info>
</computer>

# Let's create a new Policy object, using a known-valid xml text file

>>> with open('doc/policy_template.xml') as f:
...     policy_data = f.read()
... 
>>> new_policy = j.Policy(policy_data)
Object created with ID: 364

# Let's see our new policy, nicely:

>>> new_policy.pprint()
<policy>
    <general>
        <id>364</id>
        <name>jss python wrapper API test policy</name>
        <enabled>true</enabled>
		...
</policy>

# ...and let's get rid of it.

>>> new_policy.delete()
Success.