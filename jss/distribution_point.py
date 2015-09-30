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
"""distribution_point.py

Classes representing the various types of file storage availble to
Casper.
"""


import os
import re
import shutil
import socket
import subprocess
import urllib

from . import casper
from .exceptions import JSSError, JSSUnsupportedFileType
try:
    from .contrib.mount_shares_better import mount_share
except ImportError:
    # mount_shares_better uses PyObjC. If using non-system python,
    # chances are good user has not set up PyObjC, so fall back to
    # subprocess to mount. (See mount methods).
    mount_share = None
from .tools import (is_osx, is_linux, is_package)


PKG_FILE_TYPE = 0
EBOOK_FILE_TYPE = 1
IN_HOUSE_APP_FILE_TYPE = 2
SCRIPT_FILE_TYPE = 3


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
        connection: Dictionary for storing connection arguments.
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

    def copy_script(self, filename, id_=-1):
        """Copy a script to the repo's Script subdirectory.

        Scripts are copied as files to a path, or, on a "migrated" JSS,
        are POSTed to the JSS (pass an id if you wish to associate
        the script with an existing Script object).

        Args:
            filename: Path for file to copy.
            id_: Int ID, used _only_ for migrated repos. Default is -1,
                which creates a new Script.
        """
        if ("jss" in self.connection.keys() and
                self.connection["jss"].jss_migrated):
            self._copy_script_migrated(filename, id_, SCRIPT_FILE_TYPE)
        else:
            basename = os.path.basename(filename)
            self._copy(filename, os.path.join(self.connection["mount_point"],
                                              "Scripts", basename))

    def _copy_script_migrated(self, filename, id_=-1,
                              file_type=SCRIPT_FILE_TYPE):
        """Upload a script to a migrated JSS's database.

        On a "migrated" JSS, scripts are POSTed to the JSS. Pass an id
        if you wish to associate the script with an existing Script
        object, otherwise, it will create a new Script object.

        Args:
            filename: Path to script file.
            id_: Int ID of Script object to associate this file with.
                Default is -1, which creates a new Script.
        """
        basefname = os.path.basename(filename)

        resource = open(filename, "rb")
        headers = {"DESTINATION": "1", "OBJECT_ID": str(id_), "FILE_TYPE":
                   file_type, "FILE_NAME": basefname}
        response = self.connection["jss"].session.post(
            url="%s/%s" % (self.connection["jss"].base_url, "dbfileupload"),
            data=resource, headers=headers)
        return response

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

        This method will not delete a script from a migrated JSS.
        Please remove migrated scripts with jss.Script.delete.

        Args:
            filename: String filename only (i.e. no path) of file to
                delete. Will handle deleting scripts vs. packages
                automatically.
        """
        folder = "Packages" if is_package(filename) else "Scripts"
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
        if is_package(filename):
            filepath = os.path.join(self.connection["mount_point"],
                                    "Packages", filename)
        else:
            filepath = os.path.join(self.connection["mount_point"],
                                    "Scripts", filename)
        return os.path.exists(filepath)


class LocalRepository(FileRepository):
    """Casper repo located on a local filesystem path."""
    required_attrs = {"mount_point", "share_name"}

    def __init__(self, **connection_args):
        """Set up Local file share.

        If you have migrated your JSS, you need to pass a JSS object as
        a keyword argument during repository setup, and the JSS object
        needs the jss_migrated=True preference set.

        Args:
            connection_args: Dict with the following key/val pairs:
                mount_point: Path to a valid mount point.
                share_name: The fileshare's name.

                Optional connection arguments (Migrated script support):
                    jss: A JSS Object. NOTE: jss_migrated must be True
                        for this to do anything.
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
        mount_check = subprocess.check_output("mount").splitlines()
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
        share_name = urllib.quote(self.connection["share_name"],
                                  safe="~()*!.'")
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
                delete. Will handle deleting scripts vs. packages
                automatically.
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
        return urllib.quote(self.connection["password"], safe="~()*!.'")


class AFPDistributionPoint(MountedRepository):
    """Represents an AFP repository.

    For a migrated JSS, please see __init__ and copy_script docs.
    """
    protocol = "afp"
    fs_type = "afpfs"
    required_attrs = {"url", "mount_point", "username", "password",
                      "share_name"}

    def __init__(self, **connection_args):
        """Set up an AFP connection.

        If you have migrated your JSS, you need to pass a JSS object as
        a keyword argument during repository setup, and the JSS object
        needs the jss_migrated=True preference set.

        Args:
            connection_args: Dict with the following key/val pairs:
                url: URL to the mountpoint,including volume name e.g.:
                    "my_repository.domain.org/jamf" (Do _not_ include
                    protocol or auth info.)
                mount_point: Path to a valid mount point.
                share_name: The fileshare's name.
                username: Share R/W username.
                password: Share R/W password.

                Optional connection arguments (Migrated script support):
                    jss: A JSS Object. NOTE: jss_migrated must be True
                        for this to do anything.
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
                print self.connection["mount_url"]
            if mount_share:
                self.connection["mount_point"] = mount_share(
                    self.connection["mount_url"])
            else:
                # Non-Apple OS X python:
                args = ["mount", "-t", self.protocol,
                        self.connection["mount_url"],
                        self.connection["mount_point"]]
                if self.connection["jss"].verbose:
                    print " ".join(args)
                subprocess.check_call(args)
        elif is_linux():
            args = ["mount_afp", "-t", self.protocol,
                    self.connection["mount_url"],
                    self.connection["mount_point"]]
            if self.connection["jss"].verbose:
                print " ".join(args)
            subprocess.check_call(args)
        else:
            raise JSSError("Unsupported OS.")


class SMBDistributionPoint(MountedRepository):
    """Represents a SMB distribution point.

    For a migrated JSS, please see __init__ and copy_script docs.
    """
    protocol = "smbfs"
    required_attrs = {"url", "share_name", "mount_point", "domain", "username",
                      "password"}

    def __init__(self, **connection_args):
        """Set up a SMB connection.

        If you have migrated your JSS, you need to pass a JSS object as
        a keyword argument during repository setup, and the JSS object
        needs the jss_migrated=True preference set.

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

                Optional connection arguments (Migrated script support):
                    jss: A JSS Object. NOTE: jss_migrated must be True
                        for this to do anything.
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
        # username=<user>,password=<password>,domain=<domain>,port=139 \
        # //server/share /mnt/<mountpoint>
        if is_osx():
            if mount_share:
                mount_url = "smb:%s" % self.connection["mount_url"]
                if self.connection["jss"].verbose:
                    print mount_url
                self.connection["mount_point"] = mount_share(mount_url)
            else:
                # Non-Apple OS X python:
                args = ["mount", "-t", self.protocol,
                        self.connection["mount_url"],
                        self.connection["mount_point"]]
                if self.connection["jss"].verbose:
                    print " ".join(args)
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
                print " ".join(args)
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
        """Build the URL for POSTing files."""
        self.connection["upload_url"] = (
            "%s/%s" % (self.connection["jss"].base_url, "dbfileupload"))
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

    def copy_script(self, filename, id_=-1):
        """Copy a script to the distribution server.

        Args:
            filename: Full path to file to upload.
            id_: ID of Script object to associate with, or -1 for new
                Script (default).
        """
        self._copy(filename, id_=id_, file_type=SCRIPT_FILE_TYPE)

    def _copy(self, filename, id_=-1, file_type=0):
        """Upload a file to the distribution server.

        Directories/bundle-style packages must be zipped prior to
        copying.
        """
        if os.path.isdir(filename):
            raise JSSUnsupportedFileType(
                "Distribution Server type repos do not permit directory "
                "uploads. You are probably trying to upload a non-flat "
                "package. Please zip or create a flat package.")
        basefname = os.path.basename(filename)
        resource = open(filename, "rb")
        headers = {"DESTINATION": self.destination, "OBJECT_ID": str(id_),
                   "FILE_TYPE": file_type, "FILE_NAME": basefname}
        response = self.connection["jss"].session.post(
            url=self.connection["upload_url"], data=resource, headers=headers)
        if self.connection["jss"].verbose:
            print response

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
        self.connection["jss"].session.post(url=self.connection["delete_url"],
                                            data=data_dict)
        # There's no response if it works.

    def delete(self, filename):
        """Delete a package or script from the distribution server.

        This method simply finds the Package or Script object from the
        database with the API GET call and then deletes it. This will
        remove the file from the database blob.

        For setups which have file share distribution points, you will
        need to delete the files on the shares also.

        Args:
            filename: Filename (no path) to delete.
        """
        if is_package(filename):
            self.connection["jss"].Package(filename).delete()
        else:
            self.connection["jss"].Script(filename).delete()

    def exists(self, filename):
        """Check for the existence of a package or script.

        Unlike other DistributionPoint types, JDS and CDP types have no
        documented interface for checking whether the server and its
        children have a complete copy of a file. The best we can do is
        check for an object using the API /packages URL--JSS.Package()
        or /scripts and look for matches on the filename.

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
        else:
            scripts = self.connection["jss"].Script().retrieve_all()
            for script in scripts:
                if script.findtext("filename") == filename:
                    result = True
                    break

        return result

    def exists_using_casper(self, filename):
        """Check for the existence of a package file.

        Unlike other DistributionPoint types, JDS and CDP types have no
        documented interface for checking whether the server and its
        children have a complete copy of a file. The best we can do is
        check for an object using the API /packages URL--JSS.Package()
        or /scripts and look for matches on the filename.

        If this is not enough, this method uses the results of the
        casper.jxml page to determine if a package exists. This is an
        undocumented feature and as such should probably not be relied
        upon. Please note, scripts are not listed per-distributionserver
        like packages. For scripts, the best you can do is use the
        regular exists method.

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
