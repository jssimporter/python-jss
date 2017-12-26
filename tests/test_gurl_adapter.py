import pytest
from jss.gurl_adapter import GurlAdapter
from jss import JSS, Building
from xml.etree import ElementTree


@pytest.fixture
def gurl_jss(gurl_adapter, jss_prefs_dict):  # type: (GurlAdapter, dict) -> JSS
    j = JSS(
        adapter=gurl_adapter,
        url=jss_prefs_dict['jss_url'],
        user=jss_prefs_dict['jss_user'],
        password=jss_prefs_dict['jss_password'],
        ssl_verify=jss_prefs_dict['verify'],
    )
    return j


class TestGurlAdapter(object):

    def test_get(self, gurl_adapter, jss_prefs_dict):
        # type: (GurlAdapter, dict) -> None

        response = gurl_adapter.get(
            '{}/uapi/auth'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 401

    def test_post(self, gurl_adapter, jss_prefs_dict):
        # type: (GurlAdapter, dict) -> None

        response = gurl_adapter.post(
            '{}/uapi/auth/tokens'.format(jss_prefs_dict['jss_url']),
            auth=(jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False,
            force_basic_auth=True,
        )
        assert response is not None
        assert response.status_code == 200

    def test_post_xml(self, gurl_adapter, jss_prefs_dict, etree_building):
        # type: (GurlAdapter, dict, ElementTree.Element) -> None
        
        response = gurl_adapter.post(
            '{}/JSSResource/buildings/id/0'.format(jss_prefs_dict['jss_url']),
            auth=(jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password']),
            headers={'Content-Type': 'text/xml', 'Accept': 'text/xml'},
            verify=False,
            data=ElementTree.tostring(etree_building),
        )
        assert response is not None
        assert response.status_code == 200

    def test_post_jss(self, gurl_jss, etree_building):
        b = Building(jss=gurl_jss, data=etree_building)
        b.save()
