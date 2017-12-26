import pytest
from jss.gurl_adapter import GurlAdapter


class TestGurlAdapter(object):

    def test_get(self, gurl_adapter, jss_prefs_dict):  # type: (GurlAdapter, dict) -> None
        response = gurl_adapter.get(
            '{}/uapi/auth'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 401

    def test_post(self, gurl_adapter, jss_prefs_dict):  # type: (GurlAdapter, dict) -> None
        response = gurl_adapter.post(
            '{}/uapi/auth/tokens'.format(jss_prefs_dict['jss_url']),
            auth=(jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 200
