#!/usr/bin/env python
"""distribution_points.py

Utility classes for synchronizing packages and scripts to Jamf file
repositories.

Copyright (C) 2014 Shea G Craig <shea.craig@da.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


import os
import shutil
import subprocess


class DistributionPoints(object):
    """DistributionPoints is an object which reads DistributionPoint
    configuration data from the JSS and serves as a container for objects
    representing the configured distribution points.

    """
    def __init__(self, j):
        """Populate our distribution point dict from a JSS server's
        DistributionPoints.

        jss:      JSS server object

        """
        self.children = []

        self.response = j.DistributionPoint().retrieve_all()
        for distribution_point in self.response:
            name = distribution_point.findtext('name')
            URL = distribution_point.findtext('ip_address')
            connection_type = distribution_point.findtext('connection_type')
            share_name = distribution_point.findtext('share_name')
            domain = distribution_point.findtext('workgroup_or_domain')
            port = distribution_point.findtext('share_port')
            username = distribution_point.findtext('read_write_username')
            for dpref in j.repos:
                if dpref['name'] == name:
                    password = dpref['password']
                    break
            mount_point = os.path.join('/Volumes', (name + share_name).replace(' ', ''))

            if connection_type == 'AFP':
                dp = AFPDistributionPoint(URL=URL, port=port, share_name=share_name, mount_point=mount_point, username=username, password=password)
            elif connection_type == 'SMB':
                dp = SMBDistributionPoint(URL=URL, port=port, share_name=share_name, mount_point=mount_point, domain=domain, username=username, password=password)

            self.children.append(dp)



class FileUploader(object):
    """FileUploader provides a unified object for copying, deleting, and moving
    packages and dmg's to file repositories.

    Support for AFP/SMB shares, HTTP(S) distribution points, and JDS' are
    included, and are selected based on configuration files or can be overriden
    when the object is instantiated.

    This object can copy files to multiple repositories, avoiding the need to
    use Casper Admin to "Replicate" from one repository to another, as long as
    the repositories are all configured correctly.

    See the individual Repository subclasses for information regarding
    type-specific properties and configuration.

    """
    def __init__(self, jss=[], repos=[]):
        """Pass a JSS object to define a destination as configured by that
        object, OR pass a list of Repository objects to consider as targets.

        """
        self.repos = []
        repos = jss.repos + repos
        for repo in repos:
            self.repos.append(repo)

    def copy(self, filename):
        """Copy file to all repos, guessing file type and destination based
        on its extension.

        filename:       String path to the local file to copy.

        """
        extension = os.path.splitext(filename)[1].upper()
        for repo in self.repos:
            if extension in ['PKG', 'DMG']:
                repo.copy_pkg(filename)
            else:
                # All other file types can go to scripts.
                repo.copy_script(filename)

    def copy_pkg(self, filename):
        """Copy a pkg or dmg to all repositories.

        filename:       String path to the local file to copy.

        """
        for repo in self.repos:
            repo.copy_pkg(filename)

    def copy_script(self, filename):
        """Copy a script to all repositories.

        filename:       String path to the local file to copy.

        """
        for repo in self.repos:
            repo.copy_script(filename)

    def delete(self, filename, repo=None):
        """Delete a file from all repositories, or a single repository.

        file:       String filename of the file to delete.
        repo:       Optional Repository object specifying a single repo on
                    which to operate.

        """
        pass

    def move(self, oldfilename, newfilename, repo=None):
        """Rename a file on all repositories, or a single repository.

        file:       String filename of the file to delete.
        repo:       Optional Repository object specifying a single repo on
                    which to operate.

        """
        pass

class Repository(object):
    """Base class for file repositories."""
    def __init__(self, **connection_args):
        """Store the connection information."""
        self.connection = {}
        for key, value in connection_args.iteritems():
            self.connection[key] = value

        self._build_url()

    # Not really needed, since all subclasses implement this.
    # Placeholder for whether I do want to formally specify the interface
    # like this.
    def _copy(self, filename):
        raise NotImplementedError("Base class 'Repository' should not be used "
                                  "for copying!")

class MountedRepository(Repository):
    def __init__(self, **connection_args):
        super(MountedRepository, self).__init__(**connection_args)

    def _build_url(self):
        pass

    def mount(self):
        """Mount the repository."""
        # Is this volume already mounted; if so, we're done.
        if not self.is_mounted():

            # First, ensure the mountpoint exists
            if not os.path.exists(self.connection['mount_point']):
                os.mkdir(self.connection['mount_point'])

            # Try to mount
            subprocess.check_call(['mount', '-t', self.protocol,
                                   self.connection['mount_url'],
                                   self.connection['mount_point']])

    def umount(self):
        """Try to unmount our mount point."""
        # If not mounted, don't bother.
        if os.path.exists(self.connection['mount_point']):
            subprocess.check_call(['umount', self.connection['mount_point']])

    def is_mounted(self):
        """Test for whether a mount point is mounted."""
        return os.path.ismount(self.connection['mount_point'])

    def copy_pkg(self, filename):
        """Copy a package to the reo's subdirectory."""
        basename = os.path.basename(filename)
        self._copy(filename, os.path.join(self.connection['mount_point'],
                                          'Packages', basename))

    def copy_script(self, filename):
        """Copy a script to the repo's Script subdirectory."""
        basename = os.path.basename(filename)
        self._copy(filename, os.path.join(self.connection['mount_point'],
                                          'Scripts', basename))

    def _copy(self, filename, destination):
        """Copy a file to the repository. Handles folders and single files.
        Will mount if needed.

        """
        if not self.is_mounted():
            self.mount()

        full_filename = os.path.abspath(os.path.expanduser(filename))

        if os.path.isdir(full_filename):
            shutil.copytree(full_filename, destination)
        elif os.path.isfile(full_filename):
            shutil.copyfile(full_filename, destination)


class AFPDistributionPoint(MountedRepository):
    """Represents an AFP repository.

    Please note: OS X seems to cache credentials when you use mount_afp like
    this, so if you change your authentication information, you'll have to
    force a re-authentication.

    """
    protocol = 'afp'

    def __init__(self, **connection_args):
        """Set up an AFP connection.
        Required connection arguments:
        URL:            URL to the mountpoint in the format, including volume
                        name Ex:
                        'my_repository.domain.org/jamf'
                        (Do _not_ include protocol or auth info.)
        mount_point:    Path to a valid mount point.
        username:       For shares requiring authentication, the username.
        password:       For shares requiring authentication, the password.

        """
        super(AFPDistributionPoint, self).__init__(**connection_args)

    def _build_url(self):
        """Helper method for building mount URL strings."""
        if self.connection.get('username') and self.connection.get('password'):
            self.connection['mount_url'] = '%s://%s:%s@%s' % \
                    (self.protocol, self.connection['username'],
                     self.connection['password'], self.connection['URL'])
        else:
            self.connection['mount_url'] = '%s://%s' % \
                    (self.protocol, self.connection['URL'])


class SMBDistributionPoint(MountedRepository):
    protocol = 'smbfs'

    def __init__(self, **connection_args):
        """Set up a SMB connection.
        Required connection arguments:
        URL:            URL to the mountpoint in the format, including volume
                        name Ex:
                        'my_repository.domain.org/jamf'
                        (Do _not_ include protocol or auth info.)
        mount_point:    Path to a valid mount point.
        user_domain:    If you need to specify a domain, do so here.
        username:       For shares requiring authentication, the username.
        password:       For shares requiring authentication, the password.

        """
        super(SMBDistributionPoint, self).__init__(**connection_args)

    def _build_url(self):
        """Helper method for building mount URL strings."""
        if self.connection.get('username') and self.connection.get('password'):
            if self.connection.get('user_domain'):
                auth = r"%s;%s:%s" % (self.connection['user_domain'],
                                        self.connection['username'],
                                        self.connection['password'])
            else:
                auth = "%s:%s" % (self.connection['username'],
                                  self.connection['password'])
            self.connection['mount_url'] = '//%s@%s/%s' % (
                auth, self.connection['URL'], self.connection['share_name'])

        else:
            self.connection['mount_url'] = '//%s/%s' % (
                self.connection['URL'], self.connection['share_name'])


class HTTPRepository(Repository):
    pass


class HTTPSRepository(Repository):
    pass


class JDSRepository(Repository):
    pass