Warning: Due to bugs in Apache's SSL code, requests can fail with an SSL
exception: 
requests.exceptions.SSLError
"error:14094410:SSL routines:SSL3_READ_BYTES:sslv3 alert handshake failure"

This doesn't seem to be a problem for single calls, but when rapidly making
multiple calls, is nearly inevitable.

The best solution I have come up with is to wrap these sorts of situations in a
while, with a try/except block to handle the exception.