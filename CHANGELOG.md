### 0.2.1 (Unreleased)

ADDITIONS:

- Adds TemplateFromFile and TemplateFromString objects for using external template files and strings. 
- Adds batch_scope feature to jss_helper.

CHANGES:

- Added requests and FoundationPlist to contrib folder of package. No longer need separate installation.

FIXES:

- Should not see SSL handshake errors now. JSS object now has a requests.Session object which prevents having to continually renegotiate. Bonus: It seems to be significantly faster as a result.

### 0.2.0 (June 18, 2014)

FEATURES:

- Initial release.