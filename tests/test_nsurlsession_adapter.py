import pytest
import sys
import requests
from jss.nsurlsession_adapter import NSURLSessionAdapter

@pytest.fixture
def nsurlsession_adapter():  # type: () -> NSURLSessionAdapter
    adapter = NSURLSessionAdapter()
    adapter.verify = False
    return adapter


@pytest.fixture
def session(nsurlsession_adapter):  # type: () -> requests.Session
    s = requests.Session()
    s.mount('https://', nsurlsession_adapter)
    return s


@pytest.mark.skipif(sys.platform.startswith('linux'), reason='PyObjC not present on linux')
class TestNSURLSessionAdapter(object):

    def test_get_json(self, session, jss_prefs_dict):
        # type: (NSURLSessionAdapter, dict) -> None

        response = session.get(
            '{}/uapi/auth'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 401
