import pytest


class TestRequestsAdapter(object):

    def test_get(self, requests_adapter, jss_prefs_dict):  # (RequestsAdapter, dict) -> Void
        response = requests_adapter.get(
            '{}/uapi/auth'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 401

    def test_post(self, requests_adapter, jss_prefs_dict):  # (RequestsAdapter, dict) -> Void
        response = requests_adapter.post(
            '{}/uapi/auth/tokens'.format(jss_prefs_dict['jss_url']),
            auth=(jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 200


