#!/usr/bin/env python
# Copyright (C) 2014-2017 Shea G Craig
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""jss_prefs.py

Class for using a plist for storing python-jss preferences, with an
interactive configuration that runs if you have not previously set up
a plist.
"""
from __future__ import print_function

from __future__ import absolute_import
import getpass
import os
import readline   # pylint: disable=unused-import
import subprocess
from xml.parsers.expat import ExpatError

from .exceptions import JSSError, GetError
from .jamf_software_server import JSS
from .tools import is_osx, is_linux, loop_until_valid_response
try:
    from .contrib import FoundationPlist as plistlib
except ImportError:
    # If using OSX, FoundationPlist will need Foundation/PyObjC
    # available, or it won't import.
    import plistlib


PREFS_DEFAULT = "com.github.sheagcraig.python-jss.plist"


class JSSPrefs(object):
    """Object representing JSS credentials and configuration.

    This JSSPrefs object can be used as an argument for a new JSS.
    By default and with no arguments, it uses the preference domain
    "com.github.sheagcraig.python-jss.plist". However, alternate
    configurations can be supplied to the __init__ method to use
    something else.

    If no preference file is found, an interactive configuration
    function will try to help configure python-jss.

    The preference file should include the following keys:

        - **jss_url**: String, full path, including port, to JSS, e.g.
          "https://mycasper.donkey.com:8443".
        - **jss_user**: String, API username to use.
        - **jss_pass**: String, API password.
        - **verify**: *(Optional)* Boolean for whether to verify the JSS's
          certificate matches the SSL traffic. This certificate must
          be in your keychain. Defaults to True.
        - **suppress_warnings**: *(Optional)* Boolean for whether to suppress
          the urllib3 warnings likely spamming you if you choose not
          to set verify=False. Enabled by default when verify=False.
        - **repos:** *(Optional)* A list of file repositories dicts to connect.
            - repos dicts:

                CDP and JDS distribution points require:

                - **name:** String name of the distribution point. Must match
                  the value on the JSS.
                - **password:** String password for the read/write user.

                This form uses the distributionpoints API call to determine
                the remaining information. There is also an explicit form;
                See the distribution_points module for more info

                CDP, JDS and AWS types require one dict for the master, with
                key:

                - **type:** String, "CDP", "JDS" or "AWS".

                AWS distribution points require:

                - **aws_access_key_id:** The access key ID for the user with r/w permission
                    to the jamf bucket
                - **aws_secret_access_key:** The secret key for this user. NOTE: to avoid storing sensitive credentials
                    this can also be read from the environment variable `AWS_SECRET_ACCESS_KEY`.

    """

    def __init__(self, preferences_file=None):
        """Create a preferences object.

        This JSSPrefs object can be used as an argument for a new JSS.
        By default and with no arguments, it uses the preference domain
        "com.github.sheagcraig.python-jss.plist". However, alternate
        configurations can be supplied to the __init__ method to use
        something else.

        If no preferences file is specified, an interactive config
        method will run to help set up python-jss.

        See the JSSPrefs __doc__ for information on supported
        preferences.

        Args:
            preferences_file: String path to an alternate location to
            look for preferences. Defaults based on OS are:
                OS X: "~/Library/Preferences/com.github.sheagcraig.python-jss.plist"
                Linux: "~/.com.github.sheagcraig.python-jss.plist"

        Raises:
            JSSError if using an unsupported OS.
        """
        if preferences_file is None:
            if is_osx():
                preferences_file = os.path.join(
                    "~", "Library", "Preferences", PREFS_DEFAULT)
            elif is_linux():
                preferences_file = os.path.join("~", "." + PREFS_DEFAULT)
            else:
                raise JSSError("Unsupported OS.")

        self.preferences_file = os.path.expanduser(preferences_file)

        if not os.path.exists(self.preferences_file):
            self.configure()

        self._parse_plist()

    def _parse_plist(self):
        """Try to reset preferences from preference_file."""
        # If there's an ExpatError, it's probably because the plist is
        # in binary plist format.
        try:
            prefs = plistlib.readPlist(self.preferences_file)
        except ExpatError:
            # If we're on OSX, try to convert using another tool.
            if is_osx():
                plist = subprocess.check_output(
                    ["plutil", "-convert", "xml1", "-o", "-",
                     preferences_file]).decode()
                prefs = plistlib.readPlistFromString(preferences_file)

        self.user = prefs.get("jss_user")
        self.password = prefs.get("jss_pass")
        self.url = prefs.get("jss_url")
        if not all([self.user, self.password, self.url]):
            raise TypeError("Please provide all required preferences!")

        # Optional file repository array. Defaults to empty list.
        self.repos = []
        for repo in prefs.get("repos", []):
            self.repos.append(dict(repo))

        self.verify = prefs.get("verify", True)
        self.suppress_warnings = prefs.get("suppress_warnings", True)

    def configure(self):
        """Prompt user for config and write to plist

        Uses preferences_file argument from JSSPrefs.__init__ as path
        to write.
        """
        prefs = {}
        print ("It seems like you do not have a preferences file configured. "
               "Please answer the following questions to generate a plist at "
               "%s for use with python-jss." % self.preferences_file)

        prefs["jss_url"] = raw_input(
            "The complete URL to your JSS, with port (e.g. "
            "'https://mycasperserver.org:8443')\nURL: ")

        prefs["jss_user"] = raw_input("API Username: ")
        prefs["jss_pass"] = getpass.getpass("API User's Password: ")
        verify_prompt = ("Do you want to verify that traffic is encrypted by "
                         "a certificate that you trust?: (Y|N) ")
        prefs["verify"] = loop_until_valid_response(verify_prompt)
        prefs["repos"] = self._handle_repos(prefs)

        plistlib.writePlist(prefs, self.preferences_file)
        print("Preferences created.\n")

    def _handle_repos(self, prefs):
        """Handle repo configuration."""
        repos_array = []

        # Make a temporary jss object to try to pull repo information.
        jss_server = JSS(
            url=prefs["jss_url"], user=prefs["jss_user"],
            password=prefs["jss_pass"], ssl_verify=prefs["verify"])
        print("Fetching distribution point info...")
        try:
            dpts = jss_server.DistributionPoint()
        except GetError:
            print (
                "Fetching distribution point info failed. If you want to "
                "configure distribution points, ensure that your API user "
                "has read permissions for distribution points, and that the "
                "URL, username, and password are correct.")
            dpts = None

        if dpts:
            print ("There are file share distribution points configured on "
                   "your JSS. Most of the configuration can be automated "
                   "from the information on the JSS, with the exception of "
                   "the password for the R/W user.\n")

            for dpt in dpts:
                repo_dict = {}
                repo_dict["name"] = dpt.get("name")
                repo_pass_string = getpass.getpass(
                    "Please enter the R/W user's password for distribution "
                    "point: %s: " % dpt.get("name", "<NO NAME CONFIGURED>"))
                repo_dict["password"] = repo_pass_string
                repos_array.append(repo_dict)

        jds = _handle_dist_server("JDS")
        if jds:
            repos_array.append(jds)
        cdp = _handle_dist_server("CDP")
        if cdp:
            repos_array.append(cdp)

        return repos_array


def _handle_dist_server(ds_type):
    """Ask user for whether to use a type of dist server."""
    if ds_type not in ("JDS", "CDP"):
        raise ValueError("Must be JDS or CDP")
    prompt = "Does your JSS use a %s? (Y|N): " % ds_type
    result = loop_until_valid_response(prompt)

    if result:
        return {"type": ds_type}
