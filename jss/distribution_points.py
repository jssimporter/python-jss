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
import re
import shutil
import subprocess
import sys
import urllib

import casper
from .exceptions import JSSUnsupportedFileType


PKG_TYPES = ['.PKG', '.DMG', '.ZIP']
PKG_FILE_TYPE = 0
EBOOK_FILE_TYPE = 1
IN_HOUSE_APP_FILE_TYPE = 2
SCRIPT_FILE_TYPE = 3

class DistributionPoints(object):
    """DistributionPoints is an object which reads DistributionPoint
    configuration data from the JSS and serves as a container for
    objects representing the configured distribution points.

    This class provides an abstract interface for uploading packages and
    dmg's to file repositories.

    PLEASE NOTE: Not all DistributionPoint types support all of the
    available methods, or in the same way. For example, JDS' has
    caveats to the reliability of the exists() method.

    Support for AFP/SMB shares and JDS' are included, and are selected
    based on configuration files. Planned support for HTTP(S) and CDP
    types will come later.

    This object can copy files to multiple repositories, avoiding the
    need to use Casper Admin to "Replicate" from one repository to
    another, as long as the repositories are all configured correctly.

    See the individual Repository subclasses for information regarding
    type-specific properties and configuration.

    """
    def __init__(self, jss):
        """Populate our distribution point dict from our configuration
        file.

        The JSS server's DistributionPoints is used to automatically
        configure AFP and SMB shares. To make use of this, the repo's
        dictionary should contain only the name of the repo, as found in
        the web interface, and the password for the RW user. This method
        is deprecated, and you should fully specify the required
        connection arguments for each DP in the future.

        Please see the docstrings for the different DistributionPoint
        subclasses for information regarding required configuration
        information and properties.

        jss:      JSS server object

        """
        self.jss = jss
        self._children = []

        # If no distribution points are configured, there's nothing to
        # do here.
        if self.jss.repo_prefs:
            self.dp_info = self.jss.DistributionPoint().retrieve_all()
            # Set up a counter for avoiding name clashes with optional
            # name variable.
            counter = 0
            for repo in self.jss.repo_prefs:
                # Handle AFP/SMB shares, as they can be auto-configured.
                # Legacy system did not require explicit type key.
                if not repo.get('type'):
                    # Must be AFP or SMB.
                    # Use JSS.DistributionPoints information to
                    # automatically configure this DP.
                    for dp_object in self.dp_info:
                        if repo['name'] == dp_object.findtext('name'):
                            name = dp_object.findtext('name')
                            URL = dp_object.findtext('ip_address')
                            connection_type = \
                                dp_object.findtext('connection_type')
                            share_name = dp_object.findtext('share_name')
                            domain = dp_object.findtext('workgroup_or_domain')
                            port = dp_object.findtext('share_port')
                            username = \
                                dp_object.findtext('read_write_username')
                            password = repo.get('password')

                            mount_point = os.path.join('/Volumes', share_name)

                            if connection_type == 'AFP':
                                dp = AFPDistributionPoint(URL=URL, port=port,
                                    share_name=share_name,
                                    mount_point=mount_point,
                                    username=username, password=password,
                                    jss=self.jss)
                            elif connection_type == 'SMB':
                                dp = SMBDistributionPoint(URL=URL, port=port,
                                    share_name=share_name,
                                    mount_point=mount_point,
                                    domain=domain, username=username,
                                    password=password,
                                    jss=self.jss)

                            # No need to keep looping.
                            break

                # Handle Explictly declared DP's.
                elif repo.get('type') in ['AFP', 'SMB']:
                    URL = repo['URL']
                    # If found, strip the scheme off the URL
                    # it's reconstructed later
                    if "://" in URL:
                        URL = URL.split('://')[1]

                    connection_type = repo['type']
                    share_name = repo['share_name']
                    # Domain is not used for AFP.
                    domain = repo.get('domain')
                    username = repo['username']
                    password = repo['password']

                    mount_point = os.path.join('/Volumes', share_name)

                    if connection_type == 'AFP':
                        # If port isn't given, assume it's the std of
                        # 548.
                        port = repo.get('port') or '548'
                        dp = AFPDistributionPoint(URL=URL, port=port,
                                                share_name=share_name,
                                                mount_point=mount_point,
                                                username=username,
                                                password=password,
                                                jss=self.jss)
                    elif connection_type == 'SMB':
                        # If port isn't given, assume it's the std of
                        # 139.
                        port = repo.get('port') or '139'
                        dp = SMBDistributionPoint(URL=URL, port=port,
                                                share_name=share_name,
                                                mount_point=mount_point,
                                                domain=domain,
                                                username=username,
                                                password=password,
                                                jss=self.jss)

                elif repo.get('type') == 'JDS':
                    dp = JDS(jss=self.jss)
                else:
                    raise ValueError('Distribution Point Type not recognized.')

                # Add the DP to the list.
                self._children.append(dp)

    def add_distribution_point(self, dp):
        """Add a distribution point to the list."""
        self._children.append(dp)

    def remove_distribution_point(self, index):
        """Remove a distribution point by index."""
        self._children.pop(index)

    def copy(self, filename, id_=-1):
        """Copy file to all repos, guessing file type and destination
        based on its extension.

        filename:       String path to the local file to copy.
        id_:            Package or Script object ID to target. For use
                        with JDS DP's only.

        """
        if is_package(filename):
            for repo in self._children:
                repo.copy_pkg(filename, id_)
        else:
            for repo in self._children:
                # All other file types can go to scripts.
                repo.copy_script(filename, id_)

    def copy_pkg(self, filename, id_=-1):
        """Copy a pkg or dmg to all repositories.

        filename:       String path to the local file to copy.

        """
        for repo in self._children:
            repo.copy_pkg(filename, id_)

    def copy_script(self, filename, id_=-1):
        """Copy a script to all repositories.

        filename:       String path to the local file to copy.

        """
        for repo in self._children:
            repo.copy_script(filename, id_)

    def delete(self, filename):
        """Delete a file from all repositories which support it.
        Individual repositories will determine correct location to
        delete from (Scripts vs. Packages).

        filename:       The filename you wish to delete (do not
                        include a path).

        """
        for repo in self._children:
            if hasattr(repo, 'delete'):
                repo.delete(filename)

    def mount(self):
        """Mount all mountable distribution points."""
        for child in self._children:
            if hasattr(child, 'mount'):
                child.mount()

    def umount(self, forced=True):
        """Umount all mountable distribution points.

        Defaults to using forced method.

        """
        for child in self._children:
            if hasattr(child, 'umount'):
                child.umount(forced)

    def exists(self, filename):
        """Report whether a file exists on all distribution points.
        Determines file type by extension.

        filename:       Filename you wish to check. (No path! e.g.:
                        "AdobeFlashPlayer-14.0.0.176.pkg")

        """
        result = True
        for repo in self._children:
            if not repo.exists(filename):
                result = False

        return result

    def __repr__(self):
        """Nice display of our file shares."""
        output = ''
        index = 0
        for child in self._children:
            output += 79 * '-' + '\n'
            output += 'Index: %s' % index
            output += child.__repr__()
            index += 1

        return output


class Repository(object):
    """Base class for file repositories."""
    def __init__(self, **connection_args):
        """Store the connection information."""
        if self.required_attrs.issubset(set(connection_args.keys())):
            self.connection = {}
            for key, value in connection_args.iteritems():
                self.connection[key] = value

            self._build_url()
        else:
            # Put a custom exception in here.
            missing_attrs = self.required_attrs.difference(
                set(connection_args.keys()))
            raise Exception("Missing REQUIRED argument(s) %s to %s"
                            "distribution point." % (list(missing_attrs),
                                                     self.__class__))

    # Not really needed, since all subclasses implement this.
    # Placeholder for whether I do want to formally specify the
    # interface like this.
    #def _copy(self, filename):
    #    raise NotImplementedError("Base class 'Repository' should not be used"
    #                              " for copying!")

    def __repr__(self):
        output = ''
        output += "\nDistribution Point: %s\n" % self.connection['URL']
        output += "Type: %s\n" % type(self)
        output += "Connection Information:\n"
        for key, val in self.connection.items():
            output += "\t%s: %s\n" % (key, val)

        return output


class MountedRepository(Repository):
    """Parent class for mountable file shares."""
    fs_type = 'undefined'

    def __init__(self, **connection_args):
        super(MountedRepository, self).__init__(**connection_args)

    def _build_url(self):
        pass

    def mount(self, nobrowse=False):
        """Mount the repository.

        If you want it to be hidden from the GUI, pass nobrowse=True.

        """
        # Is this volume already mounted; if so, we're done.
        if not self.is_mounted():

            # First, ensure the mountpoint exists
            if not os.path.exists(self.connection['mount_point']):
                os.mkdir(self.connection['mount_point'])

            # Try to mount
            args = ['mount', '-t', self.protocol, self.connection['mount_url'],
                    self.connection['mount_point']]
            if nobrowse:
                args.insert(1, '-o')
                args.insert(2, 'nobrowse')

            subprocess.check_call(args)

    def umount(self, forced=True):
        """Try to unmount our mount point.

        Defaults to using forced method.

        """
        # If not mounted, don't bother.
        if os.path.exists(self.connection['mount_point']):
            if sys.platform == 'darwin':
                cmd = ['/usr/sbin/diskutil', 'unmount',
                       self.connection['mount_point']]
                if forced:
                    cmd.insert(2, 'force')
                subprocess.check_call(cmd)
            else:
                cmd = ['umount', self.connection['mount_point']]
                if forced:
                    cmd.insert(1, '-f')
                subprocess.check_call(cmd)

    def is_mounted(self):
        """ Test for whether a mount point is mounted.

        If it is currently mounted, determine the path where it's
        mounted and update the connection's mount_point accordingly.

        """
        mount_check = subprocess.check_output('mount').splitlines()
        # The mount command returns lines like this...
        # //username@pretendco.com/JSS%20REPO on /Volumes/JSS REPO
        # (afpfs, nodev, nosuid, mounted by local_me)

        valid_mount_strings = self._get_valid_mount_strings()
        was_mounted = False

        for mount in mount_check:
            fs_match = re.search('\(([\w]*),*.*\)$', mount)
            if fs_match:
                fs_type = fs_match.group(1)
            else:
                fs_type = None
            # Automounts, non-network shares, and network shares
            # all have a slightly different format, so it's easiest to
            # just split.
            mount_string = mount.split(' on ')[0]
            # Does the mount_string match one of our valid_mount_strings?
            if [mstring for mstring in valid_mount_strings if
                mstring in mount_string] and self.fs_type == fs_type:
                # Get the mount point string between from the end back to
                # the last "on", but before the options (wrapped in
                # parenthesis). Considers alphanumerics, / , _ , - and a
                # blank space as valid, but no crazy chars.
                mount_point_match = re.search(
                    'on ([\w/ -]*) \(.*$', mount)
                if mount_point_match:
                    mount_point = mount_point_match.group(1)
                else:
                    mount_point = None
                was_mounted = True
                # Reset the connection's mount point to the discovered
                # value.
                if mount_point:
                    self.connection['mount_point'] = mount_point
                    if self.connection['jss'].verbose:
                        print("%s is already mounted at %s.\n" % \
                              (self.connection['URL'], mount_point))

                # We found the share, no need to continue.
                break

        if not was_mounted:
            # If the share is not mounted, check for another share
            # mounted to the same path and if found, incremement the
            # name to avoid conflicts.
            count = 1
            while os.path.ismount(self.connection['mount_point']):
                self.connection['mount_point'] = "%s-%s" % \
                    (self.connection['mount_point'], count)
                count += 1

        # Do an inexpensive double check...
        return os.path.ismount(self.connection['mount_point'])

    def _get_valid_mount_strings(self):
        """Return a tuple of potential mount strings."""
        # Casper Admin seems to mount in a number of ways:
        #     - hostname/share
        #     - fqdn/share
        # Plus, there's the possibility of:
        #     - IPAddress/share
        # Then factor in the possibility that the port is included too!

        # This gives us a total of up to six valid addresses for mount
        # to report.

        import socket
        # Express results as a set so we don't have any redundent
        # entries.
        results = set()
        URL = self.connection['URL']
        share_name = urllib.quote(self.connection['share_name'],
                                  safe='~()*!.\'')
        port = self.connection['port']

        # URL from python-jss form:
        results.add(os.path.join(URL, share_name))
        results.add(os.path.join('%s:%s' % (URL, port), share_name))

        # IP Address form:
        # socket.gethostbyname() will return an IP address whether
        # an IP address, FQDN, or .local name is provided.
        ip_address = socket.gethostbyname(URL)
        results.add(os.path.join(ip_address, share_name))
        results.add(os.path.join('%s:%s' % (ip_address, port), share_name))

        # Domain name only form:
        domain_name = URL.split('.')[0]
        results.add(os.path.join(domain_name, share_name))
        results.add(os.path.join('%s:%s' % (domain_name, port), share_name))

        # FQDN form using getfqdn:
        # socket.getfqdn() could just resolve back to the ip
        # or be the same as the initial URL so only add it if it's
        # different than both.
        fqdn = socket.getfqdn(ip_address)
        results.add(os.path.join(fqdn, share_name))
        results.add(os.path.join('%s:%s' % (fqdn, port), share_name))

        return tuple(results)

    def copy_pkg(self, filename, id_=-1):
        """Copy a package to the repo's subdirectory.

        filename:           Path for file to copy.
        id_:                Ignored. Used for compatibility with JDS
                            repos.

        """
        basename = os.path.basename(filename)
        self._copy(filename, os.path.join(self.connection['mount_point'],
                                          'Packages', basename))

    def copy_script(self, filename, id_=-1):
        """Copy a script to the repo's Script subdirectory.

        filename:           Path for file to copy.
        id_:                Ignored. Used for compatibility with JDS
                            repos.

        """
        # Scripts are handled either as files copied to a path, or,
        # it's possible to have a JSS that has been "migrated" to use
        # the database to store the script in the script object, like
        # the JDS type, but still using a MountedRepository for PKG
        # files.

        # If you have migrated your JSS, you need to pass a JSS object
        # as a keyword argument during repository setup, and the JSS
        # object needs the jss_migrated=True preference set.
        if 'jss' in self.connection.keys() and \
                self.connection['jss'].jss_migrated:
            self._copy_script_migrated(filename, id_, SCRIPT_FILE_TYPE)
        else:
            basename = os.path.basename(filename)
            self._copy(filename, os.path.join(self.connection['mount_point'],
                                              'Scripts', basename))

    def _copy_script_migrated(self, filename, id_=-1,
                              file_type=SCRIPT_FILE_TYPE):
        """Upload a script to a migrated JSS's database."""
        basefname = os.path.basename(filename)

        resource = open(filename, 'rb')
        headers = {'DESTINATION': '1', 'OBJECT_ID': str(id_), 'FILE_TYPE':
                   file_type, 'FILE_NAME': basefname}
        response = self.connection['jss'].session.post(
            url='%s/%s' % (self.connection['jss'].base_url, 'dbfileupload'),
            data=resource, headers=headers)
        return response

    def _copy(self, filename, destination):
        """Copy a file to the repository. Handles folders and single
        files.  Will mount if needed.

        """
        if not self.is_mounted():
            self.mount()

        full_filename = os.path.abspath(os.path.expanduser(filename))

        if os.path.isdir(full_filename):
            shutil.copytree(full_filename, destination)
        elif os.path.isfile(full_filename):
            shutil.copyfile(full_filename, destination)

    def delete(self, filename):
        """Delete a file from the repository. Pass the file's name
        only. This method will determine whether the file is a package
        or a script.

        """
        if not self.is_mounted():
            self.mount()
        if is_package(filename):
            folder = 'Packages'
        else:
            folder = 'Scripts'
        path = os.path.join(self.connection['mount_point'], folder, filename)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)

    def exists(self, filename):
        """Report whether a file exists on the distribution point.
        Determines file type by extension.

        filename:       Filename you wish to check. (No path! e.g.:
                        "AdobeFlashPlayer-14.0.0.176.pkg")

        """
        if is_package(filename):
            filepath = os.path.join(self.connection['mount_point'],
                                    'Packages', filename)
        else:
            filepath = os.path.join(self.connection['mount_point'],
                                    'Scripts', filename)
        return os.path.exists(filepath)

    def __repr__(self):
        """Add mount status to output."""
        output = super(MountedRepository, self).__repr__()
        output += "Mounted: %s\n" % self.is_mounted()
        return output

    def _encode_password(self):
        """Returns a safely encoded and quoted password."""
        upass = unicode(self.connection['password']).encode('utf-8')
        return urllib.quote(upass, safe='~()*!.\'')


class AFPDistributionPoint(MountedRepository):
    """Represents an AFP repository.

    For migrated JSS, please see __init__ and copy_script.

    Please note: OS X seems to cache credentials when you use mount_afp
    like this, so if you change your authentication information, you'll
    have to force a re-authentication.

    """
    protocol = 'afp'
    fs_type = 'afpfs'
    required_attrs = {'URL', 'mount_point', 'username', 'password',
                      'share_name'}

    def __init__(self, **connection_args):
        """Set up an AFP connection.
        Required connection arguments:
        URL:            URL to the mountpoint in the format, including
                        volume name Ex: 'my_repository.domain.org/jamf'
                        (Do _not_ include protocol or auth info.)
        mount_point:    Path to a valid mount point.
        share_name:     The fileshare's name.
        username:       For shares requiring authentication, the
                        username.
        password:       For shares requiring authentication, the
                        password.

        Optional connection arguments (Migrated script support):
        jss:            A JSS Object. NOTE: jss_migrated must be True
                        for this to do anything.

        """
        super(AFPDistributionPoint, self).__init__(**connection_args)

    def _build_url(self):
        """Helper method for building mount URL strings."""
        if self.connection.get('username') and self.connection.get('password'):
            auth = "%s:%s@" % (self.connection['username'],
                               self._encode_password())
        else:
            auth = ''

        # Optional port number
        if self.connection.get('port'):
            port = ":%s" % self.connection['port']
        else:
            port = ''

        self.connection['mount_url'] = '%s://%s%s%s/%s' % (
            self.protocol, auth, self.connection['URL'], port,
            self.connection['share_name'])


class SMBDistributionPoint(MountedRepository):
    """Represents a SMB distribution point.

    For migrated JSS, please see __init__ and copy_script.

    """

    protocol = 'smbfs'
    fs_type = 'smbfs'
    required_attrs = {'URL', 'share_name', 'mount_point', 'domain', 'username',
                      'password'}

    def __init__(self, **connection_args):
        """Set up a SMB connection.
        Required connection arguments:
        URL:            URL to the mountpoint in the format, including
                        volume name Ex: 'my_repository.domain.org/jamf'
                        (Do _not_ include protocol or auth info.)
        mount_point:    Path to a valid mount point.
        share_name:     The fileshare's name.
        domain:         Specify the domain.
        username:       For shares requiring authentication, the
                        username.
        password:       For shares requiring authentication, the
                        password.

        Optional connection arguments (Migrated script support):
        jss:            A JSS Object. NOTE: jss_migrated must be True
                        for this to do anything.

        """
        super(SMBDistributionPoint, self).__init__(**connection_args)

    def _build_url(self):
        """Helper method for building mount URL strings."""
        # Build auth string
        if self.connection.get('username') and self.connection.get('password'):
            auth = "%s:%s@" % (self.connection['username'],
                               self._encode_password())
            if self.connection.get('domain'):
                auth = r"%s;%s" % (self.connection['domain'], auth)
        else:
            auth = ''

        # Optional port number
        if self.connection.get('port'):
            port = ":%s" % self.connection['port']
        else:
            port = ''

        # Construct mount_url
        self.connection['mount_url'] = '//%s%s%s/%s' % (
            auth, self.connection['URL'], port, self.connection['share_name'])


class JDS(Repository):
    """Class for representing JDS' and their controlling JSS.

    The JSS has a folder to which packages are uploaded. From there, the
    JSS handles the distribution to its JDS'.

    Also, there are caveats to its .exists() method which you should be
    aware of before relying on it.

    I'm not sure, but I imagine that organizations with a JDS will not
    also have other types of DP's, so it may be sufficient to just use
    the JDS class directly rather than as member of a DistributionPoints
    object.

    """
    required_attrs = {'jss'}

    def __init__(self, **connection_args):
        """Set up a connection to a JDS.
        Required connection arguments:
            jss:            A JSS Object.

        """
        super(JDS, self).__init__(**connection_args)
        self.connection['URL'] = self.connection['jss'].base_url

    def _build_url(self):
        """Builds the URL to POST files to."""
        self.connection['upload_url'] = '%s/%s' % \
                (self.connection['jss'].base_url, 'dbfileupload')
        self.connection['delete_url'] = '%s/%s' % \
                (self.connection['jss'].base_url, 'casperAdminSave.jxml')

    def copy_pkg(self, filename, id_=-1):
        """Copy a package to the JDS.

        Required Parameters:
        filename:           Full path to file to upload.
        id_:                ID of Package object to associate with, or
                            -1 for new packages (default).

        """
        self._copy(filename, id_=id_, file_type=PKG_FILE_TYPE)

    def copy_script(self, filename, id_=-1):
        """Copy a script to the JDS.

        Required Parameters:
        filename:           Full path to file to upload.
        id_:                ID of Package object to associate with, or
                            -1 for new packages (default).

        """
        self._copy(filename, id_=id_, file_type=SCRIPT_FILE_TYPE)

    def _copy(self, filename, id_=-1, file_type=0):
        """Upload a file to the JDS.

        Directories, i.e. non-flat packages will fail.

        """
        if os.path.isdir(filename):
            raise JSSUnsupportedFileType(
                'JDS type repos do not permit directory uploads. You are '
                'probably trying to upload a non-flat package. Please zip'
                'or create a flat package.')
        basefname = os.path.basename(filename)

        resource = open(filename, 'rb')
        headers = {'DESTINATION': '1', 'OBJECT_ID': str(id_), 'FILE_TYPE':
                   file_type, 'FILE_NAME': basefname}
        response = self.connection['jss'].session.post(
            url=self.connection['upload_url'], data=resource, headers=headers)
        return response

    def delete_with_casperAdminSave(self, pkg):
        """Delete a pkg from the JDS.

        pkg:        Can be a jss.Package object, an int ID of a
                    package, or a filename.

        """
        # The POST needs the package ID.
        if pkg.__class__.__name__ == 'Package':
            package_to_delete = pkg.id
        elif isinstance(pkg, int):
            package_to_delete = pkg
        elif isinstance(pkg, str):
            package_to_delete = self.connection['jss'].Package(filename).id
        else:
            raise TypeError

        data_dict = {'username': self.connection['jss'].user,
                        'password': self.connection['jss'].password,
                        'deletedPackageID': package_to_delete}
        response = self.connection['jss'].session.post(
            url=self.connection['delete_url'], data=data_dict)
        # There's no response if it works.

    def delete(self, filename):
        """Delete a package or script from the JDS.

        This method simply finds the Package or Script object with
        the API GET call and then deletes it.

        For setups which have
        more than just a JDS, you will need to delete the files on
        the shares also.

        """
        if is_package(filename):
            self.connection['jss'].Package(filename).delete()
        else:
            # Script type.
            self.connection['jss'].Script(filename).delete()

    def exists(self, filename):
        """Check for the existence of a package or script on the JDS.

        Unlike other DistributionPoint types, JDS' have no documented
        interface for checking whether the JDS and its children have a
        complete copy of a file. The best we can do is check for an
        object using the API /packages URL--JSS.Package() or /scripts
        and look for matches on the filename.

        If this is not enough, please use the alternate exists methods.
        For example, it's possible to create a Package object but never
        upload a package file, and this method will still return "True".

        Also, this may be slow, as it needs to retrieve the complete
        list of packages from the server.

        """
        # Technically, the results of the casper.jxml page list the
        # package files on the server. This is an undocumented
        # interface, however.
        result = False
        if is_package(filename):
            packages = self.connection['jss'].Package().retrieve_all()
            for package in packages:
                if package.findtext('filename') == filename:
                    result = True
                    break
        else:
            scripts = self.connection['jss'].Script().retrieve_all()
            for script in scripts:
                if script.findtext('filename') == filename:
                    result = True
                    break

        return result

    def exists_using_casper(self, filename):
        """Check for the existence of a package file on the JDS.

        Unlike other DistributionPoint types, JDS' have no documented
        interface for checking whether the JDS and its children have a
        complete copy of a file. The best we can do is check for a
        package object using the API /packages URL--JSS.Package() and
        look for matches on the filename.

        If this is not enough, this method uses the results of the
        casper.jxml page to determine if a package exists. This is an
        undocumented feature and as such should probably not be relied
        upon. Please note, scripts are not listed per-distributionserver
        like packages. For scripts, the best you can do is use the
        regular exists method.

        It will test for whether the file exists on ALL configured
        distribution servers. This may register False if the JDS is busy
        syncing them.  (Need to test this situation).

        Also, casper.jxml includes checksums. If this method proves
        reliable, checksum comparison will be added as a feature.

        """
        casper_results = casper.Casper(self.connection['jss'])
        distribution_servers = casper_results.find('distributionservers')

        # Step one: Build a list of sets of all package names.
        all_packages = []
        for distribution_server in distribution_servers:
            packages = set()
            for package in distribution_server.findall('packages/package'):
                packages.add(os.path.basename(package.find('fileURL').text))

            all_packages.append(packages)

        # Step two: Intersect the sets.
        base_set = all_packages.pop()
        for packages in all_packages:
            base_set = base_set.intersection(packages)

        # Step three: Check for membership.
        result = filename in base_set

        return result


class HTTPRepository(Repository):
    pass


class HTTPSRepository(Repository):
    pass


def is_package(filename):
    """Return True if filename is a package type."""
    return os.path.splitext(filename)[1].upper() in PKG_TYPES

def is_script(filename):
    """Return True of a filename is NOT a package.

    Because there are so many script types, it's easier to see if
    the file is a package than to see if it is a script.

    """
    return not is_package(filename)