#!/usr/bin/python
# Copyright (C) 2015 Michael Lynn
# https://gist.github.com/pudquick/1362a8908be01e23041d
# https://michaellynn.github.io/2015/08/08/learn-you-a-better-pyobjc-bridgesupport-signature/

# This version has been modified by Shea Craig to handle High Sierra.

"""mount_shares_better.py

Mount file shares on OS X.
"""


from __future__ import absolute_import
from distutils.version import StrictVersion
import subprocess

# PyLint cannot properly find names inside Cocoa libraries, so issues bogus
# No name 'Foo' in module 'Bar' warnings. Disable them.
# pylint: disable=no-name-in-module
from CoreFoundation import CFURLCreateWithString
import Foundation  # pylint: disable=unused-import
from objc import (initFrameworkWrapper, pathForFramework, loadBundleFunctions)
# pylint: enable=no-name-in-module


class AttrDict(dict):
    """Attribute Dictionary"""
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


NetFS = AttrDict()  # pylint: disable=invalid-name
# Can cheat and provide 'None' for the identifier, it'll just use
# frameworkPath instead.
# scan_classes=False means only add the contents of this Framework.
# pylint: disable=invalid-name
NetFS_bundle = initFrameworkWrapper(
    'NetFS', frameworkIdentifier=None,
    frameworkPath=pathForFramework('NetFS.framework'), globals=NetFS,
    scan_classes=False)
# pylint: enable=invalid-name

# https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/ObjCRuntimeGuide/Articles/ocrtTypeEncodings.html
# Fix NetFSMountURLSync signature
del NetFS['NetFSMountURLSync']
loadBundleFunctions(NetFS_bundle, NetFS, [('NetFSMountURLSync', b'i@@@@@@o^@')])


def mount_share(share_path):
    """Mounts a share at /Volumes

    Args:
        share_path: String URL with all auth info to connect to file share.

    Returns:
        The mount point or raises an error.
    """
    sh_url = CFURLCreateWithString(None, share_path, None)

    # Set UI to reduced interaction
    if is_high_sierra():
        open_options = None
    else:
        open_options = {NetFS.kNAUIOptionKey: NetFS.kNAUIOptionNoUI}
    # Allow mounting sub-directories of root shares
    if is_high_sierra():
        mount_options = None
    else:
        mount_options = {NetFS.kNetFSAllowSubMountsKey: True}
    # Build our connected pointers for our results
    result, output = NetFS.NetFSMountURLSync(
        sh_url, None, None, None, open_options, mount_options, None)

    # Check if it worked
    if result != 0:
        raise Exception('Error mounting url "%s": %s' % (share_path, output))
    # Return the mountpath
    return str(output[0])


def is_high_sierra():
    version = StrictVersion(
        subprocess.check_output(['sw_vers', '-productVersion']).decode().strip())
    return version >= StrictVersion('10.13')
