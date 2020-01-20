from __future__ import absolute_import
import pytest

from jss.curl_adapter import CurlAdapter
from jss import JSS


@pytest.fixture
def curl_adapter():  # type: () -> CurlAdapter
    adapter = CurlAdapter(verify=False)
    return adapter


@pytest.fixture
def curl_jss(curl_adapter, jss_prefs_dict):  # type: (CurlAdapter, dict) -> JSS
    j = JSS(
        adapter=curl_adapter,
        url=jss_prefs_dict['jss_url'],
        user=jss_prefs_dict['jss_user'],
        password=jss_prefs_dict['jss_password'],
        ssl_verify=jss_prefs_dict['verify'],
    )
    return j


class TestCurlAdapter(object):

    def test_regression_header_values(self, curl_adapter):
        # type: (CurlAdapter) -> None

        cmd = curl_adapter._build_command('https://localhost:8444', headers=['KEY: VALUE'])
        assert any(c == 'KEY: VALUE' for c in cmd)

    def test_get_xml(self, curl_adapter, jss_prefs_dict):
        # type: (CurlAdapter, dict) -> None

        response = curl_adapter.get(
            '{}/JSSResource/accounts'.format(jss_prefs_dict['jss_url']),
        )
        assert response is not None
        assert response.status_code == 401

    def test_get_json(self, curl_adapter, jss_prefs_dict):
        # type: (CurlAdapter, dict) -> None

        response = curl_adapter.get(
            '{}/uapi/auth'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        assert response is not None
        assert response.status_code == 401

    def test_get_jss(self, curl_jss):
        # type: (JSS) -> None
        
        accounts = curl_jss.Account()
        assert accounts is not None

