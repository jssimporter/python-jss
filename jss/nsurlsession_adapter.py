"""nsurlsession_adapter.py

Requests API transport that uses NSURLSession and friends via PyObjC 2.1 that ships with macOS.

Much of this code was copied, rewritten, or inspired by gurl.py from the munki project.
Thanks to Greg Neagle and frogor, amongst many other contributors.
"""
from __future__ import absolute_import
import logging
import os
import io
from requests.adapters import BaseAdapter
from requests.models import Response, PreparedRequest, Request
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers
from requests.auth import AuthBase, HTTPBasicAuth
from requests.cookies import RequestsCookieJar
from requests.exceptions import SSLError
# from cookielib import Cookie

import objc
from Foundation import NSObject, NSMutableURLRequest, NSURL, NSURLRequestUseProtocolCachePolicy, \
    NSURLRequestReloadIgnoringLocalCacheData, NSURLRequestReturnCacheDataElseLoad, \
    NSURLSessionConfiguration, NSURLSession, NSOperationQueue, NSURLCredential, \
    NSURLCredentialPersistenceNone, NSRunLoop, NSDate, NSURLResponseUnknownLength, \
    NSURLAuthenticationMethodServerTrust, NSMutableData, NSBundle


# These headers are reserved to the NSURLSession and should not be set by
# Requests, though we may use them.
_RESERVED_HEADERS = set([
    'connection', 'host', 'proxy-authenticate', 'authorization',
    'proxy-authorization', 'www-authenticate',
])

# NSURLSessionAuthChallengeDisposition enum constants
NSURLSessionAuthChallengeUseCredential = 0
NSURLSessionAuthChallengePerformDefaultHandling = 1
NSURLSessionAuthChallengeCancelAuthenticationChallenge = 2
NSURLSessionAuthChallengeRejectProtectionSpace = 3

# NSURLSessionResponseDisposition enum constants
NSURLSessionResponseCancel = 0
NSURLSessionResponseAllow = 1
NSURLSessionResponseBecomeDownload = 2

# TLS/SSLProtocol enum constants
kSSLProtocolUnknown = 0
kSSLProtocol3 = 2
kTLSProtocol1 = 4
kTLSProtocol11 = 7
kTLSProtocol12 = 8
kDTLSProtocol1 = 9

ssl_error_codes = {
    -9800: u'SSL protocol error',
    -9801: u'Cipher Suite negotiation failure',
    -9802: u'Fatal alert',
    -9803: u'I/O would block (not fatal)',
    -9804: u'Attempt to restore an unknown session',
    -9805: u'Connection closed gracefully',
    -9806: u'Connection closed via error',
    -9807: u'Invalid certificate chain',
    -9808: u'Bad certificate format',
    -9809: u'Underlying cryptographic error',
    -9810: u'Internal error',
    -9811: u'Module attach failure',
    -9812: u'Valid cert chain, untrusted root',
    -9813: u'Cert chain not verified by root',
    -9814: u'Chain had an expired cert',
    -9815: u'Chain had a cert not yet valid',
    -9816: u'Server closed session with no notification',
    -9817: u'Insufficient buffer provided',
    -9818: u'Bad SSLCipherSuite',
    -9819: u'Unexpected message received',
    -9820: u'Bad MAC',
    -9821: u'Decryption failed',
    -9822: u'Record overflow',
    -9823: u'Decompression failure',
    -9824: u'Handshake failure',
    -9825: u'Misc. bad certificate',
    -9826: u'Bad unsupported cert format',
    -9827: u'Certificate revoked',
    -9828: u'Certificate expired',
    -9829: u'Unknown certificate',
    -9830: u'Illegal parameter',
    -9831: u'Unknown Cert Authority',
    -9832: u'Access denied',
    -9833: u'Decoding error',
    -9834: u'Decryption error',
    -9835: u'Export restriction',
    -9836: u'Bad protocol version',
    -9837: u'Insufficient security',
    -9838: u'Internal error',
    -9839: u'User canceled',
    -9840: u'No renegotiation allowed',
    -9841: u'Peer cert is valid, or was ignored if verification disabled',
    -9842: u'Server has requested a client cert',
    -9843: u'Peer host name mismatch',
    -9844: u'Peer dropped connection before responding',
    -9845: u'Decryption failure',
    -9846: u'Bad MAC',
    -9847: u'Record overflow',
    -9848: u'Configuration error',
    -9849: u'Unexpected (skipped) record in DTLS'}

# define a helper function for block callbacks
import ctypes
import objc
_objc_so = ctypes.cdll.LoadLibrary(
    os.path.join(objc.__path__[0], '_objc.so'))
PyObjCMethodSignature_WithMetaData = (
    _objc_so.PyObjCMethodSignature_WithMetaData)
PyObjCMethodSignature_WithMetaData.restype = ctypes.py_object


def objc_method_signature(signature_str):
    """Return a PyObjCMethodSignature given a call signature in string
    format"""
    return PyObjCMethodSignature_WithMetaData(
        ctypes.create_string_buffer(signature_str), None, False)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# ATS hack stolen from gurl.py
# disturbing hack warning!
# this works around an issue with App Transport Security on 10.11
bundle = NSBundle.mainBundle()
info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
info['NSAppTransportSecurity'] = {'NSAllowsArbitraryLoads': True}


def build_request(request, timeout):
    # type: (PreparedRequest, Union[float, Tuple[float, float]]) -> NSMutableURLRequest
    """Convert a requests `PreparedRequest` into a suitable NSMutableURLRequest."""

    timeout = timeout if timeout else 0.0

    nsrequest = NSMutableURLRequest.requestWithURL_cachePolicy_timeoutInterval_(
        NSURL.URLWithString_(request.url),
        NSURLRequestReloadIgnoringLocalCacheData,
        timeout,
    )
    nsrequest.setHTTPMethod_(request.method)

    for k, v in request.headers.items():
        k, v = k.lower(), v.lower()

        if k in _RESERVED_HEADERS:
            logging.debug('Ignoring reserved header: %s', k)
            continue

        nsrequest.setValue_forHTTPHeaderField_(v, k)

    return nsrequest


def build_response(req, delegate, cookiestore):
    # type: (PreparedRequest, NSURLSessionAdapterDelegate, NSHTTPCookieStorage) -> Response
    """Build a requests `Response` object from the response data collected by the NSURLSessionDelegate, and the
    default cookie store."""

    response = Response()

    # Fallback to None if there's no status_code, for whatever reason.
    response.status_code = getattr(delegate, 'status', None)

    # Make headers case-insensitive.
    response.headers = CaseInsensitiveDict(getattr(delegate, 'headers', {}))

    # Set encoding.
    response.encoding = get_encoding_from_headers(response.headers)
    # response.raw = resp
    # response.reason = response.raw.reason

    if isinstance(req.url, bytes):
        response.url = req.url.decode('utf-8')
    else:
        response.url = req.url

    # Add new cookies from the server. For NSURLSession these have already been parsed.
    # jar = RequestsCookieJar()
    # for cookie in cookiestore.cookies():
    #     print cookie
    #     c = Cookie(
    #         version=cookie.version(),
    #         name=cookie.name(),
    #         value=cookie.value(),
    #         port=8444,
    #         # port=cookie.portList()[-1],
    #         port_specified=0,
    #         domain=cookie.domain(),
    #         domain_specified=cookie.domain(),
    #         domain_initial_dot=cookie.domain(),
    #         path=cookie.path(),
    #         path_specified=cookie.path(),
    #         secure=!cookie.HTTPOnly(),
    #         expires=cookie.expiresDate(),
    #         comment=cookie.comment(),
    #         comment_url=cookie.commentURL(),
    #     )
    #     jar.set_cookie(c)
    #
    # response.cookies = jar

    response.raw = io.BytesIO(buffer(delegate.output))

    # Give the Response some context.
    response.request = req
    # response.connection = self

    return response


class NSURLCredentialAuth(AuthBase):
    """HTTP Basic Authentication for NSURLSessionAdapter.

    It isn't possible to use the requests built-in HTTPBasicAuth adapter because it adds headers, which doesn't really
    gel with NSURLSession's delegate challenge methods."""

    def __init__(self, username, password):  # type: (str, str) -> None
        self.username = username
        self.password = password
        self.credential = None

    def __eq__(self, other):  # type: (Any) -> bool
        return all([
            self.username == getattr(other, 'username', None),
            self.password == getattr(other, 'password', None)
        ])

    def __ne__(self, other):  # type: (Any) -> bool
        return not self == other

    def __call__(self, r):  # type: (PreparedRequest) -> PreparedRequest
        """Instead of modifying the request object, we construct an instance of NSURLCredential to attach to ourselves.

        When the delegate detects that attribute is present, it uses it whenever a challenge comes in."""
        credential = NSURLCredential.credentialWithUser_password_persistence_(
            self.username, self.password,
            NSURLCredentialPersistenceNone  # we don't expect ephemeral requests to save keychain items.
        )
        self.credential = credential

        return r


class NSURLSessionAdapterDelegate(NSObject):
    """NSURLSessionAdapterDelegate implements the delegate methods of NSURLSession protocols such as:

    - `NSURLSessionDelegate <https://developer.apple.com/documentation/foundation/nsurlsessiondelegate?language=objc>`_.
    - `NSURLSessionTaskDelegate <https://developer.apple.com/documentation/foundation/nsurlsessiontaskdelegate?language=objc>`_.
    - `NSURLSessionDataDelegate <https://developer.apple.com/documentation/foundation/nsurlsessiondatadelegate?language=objc>`_.
    """

    def initWithAdapter_(self, adapter):
        self = objc.super(NSURLSessionAdapterDelegate, self).init()

        if self is None:
            return None

        self.adapter = adapter
        self.bytesReceived = 0
        self.expectedLength = -1
        self.percentComplete = 0
        self.done = False
        self.error = None
        self.SSLError = None
        self.output = NSMutableData.dataWithCapacity_(1024)
        self.status = None
        self.headers = {}
        self.verify = True
        self.credential = None
        self.history = []

        return self

    def isDone(self):  # () -> bool
        """Check if the connection request is complete. As a side effect,
        allow the delegates to work by letting the run loop run for a bit"""
        if self.done:
            return self.done
        # let the delegates do their thing
        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(.1))
        return self.done

    def URLSession_dataTask_didReceiveResponse_completionHandler_(
            self,
            session,           # type: NSURLSession
            task,              # type: NSURLSessionDataTask
            response,          # type: NSHTTPURLResponse
            completionHandler  # type: (NSURLSessionResponseDisposition) -> Void
    ):  # type: (...) -> None
        logger.debug('URLSession_dataTask_didReceiveResponse_completionHandler_')
        completionHandler.__block_signature__ = objc_method_signature('v@i')
        
        self.response = response
        self.bytesReceived = 0
        self.percentComplete = -1
        self.expectedLength = response.expectedContentLength()

        if response.className() == u'NSHTTPURLResponse':
            # Headers and status code only available for HTTP/S transfers
            self.status = response.statusCode()
            self.headers = dict(response.allHeaderFields())

        self.done = True

        if completionHandler:  # tell the session task to continue
            completionHandler(NSURLSessionResponseAllow)

    def URLSession_dataTask_didReceiveData_(
            self,
            session,  # type: NSURLSession
            task,     # type: NSURLSessionDataTask
            data      # type: NSData
    ):  # type: (...) -> None
        logger.debug('URLSession_dataTask_didReceiveData_ (%d bytes)', len(data))

        self.output.appendData_(data)
        self.bytesReceived += len(data)
        if self.expectedLength != NSURLResponseUnknownLength:
            self.percentComplete = int(
                float(self.bytesReceived)/float(self.expectedLength) * 100.0)

    # - NSURLSessionTaskDelegate

    def URLSession_task_didReceiveChallenge_completionHandler_(
            self,
            session,          # type: NSURLSession
            task,             # type: NSURLSessionTask
            challenge,        # type: NSURLAuthenticationChallenge
            completionHandler # type: (NSURLSessionAuthChallengeDisposition, NSURLCredential) -> Void
    ):  # type: (...) -> None
        logger.debug('URLSession_task_didReceiveChallenge_completionHandler_')
        completionHandler.__block_signature__ = objc_method_signature('v@i@')
        
        protectionSpace = challenge.protectionSpace()
        host = protectionSpace.host()
        realm = protectionSpace.realm()
        authenticationMethod = protectionSpace.authenticationMethod()

        logger.debug('NSURLProtectionSpace host: %s, realm: %s, method: %s', host,
                     realm, authenticationMethod)

        if authenticationMethod == 'NSURLAuthenticationMethodServerTrust' and not self.verify:
            logger.debug('Trusting invalid SSL certificate because verify=False')
            trust = protectionSpace.serverTrust()
            credential = NSURLCredential.credentialForTrust_(trust)
            completionHandler(
                NSURLSessionAuthChallengePerformDefaultHandling, credential)
        elif authenticationMethod in ['NSURLAuthenticationMethodDefault',
                                      'NSURLAuthenticationMethodHTTPBasic',
                                      'NSURLAuthenticationMethodHTTPDigest']:
            logger.debug('Attempting to authenticate')
            if getattr(self, 'credential', None) is not None:
                logger.debug('Using supplied NSURLCredential')
                completionHandler(
                    NSURLSessionAuthChallengeUseCredential, self.credential)
            else:
                logger.debug('No NSURLCredential available, not authenticating.')
                completionHandler(NSURLSessionAuthChallengePerformDefaultHandling, None)
        else:
            completionHandler(
                NSURLSessionAuthChallengePerformDefaultHandling, None)

    def URLSession_task_didCompleteWithError_(
            self,
            session,    # type: NSURLSession
            task,       # type: NSURLSessionTask
            error       # type: NSError
    ):  # type: (...) -> None
        logger.debug('URLSession_task_didCompleteWithError_')
        if error:
            self.error = error
            # If this was an SSL error, try to extract the SSL error code.
            if 'NSUnderlyingError' in error.userInfo():
                ssl_code = error.userInfo()['NSUnderlyingError'].userInfo().get(
                    '_kCFNetworkCFStreamSSLErrorOriginalValue', None)
                if ssl_code:
                    self.SSLError = (ssl_code, ssl_error_codes.get(
                        ssl_code, 'Unknown SSL error'))
        else:
            logger.debug('no error(s)')

        self.done = True

    def URLSession_task_willPerformHTTPRedirection_newRequest_completionHandler_(
            self,
            session,           # type: NSURLSession
            task,              # type: NSURLSessionTask
            response,          # type: NSHTTPURLResponse
            request,           # type: NSURLRequest
            completionHandler  # type: (NSURLRequest) -> None
    ):
        """This method copied largely from gurl.py"""
        # we don't actually use the session or task arguments, so
        # pylint: disable=W0613
        logger.debug('URLSession_task_willPerformHTTPRedirection_newRequest_')
        completionHandler.__block_signature__ = objc_method_signature('v@@')

        if response is None:
            # the request has changed the NSURLRequest in order to standardize
            # its format, for example, changing a request for
            # http://www.apple.com to http://www.apple.com/. This occurs because
            # the standardized, or canonical, version of the request is used for
            # cache management. Pass the request back as-is
            # (it appears that at some point Apple also defined a redirect like
            # http://developer.apple.com to https://developer.apple.com to be
            # 'merely' a change in the canonical URL.)
            # Further -- it appears that this delegate method isn't called at
            # all in this scenario, unlike NSConnectionDelegate method
            # connection:willSendRequest:redirectResponse:
            # we'll leave this here anyway in case we're wrong about that
            if completionHandler:
                completionHandler(request)
                return
            else:
                return request

        # If we get here, it appears to be a real redirect attempt
        # Annoyingly, we apparently can't get access to the headers from the
        # site that told us to redirect. All we know is that we were told
        # to redirect and where the new location is.
        newURL = request.URL().absoluteString()

        logging.debug('Being redirected to: %s' % newURL)
        # self.history.append()
        completionHandler(request)


class NSURLSessionAdapter(BaseAdapter):

    def __init__(self, credential=None, force_basic=False):
        # type: (Optional[NSURLCredential], bool) -> None
        """NSURLSessionAdapter implements a requests adapter using PyObjC + NSURLSession.

        Because of the way the delegate deals with authentication, we cannot support requests style auth which may only
        act on the content of the request. For NSURLSessionAdapter you should use NSURLCredentialAuth, which supplies an
        NSURLCredential object whenever authentication is required by the remote host.

        :param credential: NSURLCredential that will be used if the server requests basic auth.
        :param force_basic: Force basic authentication to be used for every request by preparing the Authorization
            header. This is sometimes required because NSURLSession only checks with the delegate for credentials when
            the server sends a "challenge". Some web services never even send a challenge.
        """
        super(NSURLSessionAdapter, self).__init__()

        self.verify = True
        self.credential = credential
        self.force_basic = force_basic
        self.configuration = None
        self.delegate = None
        self.session = None

    def send(
            self,
            request,       # type: PreparedRequest
            stream=False,  # type: bool
            timeout=None,  # type: Union[float, Tuple[float, float]]
            verify=True,   # type: bool
            cert=None,     # type: Any
            proxies=None   # type: dict
        ):
        # type: (...) -> Response

        self.configuration = NSURLSessionConfiguration.ephemeralSessionConfiguration()
        self.delegate = NSURLSessionAdapterDelegate.alloc().initWithAdapter_(self)
        self.delegate.credential = self.credential
        self.session = NSURLSession.sessionWithConfiguration_delegate_delegateQueue_(
            self.configuration,
            self.delegate,
            None,
        )

        nsrequest = build_request(request, timeout)
        self.verify = verify

        # TODO: Support all of this stuff.
        assert not stream
        assert not cert
        assert not proxies

        if request.method in ['PUT', 'POST'] and request.body is not None:
            # These verbs should usually be an upload task to send the correct request headers.
            task = self.session.uploadTaskWithRequest_fromData_(nsrequest, buffer(request.body))
        else:
            task = self.session.dataTaskWithRequest_(nsrequest)

        cookiestore = self.configuration.HTTPCookieStorage()

        task.resume()

        while not self.delegate.isDone():
            pass

        response = build_response(request, self.delegate, cookiestore)

        # if self.delegate.error is not None:
        #     raise self.delegate.error

        if self.delegate.SSLError is not None:
            code, message = self.delegate.SSLError
            raise SSLError('{}: {}'.format(code, message), response=response, request=request)

        return response
