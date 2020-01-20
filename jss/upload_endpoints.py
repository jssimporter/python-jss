from __future__ import absolute_import
from .jamf_software_server import JSS

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
    def __init__(self, jss):  # type: (JSS) -> None
        self.jss = jss

    def monitor_progress(self):
        """The JAMF Pro Web UI often calls this endpoint to get upload status (to display a progress bar).
        The secondary functionality is that when the upload is finished, the payload may contain a redirect URI.
        For this reason we still need to use the endpoint to determine the upload outcome.

        The format of the response is an XML fragment, even though no Content-Type is specified.

        Example (for Push Cert .p12 upload):

            <jss>
                <javascript>nextPage</javascript>
                <status>complete</status>
                <filename>push.p12</filename>
                <sessionExpiresEpoch>1800</sessionExpiresEpoch>
            </jss>

        In this example, the `javascript` element includes a function to call.
        """
        self.jss.get('/monitorUploadProgress.ajax')

    def finalize(self):
        """POST to the legacy.html page representing the object, which confirms that the upload is complete.

        For this, it seems we need some of the hidden vars from the FORM previous:

        - session-token
        - INCLUDE_PAGE_VARIABLE (the server uses this to determine the previous step, and therefore what the current
            step requires).
        - OBJECT_RANDOM_IDENTIFIER (matches the identifier appended to the end of session_identifier)
        """
        pass


class UploadAssistant(object):
    """This class represents any assistant-style upload in the JAMF Pro UI.

    Although uploads are tracked by the `com.jamfsoftware.jss.fileupload.UploadController` there are sometimes other
    fields that must be submitted to make the database consistent.
    """
    def __init__(self, j, steps):  # type: (JSS, list) -> UploadAssistant
        self._jss = j
        self._step_index = 0
        self._steps = steps

    @property
    def step_index(self):
        return self._step_index

    @step_index.setter
    def step_index(self, v):
        self._step_index = v

    @property
    def step(self):
        return self._steps[self._step_index]


class PushNotificationKeystoreAssistant(UploadAssistant):

    FIELD_METHOD_DOWNLOAD_SIGNED_CSR = 1
    FIELD_METHOD_DOWNLOAD_CSR = 2
    FIELD_METHOD_UPLOAD_P12 = 3
    FIELD_METHOD_GET_PROXY_TOKEN = 4

    def __init__(self, j, **kwargs):
        super(UploadAssistant, self).__init__(j, [
            'pushCertificateChooseMethod.jsp',
            'pushCertificateJAMFNationLogin.jsp',
            'pushCertificateDownloadSignedCSR.jsp',
            'pushCertificateDownloadUnsignedCSR.jsp',
            'pushCertificateGenerateCSRManually.jsp',
            'pushCertificateCreateCertificate.jsp',
            'pushCertificateUploadCertificate.jsp',
            'pushCertificateUploadP12.jsp',
            'pushCertificateEnterPasswordForP12.jsp',
        ], **kwargs)

    def download_signed_csr(self, jamf_nation_username, jamf_nation_password):
        pass

    def download_csr(self):
        pass

    def upload_p12(self, path, passphrase=None):
        pass

    def get_proxy_token(self):
        pass


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


class PushNotificationKeystoreUpload(Upload):

    def __init__(self, jss):
        """Construct a PushNotificationKeystoreUpload (Upload a .p12 file as push keystore).

        Notes:

        - The sessionIdentifier is constructed like so (see WEB-INF/frontend/standardFormUpload.jsp):

                sessionIdentifier = target.getClass().getName() + ":" + target.getRandomIdentifier();

            In this case the classname becomes `com.jamfsoftware.jss.objects.pushnotification.PushNotificationKeystore`.

        - The fileIdentifier is always "Keystore" (It is hardcoded into the .jsp,
            see WEB-INF/frontend/pushCertificateUploadP12.jsp).

        - The object random identifier is generated at page load time, so we have to scrape it at least once.

        Sequence:

            - Hit `legacy/pushNotificationCertificate.html?id=-1&o=c`, which is usually in an IFRAME.
            - Scrape hidden inputs from <form name="f" id="f"> :
                - name="session-token" id="session-token"
                - name="INCLUDE_PAGE_VARIABLE" id="INCLUDE_PAGE_VARIABLE"
                - name="OBJECT_RANDOM_IDENTIFIER" id="OBJECT_RANDOM_IDENTIFIER"
            - POST all of above, with FIELD_METHOD: 3 (upload p12) and action=Next
            - POST multipart/form-data file as `importFileKeystore` to:
                - upload/?sessionIdentifier=com.jamfsoftware.jss.objects.pushnotification.PushNotificationKeystore:<randomid>&fileIdentifier=Keystore"
            - When the monitor ajax endpoint says complete, POST again to legacy/pushNotificationCertificate.html with
                the INCLUDE_PAGE_VARIABLE from the previous step.
            - Now we are entering the keystore password
            - POST the keystore password as `FIELD_UPLOADED_P12_PASSWORD` and include the INCLUDE_PAGE_VARIABLE from the
                last page. with action=Next
            - Done.

        """
        super(PushNotificationKeystoreUpload, self).__init__(jss)
        self.session_identifier = "com.jamfsoftware.jss.objects.pushnotification.PushNotificationKeystore"
        self.file_identifier = "Keystore"
        self.object_random_identifier = ""

    def finalize_p12_passphrase(self):
        """The upload of a .p12 keystore has a second phase of finalization which is to specify the passphrase.

        The passphrase is included in a form variable `FIELD_UPLOADED_P12_PASSWORD`, as well as the variables from
        the previous POST to upload:

        - session-token
        - INCLUDE_PAGE_VARIABLE
        - OBJECT_RANDOM_IDENTIFIER
        - fakeUsername (empty)
        - fakePassword (empty)
        - action = Next
        """
        pass
