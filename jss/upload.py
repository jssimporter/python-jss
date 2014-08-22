#!/usr/bin/env python
"""upload.py

File upload utility classes for python-jss.
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
import subprocess

from . import jss


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
    def __init__(self, jss=None, repos=None):
        """Pass a JSS object to define a destination as configured by that
        object, OR pass a list of Repository objects to consider as targets.

        """
        pass

    def copy(self, filename, repo=None):
        """Copy a file to all repositories, or to a single repository.

        filename:       String path to the local file to copy.
        repo:       Optional Repository object specifying a single repo on
                    which to operate.

        """
        if repo:
            repo.copy(filename)
        else:
            for repo in self.jss.repositories:
                repo.copy(filename)

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
    def copy(self, filename):
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
        # NOT IMPLEMENTED YET.

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


class AFPRepository(MountedRepository):
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
        super(AFPRepository, self).__init__(**connection_args)

    def _build_url(self):
        """Helper method for building mount URL strings."""
        if self.connection.get('username') and self.connection.get('password'):
            self.connection['mount_url'] = '%s://%s:%s@%s' % \
                    (self.protocol, self.connection['username'],
                     self.connection['password'], self.connection['URL'])
        else:
            self.connection['mount_url'] = '%s://%s' % \
                    (self.protocol, self.connection['URL'])


class SMBRepository(MountedRepository):
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
        super(SMBRepository, self).__init__(**connection_args)

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
            self.connection['mount_url'] = '//%s@%s' % (auth,
                                                        self.connection['URL'])

        else:
            self.connection['mount_url'] = '//%s' % self.connection['URL']


class HTTPRepository(Repository):
    pass


class HTTPSRepository(Repository):
    pass


class JDSRepository(Repository):
    pass