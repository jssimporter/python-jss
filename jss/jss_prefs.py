#!/usr/bin/env python
# Copyright (C) 2014, 2015 Shea G Craig <shea.craig@da.org>
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


import getpass
import os
import readline   # pylint: disable=unused-import
import subprocess
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError

from .exceptions import (JSSError, JSSGetError, JSSPrefsMissingKeyError,
                         JSSPrefsMissingFileError)
from .jamf_software_server import JSS
from .tools import (is_osx, is_linux, loop_until_valid_response, indent_xml)
try:
    from .contrib import FoundationPlist
except ImportError as err:
    # If using OSX, FoundationPlist will need Foundation/PyObjC
    # available, or it won't import.

    if is_osx():
        print "Warning: Import of FoundationPlist failed:", err
        print "See README for information on this issue."
    import plistlib


class JSSPrefs(object):
    """Object representing JSS credentials and configuration.

    This JSSPrefs object can be used as an argument for a new JSS.
    By default and with no arguments, it uses the preference domain
    "com.github.sheagcraig.python-jss.plist". However, alternate
    configurations can be supplied to the __init__ method to use
    something else.

    If no preference file is found, an interactive configuration
    function will try to help configure python-jss.

    Preference file should include the following keys:
        jss_url: String, full path, including port, to JSS, e.g.
            "https://mycasper.donkey.com:8443".
        jss_user: String, API username to use.
        jss_pass: String, API password.
        verify: (Optional) Boolean for whether to verify the JSS's
            certificate matches the SSL traffic. This certificate must
            be in your keychain. Defaults to True.
        suppress_warnings: (Optional) Boolean for whether to suppress
            the urllib3 warnings likely spamming you if you choose not
            to set verify=False. Enabled by default when verify=False.
        repos: (Optional) A list of file repositories dicts to connect.
        repos dicts:
            Each file-share distribution point requires:
            name: String name of the distribution point. Must match
                the value on the JSS.
            password: String password for the read/write user.

            This form uses the distributionpoints API call to determine
            the remaining information. There is also an explicit form;
            See distribution_points package for more info

            CDP and JDS types require one dict for the master, with
            key:
                type: String, either "CDP" or "JDS".
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
            look for preferences. Defaults base on OS:
                OS X: "~/Library/Preferences/com.github.sheagcraig.python-jss.plist"
                Linux: "~/.com.github.sheagcraig.python-jss.plist"

        Raises:
            JSSError if using an unsupported OS.
        """
        if (preferences_file is not None and not
                os.path.exists(os.path.expanduser(preferences_file))):
            raise JSSPrefsMissingFileError("Preferences file not found!")
        if preferences_file is None:
            plist_name = "com.github.sheagcraig.python-jss.plist"
            if is_osx():
                preferences_file = os.path.join("~", "Library", "Preferences",
                                                plist_name)
            elif is_linux():
                preferences_file = os.path.join("~", "." + plist_name)
            else:
                raise JSSError("Unsupported OS.")

        self.preferences_file = os.path.expanduser(preferences_file)
        if os.path.exists(self.preferences_file):
            self.parse_plist(self.preferences_file)

        else:
            self.configure()
            if not os.path.exists(self.preferences_file):
                raise JSSPrefsMissingFileError("Preferences file not found!")
            else:
                self.__init__()   # pylint: disable=non-parent-init-called

    def parse_plist(self, preferences_file):
        """Try to reset preferences from preference_file."""
        preferences_file = os.path.expanduser(preferences_file)

        # Try to open using FoundationPlist. If it's not available,
        # fall back to plistlib and hope it's not binary encoded.
        try:
            prefs = FoundationPlist.readPlist(preferences_file)
        except NameError:
            try:
                prefs = plistlib.readPlist(preferences_file)
            except ExpatError:
                # If we're on OSX, try to convert using another
                # tool.
                if is_osx():
                    subprocess.call(["plutil", "-convert", "xml1",
                                     preferences_file])
                    prefs = plistlib.readPlist(preferences_file)

        self.preferences_file = preferences_file
        self.user = prefs.get("jss_user")
        self.password = prefs.get("jss_pass")
        self.url = prefs.get("jss_url")
        if not all([self.user, self.password, self.url]):
            raise JSSPrefsMissingKeyError("Please provide all required "
                                          "preferences!")

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
        root = ElementTree.Element("dict")
        print ("It seems like you do not have a preferences file configured. "
               "Please answer the following questions to generate a plist at "
               "%s for use with python-jss." % self.preferences_file)

        self.url = _get_user_input(
            "The complete URL to your JSS, with port (e.g. "
            "'https://mycasperserver.org:8443')\nURL: ", "jss_url", root)

        self.user = _get_user_input("API Username: ", "jss_user", root)

        self.password = _get_user_input("API User's Password: ", "jss_pass",
                                        root, getpass.getpass)

        verify_prompt = ("Do you want to verify that traffic is encrypted by "
                         "a certificate that you trust?: (Y|N) ")
        self.verify = _get_user_input(verify_prompt, "verify", root,
                                      loop_until_valid_response)

        self._handle_repos(root)

        self._write_plist(root)
        print "Preferences created.\n"

    def _handle_repos(self, root):
        """Handle repo configuration."""
        ElementTree.SubElement(root, "key").text = "repos"
        repos_array = ElementTree.SubElement(root, "array")

        # Make a temporary jss object to try to pull repo information.
        jss_server = JSS(url=self.url, user=self.user, password=self.password,
                         ssl_verify=self.verify, suppress_warnings=True)
        print "Fetching distribution point info..."
        try:
            dpts = jss_server.DistributionPoint()
        except JSSGetError:
            print ("Fetching distribution point info failed. If you want to "
                   "configure distribution points, ensure that your API user "
                   "has read permissions for distribution points, and that "
                   "the URL, username, and password are correct.")
            dpts = None

        if dpts:
            print ("There are file share distribution points configured on "
                   "your JSS. Most of the configuration can be automated "
                   "from the information on the JSS, with the exception of "
                   "the password for the R/W user.\n")

            for dpt in dpts:
                repo_dict = ElementTree.SubElement(repos_array, "dict")

                repo_name_key = ElementTree.SubElement(repo_dict, "key")
                repo_name_key.text = "name"
                repo_name_string = ElementTree.SubElement(repo_dict, "string")
                repo_name_string.text = dpt.get("name")

                repo_pass_key = ElementTree.SubElement(repo_dict, "key")
                repo_pass_key.text = "password"
                repo_pass_string = ElementTree.SubElement(repo_dict, "string")
                repo_pass_string.text = getpass.getpass(
                    "Please enter the R/W user's password for distribution "
                    "point: %s: " % dpt.get("name", "<NO NAME CONFIGURED>"))

        _handle_dist_server("JDS", repos_array)
        _handle_dist_server("CDP", repos_array)

    def _write_plist(self, root):
        """Write plist file based on our generated tree."""
        # prettify the XML
        indent_xml(root)

        tree = ElementTree.ElementTree(root)
        with open(self.preferences_file, "w") as prefs_file:
            prefs_file.write(
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
                "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
                "<plist version=\"1.0\">\n")
            tree.write(prefs_file, xml_declaration=False, encoding="utf-8")
            prefs_file.write("</plist>")


def _get_user_input(prompt, key_name, parent, input_func=raw_input):
    """Prompt the user for a value, and assign it to key_name."""
    val = input_func(prompt)
    ElementTree.SubElement(parent, "key").text = key_name
    if isinstance(val, bool):
        string_val = "true" if val else "false"
        ElementTree.SubElement(parent, string_val)
    else:
        ElementTree.SubElement(parent, "string").text = val
    return val


def _handle_dist_server(ds_type, repos_array):
    """Ask user for whether to use a type of dist server."""
    if ds_type not in ("JDS", "CDP"):
        raise ValueError("Must be JDS or CDP")
    prompt = "Does your JSS use a %s? (Y|N): " % ds_type
    result = loop_until_valid_response(prompt)

    if result:
        repo_dict = ElementTree.SubElement(repos_array, "dict")
        repo_name_key = ElementTree.SubElement(repo_dict, "key")
        repo_name_key.text = "type"
        repo_name_string = ElementTree.SubElement(repo_dict, "string")
        repo_name_string.text = ds_type
