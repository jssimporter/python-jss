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
"""jss.py

Classes representing a JSS, and its available API calls, represented
as JSSObjects.
"""


import copy
import os
import re
import subprocess
from urllib import quote
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError

import requests

from . import distribution_points
from .exceptions import (
    JSSPrefsMissingFileError, JSSPrefsMissingKeyError, JSSGetError,
    JSSPutError, JSSPostError, JSSDeleteError, JSSMethodNotAllowedError,
    JSSUnsupportedSearchMethodError, JSSFileUploadParameterError)
from .jssobject import *
from .tlsadapter import TLSAdapter
from .tools import is_osx, is_linux, convert_response_to_text

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

    Preference file should include the following keys:
        jss_url: String, full path, including port, to JSS, e.g.
            "https://mycasper.donkey.com:8443".
        jss_user: String, API username to use.
        jss_pass: String, API password.
        verify: (Optional) Boolean for whether to verify the JSS's
            certificate matches the SSL traffic. This certificate must
            be in your keychain. Defaults to True.
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

        See the JSSPrefs __doc__ for information on supported
        preferences.

        Args:
            preferences_file: String path to an alternate location to
                look for preferences.

        Raises:
            JSSError if using an unsupported OS.
        """
        if preferences_file is None:
            plist_name = "com.github.sheagcraig.python-jss.plist"
            if is_osx():
                preferences_file = os.path.join("~", "Library", "Preferences",
                                                plist_name)
            elif is_linux():
                preferences_file = os.path.join("~", "." + plist_name)
            else:
                raise JSSError("Unsupported OS.")

        preferences_file = os.path.expanduser(preferences_file)
        if os.path.exists(preferences_file):
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
                        subprocess.call(
                            ["plutil", "-convert", "xml1", preferences_file])
                        prefs = plistlib.readPlist(preferences_file)
            try:
                self.user = prefs["jss_user"]
                self.password = prefs["jss_pass"]
                self.url = prefs["jss_url"]
            except KeyError:
                raise JSSPrefsMissingKeyError("Please provide all required "
                                              "preferences!")

            # Optional file repository array. Defaults to empty list.
            self.repos = []
            for repo in prefs.get("repos", []):
                self.repos.append(dict(repo))

            self.verify = prefs.get("verify", True)

        else:
            raise JSSPrefsMissingFileError("Preferences file not found!")


class JSS(object):
    """Represents a JAMF Software Server, with object search methods.

    Attributes:
        base_url: String, full URL to the JSS, with port.
        user: String API username.
        password: String API password for user.
        repo_prefs: List of dicts of repository configuration data.
        verbose: Boolean whether to include extra output.
        jss_migrated: Boolean whether JSS has had scripts "migrated".
            Used to determine whether to upload scripts in Script
            object XML or as files to the distribution points.
        session: Requests session used to make all HTTP requests.
        ssl_verify: Boolean whether to verify SSL traffic from the JSS
            is genuine.
        factory: JSSObjectFactory object for building JSSObjects.
        distribution_points: DistributionPoints
    """

    def __init__(self, jss_prefs=None, url=None, user=None, password=None,
                 repo_prefs=None, ssl_verify=True, verbose=False,
                 jss_migrated=False, suppress_warnings=False):
        """Setup a JSS for making API requests.

        Provide either a JSSPrefs object OR specify url, user, and
        password to init. Other parameters are optional.

        Args:
            jss_prefs:  A JSSPrefs object.
            url: String, full URL to a JSS, with port.
            user: API Username.
            password: API Password.

            repo_prefs: A list of dicts with repository names and
                passwords.
            repos: (Optional) List of file repositories dicts to
                    connect.
                repo dicts:
                    Each file-share distribution point requires:
                        name: String name of the distribution point.
                            Must match the value on the JSS.
                        password: String password for the read/write
                            user.

                    This form uses the distributionpoints API call to
                    determine the remaining information. There is also
                    an explicit form; See distribution_points package
                    for more info

                    CDP and JDS types require one dict for the master,
                    with key:
                        type: String, either "CDP" or "JDS".

            ssl_verify: Boolean whether to verify SSL traffic from the
                JSS is genuine.
            verbose: Boolean whether to include extra output.
            jss_migrated: Boolean whether JSS has had scripts
                "migrated". Used to determine whether to upload scripts
                in Script object XML or as files to the distribution
                points.
            suppress_warnings: Turns off the urllib3 warnings. Remember,
                these warnings are there for a reason! Use at your own
                risk.
        """
        if jss_prefs is not None:
            url = jss_prefs.url
            user = jss_prefs.user
            password = jss_prefs.password
            repo_prefs = jss_prefs.repos
            ssl_verify = jss_prefs.verify

        if suppress_warnings:
            requests.packages.urllib3.disable_warnings()

        self.base_url = url
        self.user = user
        self.password = password
        self.repo_prefs = repo_prefs if repo_prefs else []
        self.verbose = verbose
        self.jss_migrated = jss_migrated
        self.session = requests.Session()
        self.session.auth = (self.user, self.password)
        self.ssl_verify = ssl_verify

        # For some objects the JSS tries to return JSON, so we explictly
        # request XML.

        headers = {"content-type": "text/xml", "Accept": "application/xml"}
        self.session.headers.update(headers)

        # Add a TransportAdapter to force TLS, since JSS no longer
        # accepts SSLv23, which is the default.

        self.session.mount(self.base_url, TLSAdapter())

        self.factory = JSSObjectFactory(self)
        self.distribution_points = distribution_points.DistributionPoints(self)

    def _error_handler(self, exception_cls, response):
        """Handle HTTP errors by formatting into strings."""
        # Responses are sent as html. Split on the newlines and give us
        # the <p> text back.
        error = convert_response_to_text(response)
        exception = exception_cls("Response Code: %s\tResponse: %s"
                                  % (response.status_code, error))
        exception.status_code = response.status_code
        raise exception

    @property
    def _url(self):
        """The URL to the Casper JSS API endpoints. Get only."""
        return "%s/%s" % (self.base_url, "JSSResource")

    @property
    def base_url(self):
        """The URL to the Casper JSS, including port if needed."""
        return self._base_url

    @base_url.setter
    def base_url(self, url):
        """The URL to the Casper JSS, including port if needed."""
        # Remove the frequently included yet incorrect trailing slash.
        self._base_url = url.rstrip("/")

    @property
    def ssl_verify(self):
        """Boolean value for whether to verify SSL traffic is valid."""
        return self.session.verify

    @ssl_verify.setter
    def ssl_verify(self, value):
        """Boolean value for whether to verify SSL traffic is valid.

        Args:
            value: Boolean.
        """
        self.session.verify = value

    def get(self, url_path):
        """GET a url, handle errors, and return an etree.

        In general, it is better to use a higher level interface for
        API requests, like the search methods on this class, or the
        JSSObjects themselves.

        Args:
            url_path: String API endpoint path to GET (e.g. "/packages")

        Returns:
            ElementTree.Element for the XML returned from the JSS.

        Raises:
            JSSGetError if provided url_path has a >= 400 response, for
            example, if an object queried for does not exist (404). Will
            also raise JSSGetError for bad XML.

            This behavior will change in the future for 404/Not Found
            to returning None.
        """
        request_url = "%s%s" % (self._url, quote(url_path.encode("utf_8")))
        response = self.session.get(request_url)

        if response.status_code == 200 and self.verbose:
            print "GET %s: Success." % request_url
        elif response.status_code >= 400:
            self._error_handler(JSSGetError, response)

        # JSS returns xml encoded in utf-8
        jss_results = response.text.encode("utf-8")
        try:
            xmldata = ElementTree.fromstring(jss_results)
        except ElementTree.ParseError:
            raise JSSGetError("Error Parsing XML:\n%s" % jss_results)

        return xmldata

    def post(self, obj_class, url_path, data):
        """POST an object to the JSS. For creating new objects only.

        The data argument is POSTed to the JSS, which, upon success,
        returns the complete XML for the new object. This data is used
        to get the ID of the new object, and, via the
        JSSObjectFactory, GET that ID to instantiate a new JSSObject of
        class obj_class.

        This allows incomplete (but valid) XML for an object to be used
        to create a new object, with the JSS filling in the remaining
        data. Also, only the JSS may specify things like ID, so this
        method retrieves those pieces of data.

        In general, it is better to use a higher level interface for
        creating new objects, namely, creating a JSSObject subclass and
        then using its save method.

        Args:
            obj_class: JSSObject subclass to create from POST.
            url_path: String API endpoint path to POST (e.g.
                "/packages/id/0")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class.

        Returns:
            An object of class obj_class, representing a newly created
            object on the JSS. The data is what has been returned after
            it has been parsed by the JSS and added to the database.

        Raises:
            JSSPostError if provided url_path has a >= 400 response.
        """
        # The JSS expects a post to ID 0 to create an object

        request_url = "%s%s" % (self._url, url_path)
        data = ElementTree.tostring(data)
        response = self.session.post(request_url, data=data)

        if response.status_code == 201 and self.verbose:
            print "POST %s: Success" % request_url
        elif response.status_code >= 400:
            self._error_handler(JSSPostError, response)

        # Get the ID of the new object. JSS returns xml encoded in utf-8

        jss_results = response.text.encode("utf-8")
        id_ = int(re.search(r"<id>([0-9]+)</id>", jss_results).group(1))

        return self.factory.get_object(obj_class, id_)

    def put(self, url_path, data):
        """Update an existing object on the JSS.

        In general, it is better to use a higher level interface for
        updating objects, namely, making changes to a JSSObject subclass
        and then using its save method.

        Args:
            url_path: String API endpoint path to PUT, with ID (e.g.
                "/packages/id/<object ID>")
            data: xml.etree.ElementTree.Element with valid XML for the
                desired obj_class.
        Raises:
            JSSPutError if provided url_path has a >= 400 response.
        """
        request_url = "%s%s" % (self._url, url_path)
        data = ElementTree.tostring(data)
        response = self.session.put(request_url, data)

        if response.status_code == 201 and self.verbose:
            print "PUT %s: Success." % request_url
        elif response.status_code >= 400:
            self._error_handler(JSSPutError, response)

    def delete(self, url_path):
        """Delete an object from the JSS.

        In general, it is better to use a higher level interface for
        deleting objects, namely, using a JSSObject's delete method.

        Args:
            url_path: String API endpoint path to DEL, with ID (e.g.
                "/packages/id/<object ID>")

        Raises:
            JSSDeleteError if provided url_path has a >= 400 response.
        """
        request_url = "%s%s" % (self._url, url_path)
        response = self.session.delete(request_url)

        if response.status_code == 200 and self.verbose:
            print "DEL %s: Success." % request_url
        elif response.status_code >= 400:
            self._error_handler(JSSDeleteError, response)

    # Convenience methods for all JSSObject types ######################

    # Define a docstring to add with a decorator. Why? To avoid having
    # the identical docstring repeat for each object type!

    def _docstring_parameter(obj_type, subset=False):
        """Decorator for adding _docstring to repetitive methods."""
        docstring = (
            "Flexibly search the JSS for objects of type {}.\n\n\tArgs:\n\t\t"
            "Data: Allows different types to conduct different types of "
            "searches. Argument of type:\n\t\t\tNone (or Provide no argument) "
            "to search for all objects.\n\t\t\tInt to search for an object by "
            "ID.\n\t\t\tString to search for an object by name.\n\t\t\t"
            "xml.etree.ElementTree.Element to create a new object from the "
            "Element's data.{}\n\n\tReturns:\n\t\tJSSObjectList for empty "
            "data arguments.\n\t\tReturns an object of type {} for searches "
            "and new objects.\n\t\t(FUTURE) Will return None if nothing is "
            "found that match the search criteria.\n\n\tRaises:\n\t\t"
            "JSSGetError for nonexistent objects.")

        if subset:
            subset_string = (
                "\n\t\tsubset: A list of XML subelement tags to request\n"
                "\t\t\t(e.g. ['general', 'purchasing']), OR an '&' \n\t\t\t"
                "delimited string (e.g. 'general&purchasing').")
        else:
            subset_string = ""

        def dec(obj):
            class_name = str(obj_type)[:-2].rsplit(".")[-1]
            updated_docstring = docstring.format(class_name, subset_string,
                                                 class_name)
            obj.__doc__ = obj.__doc__.format(
                dynamic_docstring=updated_docstring)
            return obj
        return dec

    @_docstring_parameter(Account)
    def Account(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Account, data)

    @_docstring_parameter(AccountGroup)
    def AccountGroup(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(AccountGroup, data)

    @_docstring_parameter(AdvancedComputerSearch)
    def AdvancedComputerSearch(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(AdvancedComputerSearch, data)

    @_docstring_parameter(AdvancedMobileDeviceSearch)
    def AdvancedMobileDeviceSearch(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(AdvancedMobileDeviceSearch, data)

    @_docstring_parameter(AdvancedUserSearch)
    def AdvancedUserSearch(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(AdvancedUserSearch, data)

    @_docstring_parameter(ActivationCode)
    def ActivationCode(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ActivationCode, data)

    @_docstring_parameter(Building)
    def Building(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Building, data)

    @_docstring_parameter(BYOProfile)
    def BYOProfile(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(BYOProfile, data)

    @_docstring_parameter(Category)
    def Category(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Category, data)

    @_docstring_parameter(Class)
    def Class(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Class, data)

    @_docstring_parameter(Computer, subset=True)
    def Computer(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Computer, data, subset)

    @_docstring_parameter(ComputerCheckIn)
    def ComputerCheckIn(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerCheckIn, data)

    @_docstring_parameter(ComputerCommand)
    def ComputerCommand(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerCommand, data)

    @_docstring_parameter(ComputerConfiguration)
    def ComputerConfiguration(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerConfiguration, data)

    @_docstring_parameter(ComputerExtensionAttribute)
    def ComputerExtensionAttribute(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerExtensionAttribute, data)

    @_docstring_parameter(ComputerGroup)
    def ComputerGroup(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerGroup, data)

    @_docstring_parameter(ComputerInventoryCollection)
    def ComputerInventoryCollection(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerInventoryCollection, data)

    @_docstring_parameter(ComputerInvitation)
    def ComputerInvitation(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerInvitation, data)

    @_docstring_parameter(ComputerReport)
    def ComputerReport(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ComputerReport, data)

    @_docstring_parameter(Department)
    def Department(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Department, data)

    @_docstring_parameter(DirectoryBinding)
    def DirectoryBinding(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(DirectoryBinding, data)

    @_docstring_parameter(DiskEncryptionConfiguration)
    def DiskEncryptionConfiguration(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(DiskEncryptionConfiguration, data)

    @_docstring_parameter(DistributionPoint)
    def DistributionPoint(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(DistributionPoint, data)

    @_docstring_parameter(DockItem)
    def DockItem(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(DockItem, data)

    @_docstring_parameter(EBook, subset=True)
    def EBook(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(EBook, data, subset)

    # FileUploads' only function is to upload, so a method here is not
    # provided.

    @_docstring_parameter(GSXConnection)
    def GSXConnection(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(GSXConnection, data)

    @_docstring_parameter(IBeacon)
    def IBeacon(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(IBeacon, data)

    @_docstring_parameter(JSSUser)
    def JSSUser(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(JSSUser, data)

    @_docstring_parameter(LDAPServer)
    def LDAPServer(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(LDAPServer, data)

    @_docstring_parameter(LicensedSoftware)
    def LicensedSoftware(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(LicensedSoftware, data)

    @_docstring_parameter(MacApplication, subset=True)
    def MacApplication(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MacApplication, data, subset)

    @_docstring_parameter(ManagedPreferenceProfile, subset=True)
    def ManagedPreferenceProfile(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(ManagedPreferenceProfile, data, subset)

    @_docstring_parameter(MobileDevice, subset=True)
    def MobileDevice(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDevice, data, subset)

    @_docstring_parameter(MobileDeviceApplication, subset=True)
    def MobileDeviceApplication(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceApplication, data, subset)

    @_docstring_parameter(MobileDeviceCommand)
    def MobileDeviceCommand(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceCommand, data)

    @_docstring_parameter(MobileDeviceConfigurationProfile, subset=True)
    def MobileDeviceConfigurationProfile(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceConfigurationProfile, data,
                                       subset)

    @_docstring_parameter(MobileDeviceEnrollmentProfile, subset=True)
    def MobileDeviceEnrollmentProfile(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceEnrollmentProfile, data,
                                       subset)

    @_docstring_parameter(MobileDeviceExtensionAttribute)
    def MobileDeviceExtensionAttribute(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceExtensionAttribute, data)

    @_docstring_parameter(MobileDeviceInvitation)
    def MobileDeviceInvitation(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceInvitation, data)

    @_docstring_parameter(MobileDeviceGroup)
    def MobileDeviceGroup(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceGroup, data)

    @_docstring_parameter(MobileDeviceProvisioningProfile, subset=True)
    def MobileDeviceProvisioningProfile(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(MobileDeviceProvisioningProfile, data,
                                       subset)

    @_docstring_parameter(NetbootServer)
    def NetbootServer(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(NetbootServer, data)

    @_docstring_parameter(NetworkSegment)
    def NetworkSegment(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(NetworkSegment, data)

    @_docstring_parameter(OSXConfigurationProfile, subset=True)
    def OSXConfigurationProfile(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(OSXConfigurationProfile, data, subset)

    @_docstring_parameter(Package)
    def Package(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Package, data)

    @_docstring_parameter(Peripheral, subset=True)
    def Peripheral(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Peripheral, data, subset)

    @_docstring_parameter(PeripheralType)
    def PeripheralType(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(PeripheralType, data)

    @_docstring_parameter(Policy, subset=True)
    def Policy(self, data=None, subset=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Policy, data, subset)

    @_docstring_parameter(Printer)
    def Printer(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Printer, data)

    @_docstring_parameter(RestrictedSoftware)
    def RestrictedSfotware(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(RestrictedSoftware, data)

    @_docstring_parameter(RemovableMACAddress)
    def RemovableMACAddress(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(RemovableMACAddress, data)

    @_docstring_parameter(SavedSearch)
    def SavedSearch(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(SavedSearch, data)

    @_docstring_parameter(Script)
    def Script(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Script, data)

    @_docstring_parameter(Site)
    def Site(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(Site, data)

    @_docstring_parameter(SoftwareUpdateServer)
    def SoftwareUpdateServer(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(SoftwareUpdateServer, data)

    @_docstring_parameter(SMTPServer)
    def SMTPServer(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(SMTPServer, data)

    @_docstring_parameter(UserExtensionAttribute)
    def UserExtensionAttribute(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(UserExtensionAttribute, data)

    @_docstring_parameter(User)
    def User(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(User, data)

    @_docstring_parameter(UserGroup)
    def UserGroup(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(UserGroup, data)

    @_docstring_parameter(VPPAccount)
    def VPPAccount(self, data=None):
        """{dynamic_docstring}"""
        return self.factory.get_object(VPPAccount, data)


class JSSObjectFactory(object):
    """Create JSSObjects intelligently based on a single parameter.

    Attributes:
        jss: Copy of a JSS object to which API requests are
        delegated.
    """

    def __init__(self, jss):
        """Configure a JSSObjectFactory

        Args:
            jss: JSS object to which API requests should be
                delegated.
        """
        self.jss = jss

    def get_object(self, obj_class, data=None, subset=None):
        """Return a subclassed JSSObject instance by querying for
        existing objects or posting a new object.

        Args:
            obj_class: The JSSObject subclass type to search for or
                create.
            data: The data parameter performs different operations
                depending on the type passed.
                None: Perform a list operation, or for non-container
                    objects, return all data.
                int: Retrieve an object with ID of <data>.
                str: Retrieve an object with name of <str>. For some
                    objects, this may be overridden to include searching
                    by other criteria. See those objects for more info.
                xml.etree.ElementTree.Element: Create a new object from
                    xml.
            subset:
                A list of XML subelement tags to request (e.g.
                ['general', 'purchasing']), OR an '&' delimited string
                (e.g. 'general&purchasing'). This is not supported for
                all JSSObjects.

        Returns:
            JSSObjectList: for empty or None arguments to data.
            JSSObject: Returns an object of type obj_class for searches
                and new objects.
            (FUTURE) Will return None if nothing is found that match
                the search criteria.

        Raises:
            TypeError: if subset not formatted properly.
            JSSMethodNotAllowedError: if you try to perform an operation
                not supported by that object type.
            JSSGetError: If object searched for is not found.
            JSSPostError: If attempted object creation fails.
        """
        if subset:
            if not isinstance(subset, list):
                if isinstance(subset, (str, unicode)):
                    subset = subset.split("&")
                else:
                    raise TypeError

        # List objects

        if data is None:
            url = obj_class.get_url(data)
            if obj_class.can_list and obj_class.can_get:
                if (subset and len(subset) == 1 and subset[0].upper() ==
                        "BASIC") and obj_class is Computer:
                    url += "/subset/basic"

                result = self.jss.get(url)

                if obj_class.container:
                    result = result.find(obj_class.container)

                return self._build_jss_object_list(result, obj_class)

            # Single object

            elif obj_class.can_get:
                xmldata = self.jss.get(url)
                return obj_class(self.jss, xmldata)
            else:
                raise JSSMethodNotAllowedError(
                    obj_class.__class__.__name__)

        # Retrieve individual objects
        elif type(data) in [str, int, unicode]:
            if obj_class.can_get:
                url = obj_class.get_url(data)
                if subset:
                    if not "general" in subset:
                        subset.append("general")
                    url += "/subset/%s" % "&".join(subset)

                xmldata = self.jss.get(url)

                # Some name searches may result in multiple found
                # objects. e.g. A computer search for "MacBook Pro" may
                # return ALL computers which have not had their name
                # changed.
                if xmldata.find("size") is not None:
                    return self._build_jss_object_list(xmldata, obj_class)
                else:
                    return obj_class(self.jss, xmldata)
            else:
                raise JSSMethodNotAllowedError(obj_class.__class__.__name__)

        # Create a new object

        elif isinstance(data, ElementTree.Element):
            if obj_class.can_post:
                url = obj_class.get_post_url()
                return self.jss.post(obj_class, url, data)
            else:
                raise JSSMethodNotAllowedError(obj_class.__class__.__name__)
        else:
            raise ValueError

    def _build_jss_object_list(self, response, obj_class):
        """Build a JSSListData object from response."""
        response_objects = [item for item in response
                            if item is not None and
                            item.tag != "size"]
        objects = [
            JSSListData(obj_class, {i.tag: i.text for i in response_object},
                        self) for response_object in response_objects]

        return JSSObjectList(self, obj_class, objects)


class JSSListData(dict):
    """Holds overview information returned from a listing GET."""

    def __init__(self, obj_class, data, factory):
        """Configure a JSSListData item."""
        self.obj_class = obj_class
        self.factory = factory
        super(JSSListData, self).__init__(data)

    @property
    def id(self):
        """Return the object's ID property."""
        return int(self["id"])

    @property
    def name(self):
        """Return the object's name property."""
        return self["name"]

    def retrieve(self):
        """Retrieve the full object XML for this item."""
        return self.factory.get_object(self.obj_class, self.id)


class JSSObjectList(list):
    """A list style collection of JSSObjects.

    List operations retrieve minimal or overview information for most
    object types. For example, we may want to see all the Computers on
    the JSS but that does not mean we want to do a full object GET for
    each one.

    The JSSObjectList provides Methods to retrieve individual members'
    full information (retrieve_by_id, retrieve), and to retrieve the
    full information for each member of the entire list (retrieve_all).

    Attributes:
        factory: A JSSObjectFactory for managing object construction and
            searching.
        obj_class: A JSSObject class (e.g. jss.Computer) that the list
            contains.
    """

    def __init__(self, factory, obj_class, objects):
        """Construct a list of JSSObjects.

        Args:
            factory: A JSSObjectFactory for managing object construction
                in the event one of the retrieval methods is used.
            obj_class: A JSSObject class (e.g. jss.Computer) that the
                list contains.
            objects: A list of JSSListData objects (incomplete data
                about a JSSObject, as returned by the JSS from a listing
                request).
        """
        self.factory = factory
        self.obj_class = obj_class
        super(JSSObjectList, self).__init__(objects)

    def __repr__(self):
        """Make data human readable."""
        # Note: Large lists/objects may take a long time to indent!
        delimeter = 50 * "-" + "\n"
        output_string = delimeter
        for obj in self:
            output_string += "List index: \t%s\n" % self.index(obj)
            for key, val in obj.items():
                # TODO: Update this to match Spruce output code.
                output_string += "%s:\t\t%s\n" % (key, val)
            output_string += delimeter
        return output_string.encode("utf-8")

    def sort(self):
        """Sort list elements by ID."""
        super(JSSObjectList, self).sort(key=lambda k: k.id)

    def sort_by_name(self):
        """Sort list elements by name."""
        super(JSSObjectList, self).sort(key=lambda k: k.name)

    def retrieve(self, index):
        """Return a JSSObject for the JSSListData element at index."""
        return self[index].retrieve()

    def retrieve_by_id(self, id_):
        """Return a JSSObject for the element with ID id_"""
        items_with_id = [item for item in self if item.id == int(id_)]
        if len(items_with_id) == 1:
            return items_with_id[0].retrieve()

    def retrieve_all(self, subset=None):
        """Return a list of all JSSListData elements as full JSSObjects.

        This can take a long time given a large number of objects,
        and depending on the size of each object. Subsetting to only
        include the data you need can improve performance.

        Args:
            subset: For objects which support it, a list of sub-tags to
                request, or an "&" delimited string, (e.g.
                "general&purchasing").  Default to None.
        """
        # Attempt to speed this procedure up as much as can be done.

        get_object = self.factory.get_object
        obj_class = self.obj_class

        return [get_object(obj_class, list_obj.id, subset)
                for list_obj in self]
