
UPLOAD_TYPE_MAC_PROFILE = 4
UPLOAD_TYPE_IOS_PROFILE = 22


class Upload(object):
    """This type of object represents all transfers carried out by the
    FrontEndUploadController (com.jamfsoftware.jss.fileupload.UploadController).

    These types of upload usually require the following:

    - A file identifier to indicate what type of file is being uploaded. This is a number corresponding to some kind
        of internal enum.
    - A session token, which is used as a CSRF token for each upload.
    - Request data is posted to /upload/?sessionIdentifier=&fileIdentifier=&session-token=
    - The response is an empty body (200).
    - The ajax call to monitorUploadProgress.ajax receives a redirect URL when the upload is finished.
    - The redirected URL must be saved to persist the upload.
    """
    def __init__(self, jss):
        self.jss = jss


class MacOSConfigurationProfileUpload(Upload):
    """This object represents a direct upload of a macOS configuration profile to the web ui.

    Use this to upload signed profiles directly into the JPS.
    """

    def __init__(self, jss):
        super(MacOSConfigurationProfileUpload, self).__init__(jss)
        self.session_identifier = "UPLOAD_FROM_LIST"
        self.file_identifier = UPLOAD_TYPE_MAC_PROFILE


class IOSConfigurationProfileUpload(Upload):

    def __init__(self, jss):
        super(IOSConfigurationProfileUpload, self).__init__(jss)
        self.session_identifier = "UPLOAD_FROM_LIST"
        self.file_identifier = UPLOAD_TYPE_IOS_PROFILE
