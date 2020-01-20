#!/usr/bin/env python
# Copyright (C) 2014-2018 Shea G Craig, 2018 Mosen
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
"""distribution_point.py

Classes representing the various types of file storage available to
the JAMF Pro Server.
"""

from __future__ import division
from __future__ import print_function

from __future__ import absolute_import
import os
import re
import shutil
import socket
import subprocess
import sys
import io
import math
import multiprocessing
import threading

sys.path.insert(0, '/Library/AutoPkg/JSSImporter')
import requests

try:
    # Python 2.6-2.7
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser


# 2 and 3 compatible
try:
    from urllib.parse import urlparse, urlencode, unquote, quote
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode, unquote, quote
    from urllib2 import urlopen, Request, HTTPError

from . import casper
from . import abstract
from .exceptions import JSSError
try:
    from .contrib.mount_shares_better import mount_share
except ImportError:
    # mount_shares_better uses PyObjC. If using non-system python,
    # chances are good user has not set up PyObjC, so fall back to
    # subprocess to mount. (See mount methods).
    mount_share = None
from .tools import (is_osx, is_linux, is_package)

try:
    import boto.s3
    from boto.s3.connection import S3Connection, OrdinaryCallingFormat, S3ResponseError
    from boto.s3.key import Key

    BOTO_AVAILABLE = True
except ImportError:
    print("boto is not available, you will not be able to use the AWS distribution point type")
    BOTO_AVAILABLE = False

PKG_FILE_TYPE = '0'
EBOOK_FILE_TYPE = '1'
IN_HOUSE_APP_FILE_TYPE = '2'


def auto_mounter(original):
    """Decorator for automatically mounting, if needed."""
    def mounter(*args):
        """If not mounted, mount."""
        self = args[0]
        if not self.is_mounted():
            self.mount()
        return original(*args)
    return mounter


# pylint: disable=too-few-public-methods
class Repository(object):
    """Base class for file repositories.

    This class is not usable on its own; however, it provides the base
    init which all subclasses should use.

    Attributes:
        connection (dict): Dictionary for storing connection arguments.
        required_attrs (Set): A set of the keys which must be supplied to the initializer, otherwise a JSSError will
            be raised.

    Raises:
        JSSError: If mandatory arguments are not supplied to the initializer.
    """
    required_attrs = set()

    def __init__(self, **connection_args):
        """Store the connection information."""
        if self.required_attrs.issubset(set(connection_args.keys())):
            self.connection = connection_args
            self._build_url()
        else:
            missing_attrs = self.required_attrs.difference(
                set(connection_args.keys()))
            raise JSSError(
                "Missing REQUIRED argument(s) %s to %s distribution point." %
                (list(missing_attrs), self.__class__))

    def __repr__(self):
        """Return string representation of connection arguments."""
        output = ["Distribution Point: %s" % self.connection["url"]]
        output.append("Type: %s" % type(self))
        output.append("Connection Information:")
        for key, val in self.connection.items():
            output.append("\t%s: %s" % (key, val))

        return "\n".join(output) + "\n"

    def _build_url(self):
        """Private build url method."""
        raise NotImplementedError


# pylint: enable=too-few-public-methods

class FileRepository(Repository):
    """Local file shares."""

    def _build_url(self):
        """Build a connection URL."""
        pass

    def copy_pkg(self, filename, _):
        """Copy a package to the repo's Package subdirectory.

        Args:
            filename: Path for file to copy.
            _: Ignored. Used for compatibility with JDS repos.
        """
        basename = os.path.basename(filename)
        self._copy(filename, os.path.join(self.connection["mount_point"],
                                          "Packages", basename))

    def _copy(self, filename, destination):   # pylint: disable=no-self-use
        """Copy a file or folder to the repository.

        Will mount if needed.

        Args:
            filename: Path to copy.
            destination: Remote path to copy file to.
        """
        full_filename = os.path.abspath(os.path.expanduser(filename))

        if os.path.isdir(full_filename):
            shutil.copytree(full_filename, destination)
        elif os.path.isfile(full_filename):
            shutil.copyfile(full_filename, destination)

    def delete(self, filename):
        """Delete a file from the repository.

        Args:
            filename: String filename only (i.e. no path) of file to
                delete.
        """
        folder = "Packages"
        path = os.path.join(self.connection["mount_point"], folder, filename)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)

    def exists(self, filename):
        """Report whether a file exists on the distribution point.

        Determines file type by extension.

        Args:
            filename: Filename you wish to check. (No path! e.g.:
                "AdobeFlashPlayer-14.0.0.176.pkg")
        """
        filepath = os.path.join(
            self.connection["mount_point"], "Packages", filename)
        return os.path.exists(filepath)

    def __contains__(self, filename):
        """Magic method to allow constructs similar to:

            if 'abc.pkg' in dp:
        """
        return self.exists(filename)


class LocalRepository(FileRepository):
    """JAMF Pro repo located on a local filesystem path."""
    required_attrs = {"mount_point", "share_name"}

    def __init__(self, **connection_args):
        """Set up Local file share.

        Args:
            connection_args: Dict with the following key/val pairs:
                mount_point: Path to a valid mount point.
                share_name: The fileshare's name.
        """

        super(LocalRepository, self).__init__(**connection_args)
        self.connection["url"] = "local://%s" % self.connection["mount_point"]


class MountedRepository(FileRepository):
    """Parent class for mountable file shares.

    Attributes:
        fs_type: Class attribute, string protocol type (currently AFP
            or SMB).
    """
    fs_type = "undefined"

    def __init__(self, **connection_args):
        """Init a MountedRepository by calling super."""
        super(MountedRepository, self).__init__(**connection_args)

    def mount(self):
        """Mount the repository."""
        if not self.is_mounted():
            # OS X mounting is handled automagically in /Volumes:
            # DO NOT mkdir there!
            # For Linux, ensure the mountpoint exists.
            if not is_osx():
                if not os.path.exists(self.connection["mount_point"]):
                    os.mkdir(self.connection["mount_point"])
            self._mount()

    def _mount(self):
        """Private mount method."""
        raise NotImplementedError

    def umount(self, forced=True):
        """Try to unmount our mount point.

        Defaults to using forced method. If OS is Linux, it will not
        delete the mount point.

        Args:
            forced: Bool whether to force the unmount. Default is True.
        """
        if self.is_mounted():
            if is_osx():
                cmd = ["/usr/sbin/diskutil", "unmount",
                       self.connection["mount_point"]]
                if forced:
                    cmd.insert(2, "force")
                subprocess.check_call(cmd)
            else:
                cmd = ["umount", self.connection["mount_point"]]
                if forced:
                    cmd.insert(1, "-f")
                subprocess.check_call(cmd)

    def is_mounted(self):
        """Test for whether a mount point is mounted.

        If it is currently mounted, determine the path where it's
        mounted and update the connection's mount_point accordingly.
        """
        mount_check = subprocess.check_output("mount").decode().splitlines()
        # The mount command returns lines like this on OS X...
        # //username@pretendco.com/JSS%20REPO on /Volumes/JSS REPO
        # (afpfs, nodev, nosuid, mounted by local_me)
        # and like this on Linux...
        # //pretendco.com/jamf on /mnt/jamf type cifs (rw,relatime,
        # <options>...)

        valid_mount_strings = self._get_valid_mount_strings()
        was_mounted = False
        if is_osx():
            mount_string_regex = re.compile(r"\(([\w]*),*.*\)$")
            mount_point_regex = re.compile(r"on ([\w/ -]*) \(.*$")
        elif is_linux():
            mount_string_regex = re.compile(r"type ([\w]*) \(.*\)$")
            mount_point_regex = re.compile(r"on ([\w/ -]*) type .*$")
        else:
            raise JSSError("Unsupported OS.")

        for mount in mount_check:
            fs_match = re.search(mount_string_regex, mount)
            fs_type = fs_match.group(1) if fs_match else None
            # Automounts, non-network shares, and network shares
            # all have a slightly different format, so it's easiest to
            # just split.
            mount_string = mount.split(" on ")[0]
            # Does the mount_string match one of our valid_mount_strings?
            if [mstring for mstring in valid_mount_strings if
                    mstring in mount_string] and self.fs_type == fs_type:
                # Get the mount point string between from the end back to
                # the last "on", but before the options (wrapped in
                # parenthesis). Considers alphanumerics, / , _ , - and a
                # blank space as valid, but no crazy chars.
                match = re.search(mount_point_regex, mount)
                mount_point = match.group(1) if match else None
                was_mounted = True
                # Reset the connection's mount point to the discovered
                # value.
                if mount_point:
                    self.connection["mount_point"] = mount_point
                    if self.connection["jss"].verbose:
                        print ("%s is already mounted at %s.\n" %
                               (self.connection["url"], mount_point))

                # We found the share, no need to continue.
                break

        if not was_mounted:
            # If the share is not mounted, check for another share
            # mounted to the same path and if found, incremement the
            # name to avoid conflicts.
            count = 1
            while os.path.ismount(self.connection["mount_point"]):
                self.connection["mount_point"] = (
                    "%s-%s" % (self.connection["mount_point"], count))
                count += 1

        # Do an inexpensive double check...
        return os.path.ismount(self.connection["mount_point"])

    def _get_valid_mount_strings(self):
        """Return a tuple of potential mount strings.

        Casper Admin seems to mount in a number of ways:
            - hostname/share
            - fqdn/share
        Plus, there's the possibility of:
            - IPAddress/share
        Then factor in the possibility that the port is included too!
        This gives us a total of up to six valid addresses for mount
        to report.
        """
        results = set()
        join = os.path.join
        url = self.connection["url"]
        share_name = quote(self.connection["share_name"],
                                  safe="~()*!.'$")
        port = self.connection["port"]

        # URL from python-jss form:
        results.add(join(url, share_name))
        results.add(join("%s:%s" % (url, port), share_name))

        # IP Address form:
        # socket.gethostbyname() will return an IP address whether
        # an IP address, FQDN, or .local name is provided.
        ip_address = socket.gethostbyname(url)
        results.add(join(ip_address, share_name))
        results.add(join("%s:%s" % (ip_address, port), share_name))

        # Domain name only form:
        domain_name = url.split(".")[0]
        results.add(join(domain_name, share_name))
        results.add(join("%s:%s" % (domain_name, port), share_name))

        # FQDN form using getfqdn:
        # socket.getfqdn() could just resolve back to the ip
        # or be the same as the initial URL so only add it if it's
        # different than both.
        fqdn = socket.getfqdn(ip_address)
        results.add(join(fqdn, share_name))
        results.add(join("%s:%s" % (fqdn, port), share_name))

        return tuple(results)

    @auto_mounter
    def _copy(self, filename, destination):
        """Copy a file or folder to the repository.

        Will mount if needed.

        Args:
            filename: Path to copy.
            destination: Remote path to copy file to.
        """
        super(MountedRepository, self)._copy(filename, destination)

    @auto_mounter
    def delete(self, filename):
        """Delete a file from the repository.

        Args:
            filename: String filename only (i.e. no path) of file to
                delete.
        """
        super(MountedRepository, self).delete(filename)

    @auto_mounter
    def exists(self, filename):
        """Report whether a file exists on the distribution point.

        Determines file type by extension.

        Args:
            filename: Filename you wish to check. (No path! e.g.:
                "AdobeFlashPlayer-14.0.0.176.pkg")
        """
        return super(MountedRepository, self).exists(filename)

    def __repr__(self):
        """Return a formatted string of connection info."""
        # Do an "update" to get current mount points.
        self.is_mounted()
        output = super(MountedRepository, self).__repr__()
        output += "Mounted: %s\n" % self.is_mounted()
        return output

    @property
    def _encoded_password(self):
        """Returns the safely url-quoted password for this DP."""
        return quote(self.connection["password"], safe="~()*!.'$")


class AFPDistributionPoint(MountedRepository):
    """Represents an AFP repository."""
    protocol = "afp"
    fs_type = "afpfs"
    required_attrs = {"url", "mount_point", "username", "password",
                      "share_name"}

    def __init__(self, **connection_args):
        """Set up an AFP connection.

        Args:
            connection_args (dict): Dict with the following key/val pairs:
                url: URL to the mountpoint,including volume name e.g.:
                    "my_repository.domain.org/jamf" (Do _not_ include
                    protocol or auth info.)
                mount_point: Path to a valid mount point.
                share_name: The fileshare's name.
                username: Share R/W username.
                password: Share R/W password.
        """
        super(AFPDistributionPoint, self).__init__(**connection_args)
        # Check to see if share is mounted, and update mount point
        self.is_mounted()

    def _build_url(self):
        """Build the URL string to mount this file share."""
        if self.connection.get("username") and self.connection.get("password"):
            auth = "%s:%s@" % (self.connection["username"],
                               self._encoded_password)
        else:
            auth = ""

        # Optional port number
        port = self.connection.get("port")
        port = ":" + port if port else ""

        self.connection["mount_url"] = "%s://%s%s%s/%s" % (
            self.protocol, auth, self.connection["url"], port,
            self.connection["share_name"])

    def _mount(self):
        """Mount based on which OS is running."""
        # mount_afp "afp://scraig:<password>@address/share" <mnt_point>
        if is_osx():
            if self.connection["jss"].verbose:
                print(self.connection["mount_url"])
            if mount_share:
                self.connection["mount_point"] = mount_share(
                    self.connection["mount_url"])
            else:
                # Non-Apple OS X python:
                args = ["mount", "-t", self.protocol,
                        self.connection["mount_url"],
                        self.connection["mount_point"]]
                if self.connection["jss"].verbose:
                    print(" ".join(args))
                subprocess.check_call(args)
        elif is_linux():
            args = ["mount_afp", "-t", self.protocol,
                    self.connection["mount_url"],
                    self.connection["mount_point"]]
            if self.connection["jss"].verbose:
                print(" ".join(args))
            subprocess.check_call(args)
        else:
            raise JSSError("Unsupported OS.")


class SMBDistributionPoint(MountedRepository):
    """Represents a SMB distribution point."""
    protocol = "smbfs"
    required_attrs = {"url", "share_name", "mount_point", "domain", "username",
                      "password"}

    def __init__(self, **connection_args):
        """Set up a SMB connection.

        Args:
            connection_args: Dict with the following key/val pairs:
                url: URL to the mountpoint,including volume name e.g.:
                    "my_repository.domain.org/jamf" (Do _not_ include
                    protocol or auth info.)
                mount_point: Path to a valid mount point.
                share_name: The fileshare's name.
                domain: Specify the domain.
                username: Share R/W username.
                password: Share R/W password.
        """
        super(SMBDistributionPoint, self).__init__(**connection_args)
        if is_osx():
            self.fs_type = "smbfs"
        if is_linux():
            self.fs_type = "cifs"
        # Check to see if share is mounted, and update.
        self.is_mounted()

    def _build_url(self):
        """Build the URL string to mount this file share."""
        if self.connection.get("username") and self.connection.get("password"):
            auth = "%s:%s@" % (self.connection["username"],
                               self._encoded_password)
            if self.connection.get("domain"):
                auth = r"%s;%s" % (self.connection["domain"], auth)
        else:
            auth = ""

        # Optional port number
        port = self.connection.get("port")
        port = ":" + port if port else ""

        # Construct mount_url
        self.connection["mount_url"] = "//%s%s%s/%s" % (
            auth, self.connection["url"], port, self.connection["share_name"])

    def _mount(self):
        """Mount based on which OS is running."""
        # mount -t cifs -o \
        # username=<user>,password=<password>,domain=<domain>,port=445 \
        # //server/share /mnt/<mountpoint>
        if is_osx():
            if mount_share:
                mount_url = "smb:%s" % self.connection["mount_url"]
                if self.connection["jss"].verbose:
                    print(mount_url)
                self.connection["mount_point"] = mount_share(mount_url)
            else:
                # Non-Apple OS X python:
                args = ["mount", "-t", self.protocol,
                        self.connection["mount_url"],
                        self.connection["mount_point"]]
                if self.connection["jss"].verbose:
                    print(" ".join(args))
                subprocess.check_call(args)
        elif is_linux():
            args = ["mount", "-t", "cifs", "-o",
                    "username=%s,password=%s,domain=%s,port=%s" %
                    (self.connection["username"], self.connection["password"],
                     self.connection["domain"], self.connection["port"]),
                    "//%s/%s" % (self.connection["url"],
                                 self.connection["share_name"]),
                    self.connection["mount_point"]]
            if self.connection["jss"].verbose:
                print(" ".join(args))
            subprocess.check_call(args)
        else:
            raise JSSError("Unsupported OS.")


class DistributionServer(Repository):
    """Abstract class for representing JDS and CDP type repos.

    The JSS has a folder to which packages are uploaded via a private
    API call to dbfileupload. From there, the JSS handles the
    distribution to its Cloud and JDS points.

    There are caveats to its exists() method which you should be
    aware of, along with a private API exists_with_casper method, which
    probably works more like what one would expect. Please see those
    methods for more information.
    """
    required_attrs = {"jss"}
    destination = "0"

    def __init__(self, **connection_args):
        """Set up a connection to a distribution server.

        Args:
            connection_args: Dict, with required key:
                jss: A JSS Object.
        """
        super(DistributionServer, self).__init__(**connection_args)
        self.connection["url"] = self.connection["jss"].base_url

    def _build_url(self):
        """Build the URL for POSTing files. 10.2 and earlier.

        This actually still works in some scenarios, but it seems like it will be deprecated soon.
        """
        self.connection["upload_url"] = (
                "%s/%s" % (self.connection["jss"].base_url, "dbfileupload"))
        self.connection["delete_url"] = (
                "%s/%s" % (self.connection["jss"].base_url,
                           "casperAdminSave.jxml"))

    def _build_url_modern(self):
        """Build the URL for POSTing files.

        This uses the UploadServlet that has been used to handle most file uploads into JAMF Pro.
        """
        self.connection["upload_url"] = (
            "%s/%s" % (self.connection["jss"].base_url, "upload"))
        self.connection["delete_url"] = (
            "%s/%s" % (self.connection["jss"].base_url,
                       "casperAdminSave.jxml"))

    def copy_pkg(self, filename, id_=-1):
        """Copy a package to the distribution server.

        Bundle-style packages must be zipped prior to copying.

        Args:
            filename: Full path to file to upload.
            id_: ID of Package object to associate with, or -1 for new
                packages (default).
        """
        self._copy(filename, id_=id_, file_type=PKG_FILE_TYPE)

    def _copy(self, filename, id_=-1, file_type=0):
        """Upload a file to the distribution server. 10.2 and earlier

        Directories/bundle-style packages must be zipped prior to
        copying.
        """
        if os.path.isdir(filename):
            raise TypeError(
                "Distribution Server type repos do not permit directory "
                "uploads. You are probably trying to upload a non-flat "
                "package. Please zip or create a flat package.")
        basefname = os.path.basename(filename)
        resource = open(filename, "rb")
        headers = {"DESTINATION": self.destination, "OBJECT_ID": str(id_),
                   "FILE_TYPE": file_type, "FILE_NAME": basefname}
        response = self.connection["jss"].session.post(
            url=self.connection["upload_url"],
            data=resource.read(),
            headers=headers)
        if self.connection["jss"].verbose:
            print(response)

    def _copy_new(self, filename, id_=-1, file_type=0):
        """Upload a file to the distribution server.

        Directories/bundle-style packages must be zipped prior to
        copying.
        """
        if os.path.isdir(filename):
            raise TypeError(
                "Distribution Server type repos do not permit directory "
                "uploads. You are probably trying to upload a non-flat "
                "package. Please zip or create a flat package.")
        basefname = os.path.basename(filename)
        resource = open(filename, "rb")
        headers = {"sessionIdentifier": "com.jamfsoftware.jss.objects.packages.Package:%s" % str(id_),
                   "fileIdentifier": "FIELD_FILE_NAME_FOR_DIST_POINTS"}
        response = self.connection["jss"].session.post(
            url=self.connection["upload_url"],
            data=resource.read(),
            headers=headers)
        print(response)
        if self.connection["jss"].verbose:
            print(response)

    def delete_with_casper_admin_save(self, pkg):
        """Delete a pkg from the distribution server.

        Args:
            pkg: Can be a jss.Package object, an int ID of a package, or
                a filename.
        """
        # The POST needs the package ID.
        if pkg.__class__.__name__ == "Package":
            package_to_delete = pkg.id
        elif isinstance(pkg, int):
            package_to_delete = pkg
        elif isinstance(pkg, str):
            package_to_delete = self.connection["jss"].Package(pkg).id
        else:
            raise TypeError

        data_dict = {"username": self.connection["jss"].user,
                     "password": self.connection["jss"].password,
                     "deletedPackageID": package_to_delete}
        self.connection["jss"].session.post(
            url=self.connection["delete_url"], data=data_dict)
        # There's no response if it works.

    def delete(self, filename):
        """Delete a package distribution server.

        This method simply finds the Package object from the database
        with the API GET call and then deletes it. This will remove the
        file from the database blob.

        For setups which have file share distribution points, you will
        need to delete the files on the shares also.

        Args:
            filename: Filename (no path) to delete.
        """
        if is_package(filename):
            self.connection["jss"].Package(filename).delete()

    def exists(self, filename):
        """Check for the existence of a package.

        Unlike other DistributionPoint types, JDS and CDP types have no
        documented interface for checking whether the server and its
        children have a complete copy of a file. The best we can do is
        check for an object using the API /packages URL--JSS.Package()
        and look for matches on the filename.

        If this is not enough, please use the alternate
        exists_with_casper method.  For example, it's possible to create
        a Package object but never upload a package file, and this
        method will still return "True".

        Also, this may be slow, as it needs to retrieve the complete
        list of packages from the server.
        """
        # Technically, the results of the casper.jxml page list the
        # package files on the server. This is an undocumented
        # interface, however.
        result = False
        if is_package(filename):
            packages = self.connection["jss"].Package().retrieve_all()
            for package in packages:
                if package.findtext("filename") == filename:
                    result = True
                    break

        return result

    def exists_using_casper(self, filename):
        """Check for the existence of a package file.

        Unlike other DistributionPoint types, JDS and CDP types have no
        documented interface for checking whether the server and its
        children have a complete copy of a file. The best we can do is
        check for an object using the API /packages URL--JSS.Package()
        and look for matches on the filename.

        If this is not enough, this method uses the results of the
        casper.jxml page to determine if a package exists. This is an
        undocumented feature and as such should probably not be relied
        upon.

        It will test for whether the file exists on ALL configured
        distribution servers. This may register False if the JDS is busy
        syncing them.
        """
        casper_results = casper.Casper(self.connection["jss"])
        distribution_servers = casper_results.find("distributionservers")

        # Step one: Build a list of sets of all package names.
        all_packages = []
        for distribution_server in distribution_servers:
            packages = set()
            for package in distribution_server.findall("packages/package"):
                packages.add(os.path.basename(package.find("fileURL").text))

            all_packages.append(packages)

        # Step two: Intersect the sets.
        base_set = all_packages.pop()
        for packages in all_packages:
            base_set = base_set.intersection(packages)

        # Step three: Check for membership.
        return filename in base_set


class JDS(DistributionServer):
    """Class for representing a JDS and its controlling JSS.

    The JSS has a folder to which packages are uploaded. From there, the
    JSS handles the distribution to its Cloud and JDS points.

    This class should be considered experimental!
    - There are caveats to its .exists() method
    - It is unclear at the moment what the interaction is in systems
    that have both a JDS and a CDP, especially depending on which is the
    master.
    """
    required_attrs = {"jss"}
    destination = "1"


class CDP(DistributionServer):
    """Class for representing a CDP and its controlling JSS.

    The JSS has a folder to which packages are uploaded. From there, the
    JSS handles the distribution to its Cloud and JDS points.

    This class should be considered experimental!
    - There are caveats to its .exists() method
    - It is unclear at the moment what the interaction is in systems
    that have both a JDS and a CDP, especially depending on which is the
    master.
    """
    required_attrs = {"jss"}
    destination = "2"


class CloudDistributionServer(Repository):
    """Abstract class for representing JCDS type repos.

    """
    def package_index_using_casper(self):
        """Get a list of packages on the JCDS

        Similar to JDS and CDP, JCDS types have no
        documented interface for checking whether the server and its
        children have a complete copy of a file. The best we can do is
        check for an object using the API /packages URL--JSS.Package()
        and look for matches on the filename.

        If this is not enough, this method uses the results of the
        casper.jxml page to determine if a package exists. This is an
        undocumented feature and as such should probably not be relied
        upon.

        It will test for whether the file exists on only cloud distribution points.
        """
        casper_results = casper.Casper(self.connection["jss"])
        cloud_distribution_points = casper_results.find("cloudDistributionPoints")

        # Step one: Build a list of sets of all package names.
        all_packages = []
        for distribution_point in cloud_distribution_points:
            if distribution_point.findtext('name') != 'Jamf Cloud':
                continue  # type 4 might be reserved for JCDS?

            for package in distribution_point.findall("packages/package"):
                package_obj = casper_results.find("./packages/package[id='%s']" % (package.findtext('id'),))

                all_packages.append({
                    'id': package.findtext('id'),
                    'checksum': package.findtext('checksum'),
                    'size': package.findtext('size'),
                    'lastModified': package.findtext('lastModified'),
                    'fileURL': unquote(package.findtext('fileURL')),
                    'name': package_obj.findtext('name'),
                    'filename': package_obj.findtext('filename'),
                })

        return all_packages


def _jcds_upload_chunk(
        filename,
        base_url,
        upload_token,
        chunk_index,
        chunk_size,
        total_chunks):
    """Upload a single chunk of a file to JCDS.

    Args:
        filename (str): The full path to the file being uploaded.
        base_url (str): The JCDS base URL which includes the regional hostname and the tenant id.
        upload_token (str): The upload token, scraped from legacy/packages.html
        chunk_index (int): The zero-based index of the chunk being uploaded.
        total_chunks (int): The total count of chunks to upload

    Returns:
        dict: JSON Response from JCDS
    """
    print("Working on Chunk [{}/{}]".format(chunk_index + 1, total_chunks))
    resource = open(filename, "rb")
    resource.seek(chunk_index * chunk_size)
    chunk_data = resource.read(chunk_size)
    basefname = os.path.basename(filename)
    chunk_url = "{}/{}/part?chunk={}&chunks={}".format(
        base_url, basefname, chunk_index, total_chunks
    )

    chunk_reader = io.BytesIO(chunk_data)
    headers = {"X-Auth-Token": upload_token}
    response = requests.post(
        url=chunk_url,
        headers=headers,
        files={'file': chunk_reader},
    )

    return response.json()


# Semaphore controlling max workers for chunked uploads
jcds_semaphore = threading.BoundedSemaphore(value=3)


class JCDSChunkUploadThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.filename = kwargs['filename']
        self.base_url = kwargs['base_url']
        self.upload_token = kwargs['upload_token']
        self.chunk_index = kwargs['chunk_index']
        self.chunk_size = kwargs['chunk_size']
        self.total_chunks = kwargs['total_chunks']

        super_kwargs = dict(kwargs)
        del super_kwargs['filename']
        del super_kwargs['base_url']
        del super_kwargs['upload_token']
        del super_kwargs['chunk_index']
        del super_kwargs['chunk_size']
        del super_kwargs['total_chunks']

        super(JCDSChunkUploadThread, self).__init__(*args, **super_kwargs)

    def run(self):
        jcds_semaphore.acquire()
        try:
            print("Working on Chunk [{}/{}]".format(self.chunk_index + 1, self.total_chunks))

            resource = open(self.filename, "rb")
            resource.seek(self.chunk_index * self.chunk_size)
            chunk_data = resource.read(self.chunk_size)
            basefname = os.path.basename(self.filename)
            chunk_url = "{}/{}/part?chunk={}&chunks={}".format(
                self.base_url, basefname, self.chunk_index, self.total_chunks
            )

            chunk_reader = io.BytesIO(chunk_data)
            headers = {"X-Auth-Token": self.upload_token}
            response = requests.post(
                url=chunk_url,
                headers=headers,
                files={'file': chunk_reader},
            )

            return response.json()
        except:
            pass
        finally:
            jcds_semaphore.release()


class AWS(CloudDistributionServer, abstract.AbstractRepository):
    """Class for representing an AWS Cloud Distribution Point and its controlling JSS.

    """
    required_attrs = {"jss", "bucket"}

    def __init__(self, **connection_args):
        """Set up a connection to an AWS S3 bucket.

        It is more secure to use the following environment variables provided by boto:

            AWS_ACCESS_KEY_ID - The access key id to the jamf bucket
            AWS_SECRET_ACCESS_KEY - The secret access key to the jamf bucket

        You may also use the file ~/.boto as described in the boto documentation.

        Args:
            connection_args: Dict, with required keys:
                jss: A JSS Object.
                bucket: Name of the JAMF bucket.
                aws_access_key_id (optional): The access key id
                secret_access_key (optional): The secret access key, use environment instead.
                host (optional): A bucket host. Seems to be needed if your bucket is not in the default location
                    eg. southeast asia ap 2
                chunk_size (optional): The chunk size for large objects >50mb

        Throws:
            S3ResponseError if the bucket does not exist
        """
        super(AWS, self).__init__(**connection_args)
        self.s3 = S3Connection(
            aws_access_key_id=connection_args.get('aws_access_key_id', None),
            aws_secret_access_key=connection_args.get('aws_secret_access_key', None),
            host=connection_args.get('host', boto.s3.connection.NoHostProvided),
        )
        try:
            self.bucket = self.s3.get_bucket(connection_args['bucket'])
        except S3ResponseError as e:
            raise JSSError("got error getting bucket, may not exist: {}".format(connection_args['bucket']))

        self.connection["url"] = self.bucket
        self.chunk_size = connection_args.get('chunk_size', 52428800)  # 50 mb default

    def _build_url(self):
        """Build a connection URL."""
        pass

    def copy_pkg(self, filename, id_=-1):
        """Copy a package to the repo's Package subdirectory.

        Args:
            filename: Path for file to copy.
            id_: Unused
        """
        self._copy(filename, id_=id_)

    def _copy(self, filename, id_=-1):   # type: (str, int) -> None
        """Copy a file or folder to the bucket.

        Does not yet support chunking.

        Args:
            filename: Path to copy.
            destination: Remote path to copy file to.
        """
        bucket_key = os.path.basename(filename)
        exists = self.bucket.get_key(bucket_key)
        if exists:
            print("Already exists")
        else:
            k = Key(self.bucket)
            k.key = bucket_key
            k.set_metadata('jamf-package-id', id_)
            k.set_contents_from_filename(filename)

    def delete(self, filename):  # type: (str) -> None
        bucket_key = os.path.basename(filename)
        self.bucket.delete_key(bucket_key)

    def exists(self, filename):  # type: (str) -> bool
        """Check whether a package already exists by checking for a bucket item with the same filename.

        Args:
            filename: full path to filename. Only the name itself will be checked.

        Returns:
            True if the package exists, else false
        """
        k = self.bucket.get_key(os.path.basename(filename))
        return k is not None


class JCDS(CloudDistributionServer):
    """Class for representing a JCDS and its controlling jamfcloud JSS.

    The JSS allows direct upload to the JCDS by exposing the access token from the package upload page.

    This class should be considered experimental!
    """
    required_attrs = {"jss"}
    destination = "3"
    workers = 3
    chunk_size = 1048768

    def __init__(self, **connection_args):
        """Set up a connection to a distribution server.

        Args:
            connection_args (dict):
                jss (JSS): The associated JAMF Pro Server instance
        """
        super(JCDS, self).__init__(**connection_args)
        self.connection["url"] = "JCDS"

    def _scrape_tokens(self):
        """Scrape JCDS upload URL and upload access token from the jamfcloud instance."""
        jss = self.connection['jss']
        response = jss.scrape('legacy/packages.html?id=-1&o=c')
        matches = re.search(r'data-base-url="([^"]*)"', response.content.decode("utf-8"))
        if matches is None:
            raise JSSError('Did not find the JCDS base URL on the packages page. Is this actually Jamfcloud?')

        jcds_base_url = matches.group(1)

        matches = re.search(r'data-upload-token="([^"]*)"', response.content.decode("utf-8"))
        if matches is None:
            raise JSSError('Did not find the JCDS upload token on the packages page. Is this actually Jamfcloud?')

        jcds_upload_token = matches.group(1)

        h = HTMLParser()
        jcds_base_url = h.unescape(jcds_base_url)
        self.connection['jcds_base_url'] = jcds_base_url
        self.connection['jcds_upload_token'] = jcds_upload_token
        self.connection["url"] = jcds_base_url  # This is to make JSSImporter happy because it accesses .connection

    def _build_url(self):
        """Build a connection URL."""
        pass

    def copy_pkg(self, filename, id_=-1):
        """Copy a package to the JAMF Cloud distribution server.

        Bundle-style packages must be zipped prior to copying.

        Args:
            filename: Full path to file to upload.
            id_: ID of Package object to associate with, or -1 for new
                packages (default).
        """
        self._copy(filename, id_=id_)

    def _build_chunk_url(self, filename, chunk, chunk_total):
        """Build the path to the chunk being uploaded to the JCDS."""
        return "{}/{}/part?chunk={}&chunks={}".format(
            self.connection["jcds_base_url"], filename, chunk, chunk_total
        )

    def _copy_multiprocess(self, filename, upload_token, id_=-1):
        """Upload a file to the distribution server using multiple processes to upload several chunks in parallel.

        Directories/bundle-style packages must be zipped prior to copying.
        """
        fsize = os.stat(filename).st_size
        total_chunks = int(math.ceil(fsize / JCDS.chunk_size))
        p = multiprocessing.Pool(3)

        def _chunk_args(chunk_index):
            return [filename, self.connection["jcds_base_url"], upload_token, chunk_index, JCDS.chunk_size, total_chunks]

        for chunk in xrange(0, total_chunks):
            res = p.apply_async(_jcds_upload_chunk, _chunk_args(chunk))
            data = res.get(timeout=10)
            print("id: {0}, version: {1}, size: {2}, filename: {3}, lastModified: {4}, created: {5}".format(
                data['id'], data['version'], data['size'], data['filename'], data['lastModified'], data['created']))

    def _copy_threaded(self, filename, upload_token, id_=-1):
        """Upload a file to the distribution server using multiple threads to upload several chunks in parallel."""
        fsize = os.stat(filename).st_size
        total_chunks = int(math.ceil(fsize / JCDS.chunk_size))

        for chunk in xrange(0, total_chunks):
            t = JCDSChunkUploadThread(
                filename=filename,
                base_url=self.connection["jcds_base_url"],
                upload_token=upload_token,
                chunk_index=chunk,
                chunk_size=JCDS.chunk_size,
                total_chunks=total_chunks,
            )
            t.start()

    def _copy_sequential(self, filename, upload_token, id_=-1):
        """Upload a file to the distribution server using the same process as python-jss.

        Directories/bundle-style packages must be zipped prior to copying.
        """
        fsize = os.stat(filename).st_size
        total_chunks = int(math.ceil(fsize / JCDS.chunk_size))

        basefname = os.path.basename(filename)
        resource = open(filename, "rb")

        headers = {
            "X-Auth-Token": self.connection['jcds_upload_token'],
            # "Content-Type": "application/octet-steam",
        }

        for chunk in xrange(0, total_chunks):
            resource.seek(chunk * JCDS.chunk_size)
            chunk_data = resource.read(JCDS.chunk_size)
            chunk_reader = io.BytesIO(chunk_data)
            chunk_url = self._build_chunk_url(basefname, chunk, total_chunks)
            response = self.connection["jss"].session.post(
                url=chunk_url,
                headers=headers,
                files={'file': chunk_reader},
            )

            if self.connection["jss"].verbose:
                print(response.json())

        resource.close()

    def _copy(self, filename, id_=-1, file_type=0):
        """Upload a file to the distribution server. 10.2 and earlier

        Directories/bundle-style packages must be zipped prior to
        copying.

        JCDS returns a JSON structure like this::

            {
                u'status': u'PENDING',
                u'created': u'2018-07-10T03:21:17.000Z',
                u'lastModified': u'2018-07-11T03:55:32.000Z',
                u'filename': u'SkypeForBusinessInstaller-16.18.0.51.pkg',
                u'version': 6,
                u'md5': u'',
                u'sha512': u'',
                u'id': u'3a7e6a7479fc4000bf53a9693d906b11',
                u'size': 35658112
            }

        """
        if os.path.isdir(filename):
            raise TypeError(
                "JCDS Server type repos do not permit directory "
                "uploads. You are probably trying to upload a non-flat "
                "package. Please zip or create a flat package.")

        if 'jcds_upload_token' not in self.connection:
            self._scrape_tokens()

        self._copy_threaded(filename, self.connection['jcds_upload_token'])
        # if False:
        #self._copy_sequential(filename, self.connection['jcds_upload_token'])
        # else:
        #     self._copy_threaded(filename, self.connection['jcds_upload_token'])

    def exists(self, filename):
        """Check whether a package file already exists."""
        packages = self.package_index_using_casper()
        for p in packages:
            url, token = p['fileURL'].split('?', 2)
            urlparts = url.split('/')

            if urlparts[-1] == filename:
                return True

        return False

    def __repr__(self):
        """Return string representation of connection arguments."""
        output = ["JAMF Cloud Distribution Server: %s" % self.connection["jss"].base_url]
        output.append("Type: %s" % type(self))
        output.append("Connection Information:")
        for key, val in self.connection.items():
            output.append("\t%s: %s" % (key, val))

        return "\n".join(output) + "\n"
