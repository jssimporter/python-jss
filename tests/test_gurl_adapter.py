import pytest
from jss.gurl_adapter import GurlAdapter
from jss import JSS, Building
from xml.etree import ElementTree

XML_DOC = '<?xml version="1.0" encoding="UTF-8"?>'


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

    def test_get_json(self, gurl_adapter, jss_prefs_dict):
        # type: (GurlAdapter, dict) -> None

        response = gurl_adapter.get(
            '{}/uapi/auth'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            verify=False)
        assert response is not None
        assert response.status_code == 401

    def test_post_json(self, gurl_adapter, jss_prefs_dict):
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
            data=ElementTree.tostring(etree_building, encoding='utf8'),
        )
        assert response is not None
        assert response.status_code == 200

    def test_get_jss(self, gurl_jss):
        # type: (JSS) -> None
        accounts = gurl_jss.Account()
        assert accounts is not None
        
    def test_post_jss(self, gurl_jss):
        # type: (JSS) -> None
        
        b = Building(gurl_jss, 'Test Building')
        b.save()
        assert b.id is not None
        b.delete()

    def test_put_jss(self, gurl_jss):
        # type: (JSS) -> None

        cc = gurl_jss.ComputerCheckIn()
        assert cc is not None
        cc.find('log_startup_event').text = "true"
        cc.save()
        assert cc.findtext('log_startup_event') == "true"

    def test_delete_jss(self, gurl_jss):
        # type: (JSS) -> None
        pass