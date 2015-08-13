#!/usr/bin/python
#
# Copyright (C) 2015 Michael Lynn
# https://gist.github.com/pudquick/1362a8908be01e23041d
# https://michaellynn.github.io/2015/08/08/learn-you-a-better-pyobjc-bridgesupport-signature/

"""mount_shares_better.py

Mount file shares on OS X.
"""


import CoreFoundation
import Foundation
import objc


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


NetFS = AttrDict()
# Can cheat and provide 'None' for the identifier, it'll just use
# frameworkPath instead.
# scan_classes=False means only add the contents of this Framework.
NetFS_bundle = objc.initFrameworkWrapper(
    'NetFS', frameworkIdentifier=None,
    frameworkPath=objc.pathForFramework('NetFS.framework'), globals=NetFS,
    scan_classes=False)

# https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/ObjCRuntimeGuide/Articles/ocrtTypeEncodings.html
# Fix NetFSMountURLSync signature
del NetFS['NetFSMountURLSync']
objc.loadBundleFunctions(NetFS_bundle, NetFS,
                         [('NetFSMountURLSync', 'i@@@@@@o^@')])


def mount_share(share_path):
    """Mounts a share at /Volumes

    Args:
        share_path: String URL with all auth info to connect to file share.

    Returns:
        The mount point or raises an error.
    """
    sh_url = CoreFoundation.CFURLCreateWithString(None, share_path, None)
    # Set UI to reduced interaction
    open_options  = {NetFS.kNAUIOptionKey: NetFS.kNAUIOptionNoUI}
    # Allow mounting sub-directories of root shares
    mount_options = {NetFS.kNetFSAllowSubMountsKey: True}
    # Build our connected pointers for our results
    result, output = NetFS.NetFSMountURLSync(sh_url, None, None, None,
                                             open_options, mount_options, None)
    # Check if it worked
    if result != 0:
         raise Exception('Error mounting url "%s": %s' % (share_path, output))
    # Return the mountpath
    return str(output[0])
