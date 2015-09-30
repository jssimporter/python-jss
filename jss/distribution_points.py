#!/usr/bin/env python
# Copyright (C) 2014 Shea G Craig <shea.craig@da.org>
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
"""distribution_points.py

Utility class for synchronizing packages and scripts to Jamf file
repositories, CDPs, and JDSs.
"""


import os

from .distribution_point import (AFPDistributionPoint, SMBDistributionPoint,
                                 JDS, CDP, LocalRepository)
from .exceptions import JSSError
from .tools import (is_osx, is_linux, is_package)


class DistributionPoints(object):
    """Manage multiple DistributionPoint objects.

    DistributionPoints is an object which reads DistributionPoint
    configuration data from the JSS and serves as a container for
    objects representing the configured distribution points.

    This class provides an abstracted interface for uploading packages
    and dmg's to file repositories.

    PLEASE NOTE: Not all DistributionPoint types support all of the
    available methods, or in the same way. For example, a JDS has
    caveats to the reliability of the exists() method.

    Support for Local repositories, AFP/SMB shares and JDS and CDP
    servers are included, and are selected based on configuration files.

    This object can copy files to multiple repositories, avoiding the
    need to use Casper Admin to "Replicate" from one repository to
    another, as long as the repositories are all configured correctly.

    See the individual Repository subclasses for information regarding
    type-specific properties and configuration.
    """

    def __init__(self, jss):
        """Config the DP dict from configuration file.

        The JSS API endpoint DistributionPoints is used to automatically
        configure AFP and SMB shares. To make use of this, the repo's
        dictionary should contain only the name of the repo, as found in
        the web interface, and the password for the RW user.

        Please see the docstrings for the different DistributionPoint
        subclasses for information regarding required configuration
        information and properties.

        Args:
            jss: JSS server object

        Raises:
            JSSError if an unsupported OS is used.
        """
        self.jss = jss
        self._children = []

        # If no distribution points are configured, there's nothing to
        # do here.
        if self.jss.repo_prefs:
            self.dp_info = self.jss.DistributionPoint().retrieve_all()

            for repo in self.jss.repo_prefs:
                # Handle AFP/SMB shares, as they can be auto-configured.
                # Legacy system did not require explicit type key.
                if not repo.get("type"):
                    # Must be AFP or SMB.
                    # Use JSS.DistributionPoints information to
                    # automatically configure this DP.
                    dpt = self._get_auto_configured_dp(repo)
                # Handle Explictly declared DP's.
                elif repo.get("type") in ["AFP", "SMB"]:
                    dpt = self._get_explictly_configured_dp(repo)
                elif repo.get("type") == "JDS":
                    dpt = JDS(jss=self.jss)
                elif repo.get("type") == "CDP":
                    dpt = CDP(jss=self.jss)
                elif repo.get("type") == "Local":
                    mount_point = repo["mount_point"]
                    share_name = repo["share_name"]
                    dpt = LocalRepository(mount_point=mount_point,
                                          share_name=share_name, jss=self.jss)
                else:
                    raise ValueError("Distribution Point Type not recognized.")

                # Add the DP to the list.
                self._children.append(dpt)

    def _get_auto_configured_dp(self, repo):
        "Return a file share DP from auto-configured data."""
        for dp_object in self.dp_info:
            if repo["name"] == dp_object.findtext("name"):
                url = dp_object.findtext("ip_address")
                connection_type = dp_object.findtext("connection_type")
                share_name = dp_object.findtext("share_name")
                domain = dp_object.findtext("workgroup_or_domain")
                port = dp_object.findtext("share_port")
                username = dp_object.findtext("read_write_username")
                password = repo.get("password")
                # Make very sure this password is unicode.
                if isinstance(password, str):
                    password = unicode(password, "utf-8")

                if is_osx():
                    mount_point = os.path.join("/Volumes", share_name)
                elif is_linux():
                    mount_point = os.path.join("/mnt", share_name)
                else:
                    raise JSSError("Unsupported OS.")

                if connection_type == "AFP":
                    dpt = AFPDistributionPoint(
                        url=url, port=port, share_name=share_name,
                        mount_point=mount_point, username=username,
                        password=password, jss=self.jss)
                elif connection_type == "SMB":
                    dpt = SMBDistributionPoint(
                        url=url, port=port, share_name=share_name,
                        mount_point=mount_point, domain=domain,
                        username=username, password=password,
                        jss=self.jss)

                return dpt

    def _get_explictly_configured_dp(self, repo):
        "Return a file share DP from auto-configured data."""
        url = repo["URL"]

        # If found, strip the scheme off the URL
        if "://" in url:
            url = url.split("://")[1]

        connection_type = repo["type"]
        share_name = repo["share_name"]

        # Domain is not used for AFP.
        domain = repo.get("domain")
        username = repo["username"]
        password = repo["password"]
        # Make very sure this password is unicode.
        if isinstance(password, str):
            password = unicode(password, "utf-8")

        if is_osx():
            mount_point = os.path.join("/Volumes", share_name)
        elif is_linux():
            mount_point = os.path.join("/mnt", share_name)
        else:
            raise JSSError("Unsupported OS.")

        if connection_type == "AFP":

            # If port isn't given, assume it's the std of
            # 548.
            port = repo.get("port", "548")
            dpt = AFPDistributionPoint(
                url=url, port=port, share_name=share_name,
                mount_point=mount_point, username=username, password=password,
                jss=self.jss)
        elif connection_type == "SMB":
            # If port isn't given, assume it's the std of
            # 139.
            port = repo.get("port", "139")
            dpt = SMBDistributionPoint(
                url=url, port=port, share_name=share_name,
                mount_point=mount_point, domain=domain, username=username,
                password=password, jss=self.jss)

        return dpt

    def add_distribution_point(self, distribution_point):
        """Add a distribution point to the list."""
        self._children.append(distribution_point)

    def remove_distribution_point(self, index):
        """Remove a distribution point by index."""
        self._children.pop(index)

    def copy(self, filename, id_=-1, pre_callback=None, post_callback=None):
        """Copy a package or script to all repos.

        Determines appropriate location (for file shares) and type based
        on file extension.

        Args:
            filename: String path to the local file to copy.
            id_: Package or Script object ID to target. For use with JDS
                and CDP DP's only. If uploading a package that does not
                have a corresponding object, use id_ of -1, which is the
                default.
            pre_callback: Func to call before each distribution point
                starts copying. Should accept a Repository connection
                dictionary as a parameter. Will be called like:
                    `pre_callback(repo.connection)`
            post_callback: Func to call after each distribution point
                finishes copying. Should accept a Repository connection
                dictionary as a parameter. Will be called like:
                    `pre_callback(repo.connection)`
        """
        for repo in self._children:
            if is_package(filename):
                copy_method = repo.copy_pkg
            else:
                # All other file types can go to scripts.
                copy_method = repo.copy_script
            if pre_callback:
                pre_callback(repo.connection)
            copy_method(filename, id_)
            if post_callback:
                post_callback(repo.connection)

    def copy_pkg(self, filename, id_=-1):
        """Copy a pkg, dmg, or zip to all repositories.

        Args:
            filename: String path to the local file to copy.
            id_: Integer ID you wish to associate package with for a JDS
                or CDP only. Default is -1, which is used for creating
                a new package object in the database.
        """
        for repo in self._children:
            repo.copy_pkg(filename, id_)

    def copy_script(self, filename, id_=-1):
        """Copy a script to all repositories.

        Takes into account whether a JSS has been migrated. See the
        individual DistributionPoint types for more information.

        Args:
            filename: String path to the local file to copy.
            id_: Integer ID you wish to associate script with for a JDS
                or CDP only. Default is -1, which is used for creating
                a new script object in the database.
        """
        for repo in self._children:
            repo.copy_script(filename, id_)

    def delete(self, filename):
        """Delete a file from all repositories which support it.

        Individual repositories will determine correct location to
        delete from (Scripts vs. Packages).

        This will not remove the corresponding Package or Script object
        from the JSS's database!

        Args:
            filename: The filename you wish to delete (do not include a
                path).
        """
        for repo in self._children:
            if hasattr(repo, "delete"):
                repo.delete(filename)

    def mount(self):
        """Mount all mountable distribution points."""
        for child in self._children:
            if hasattr(child, "mount"):
                child.mount()

    def umount(self, forced=True):
        """Umount all mountable distribution points.

        Defaults to using forced method.
        """
        for child in self._children:
            if hasattr(child, "umount"):
                child.umount(forced)

    def exists(self, filename):
        """Report whether a file exists on all distribution points.

        Determines file type by extension.

        Args:
            filename: Filename you wish to check. (No path! e.g.:
                "AdobeFlashPlayer-14.0.0.176.pkg")

        Returns:
            Boolean
        """
        result = True
        for repo in self._children:
            if not repo.exists(filename):
                result = False
        return result

    def __repr__(self):
        """Print out information on distribution points."""
        output = []
        index = 0
        for child in self._children:
            output.append("%s" % (79 * "-"))
            output.append("Index: %s" % index)
            output.append(child.__repr__())
            index += 1

        return "\n".join(output)


