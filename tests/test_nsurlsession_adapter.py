import pytest
import sys
import requests
from jss.nsurlsession_adapter import NSURLSessionAdapter, NSURLCredentialHTTPBasicAuth


@pytest.fixture
def nsurlsession_adapter():  # type: () -> NSURLSessionAdapter
    adapter = NSURLSessionAdapter()
    adapter.verify = False
    return adapter


@pytest.fixture
def nsbasicauth(jss_prefs_dict):
    return NSURLCredentialHTTPBasicAuth(jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password'])


@pytest.fixture
def session(nsurlsession_adapter):  # type: () -> requests.Session
    s = requests.Session()
    s.mount('https://', nsurlsession_adapter)
    return s


@pytest.mark.skipif(sys.platform.startswith('linux'), reason='PyObjC not present on linux')
class TestNSURLSessionAdapter(object):

    def test_get_json(self, session, jss_prefs_dict):
        # type: (requests.Session, dict) -> None

        response = session.get(
            '{}/uapi/auth'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 401
        assert response.content is not None

    def test_post_json(self, session, jss_prefs_dict):
        # type: (requests.Session, dict) -> None

        response = session.post(
            '{}/uapi/auth/tokens'.format(jss_prefs_dict['jss_url']),
            auth=(jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False,
            # force_basic_auth=True,
        )
        assert response is not None
        assert response.status_code == 200

    def test_get_xml(self, session, jss_prefs_dict, nsbasicauth):
        # type: (requests.Session, dict) -> None

        response = session.get(
            '{}/JSSResource/accounts'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'text/xml', 'Accept': 'text/xml'},
            auth=nsbasicauth,
            verify=False)
        assert response is not None
        assert response.status_code == 401
        assert response.content is not None

        print response.content
