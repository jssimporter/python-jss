from __future__ import print_function

import pytest
import sys
import requests
from xml.etree import ElementTree
try:
    from jss.nsurlsession_adapter import NSURLSessionAdapter, NSURLCredentialAuth
    from Foundation import NSURLCredential, NSURLCredentialPersistenceNone
except ImportError:
    pass

from jss import JSS, QuerySet
from jss.exceptions import GetError



@pytest.fixture
def credential(jss_prefs_dict):
    credential = NSURLCredential.credentialWithUser_password_persistence_(
        jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password'],
        NSURLCredentialPersistenceNone  # we don't expect ephemeral requests to save keychain items.
    )
    return credential


@pytest.fixture
def nsurlsession_adapter(credential):  # type: () -> NSURLSessionAdapter
    adapter = NSURLSessionAdapter(credential=credential)
    adapter.verify = False
    return adapter


@pytest.fixture
def ns_auth_provider(jss_prefs_dict):
    return NSURLCredentialAuth(jss_prefs_dict['jss_user'], jss_prefs_dict['jss_password'])


@pytest.fixture
def session(nsurlsession_adapter):  # type: () -> requests.Session
    s = requests.Session()
    s.mount('https://', nsurlsession_adapter)
    s.mount('http://', nsurlsession_adapter)
    return s


@pytest.fixture
def ns_jss(session, jss_prefs_dict):
    o = JSS(
        url=jss_prefs_dict['jss_url'],
        user=jss_prefs_dict['jss_user'],
        password=jss_prefs_dict['jss_password'],
        ssl_verify=jss_prefs_dict['verify'],
        adapter=session,
    )
    return o


@pytest.mark.skipif(sys.platform.startswith('linux'), reason='PyObjC not present on linux')
@pytest.mark.macos
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

    def test_get_xml(self, session, jss_prefs_dict, credential):
        # type: (requests.Session, dict, NSURLCredentialAuth) -> None
        response = session.get(
            '{}/JSSResource/accounts'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'text/xml', 'Accept': 'text/xml'},
            # auth=credentials,
            verify=False)
        assert response is not None
        assert response.status_code == 200
        assert response.content is not None

        print(response.content)

    def test_post_xml(self, session, jss_prefs_dict, etree_building):
        # type: (requests.Session, dict, ElementTree.Element) -> None
        response = session.post(
            '{}/JSSResource/buildings/id/0'.format(jss_prefs_dict['jss_url']),
            headers={'Content-Type': 'text/xml', 'Accept': 'text/xml'},
            data=ElementTree.tostring(etree_building, encoding='utf8'),
            verify=False)
        assert response is not None
        assert response.status_code == 201
        assert response.content is not None

        print(response.content)

    def test_delete_xml(self, session, jss_prefs_dict, etree_building):
        # type: (requests.Session, dict, ElementTree.Element) -> None
        response = session.delete(
            '{}/JSSResource/buildings/name/{}'.format(jss_prefs_dict['jss_url'], etree_building.findtext('name')),
            headers={'Content-Type': 'text/xml', 'Accept': 'text/xml'},
            verify=False)
        assert response is not None
        assert response.status_code == 200
        assert response.content is not None

        print(response.content)

    def test_get_jss(self, ns_jss):
        # type: (JSS) -> None
        result = ns_jss.Package()
        assert result is not None
        assert isinstance(result, QuerySet)

    def test_post_jss(self, ns_jss, etree_building):
        # type: (JSS, ElementTree.Element) -> None
        fixture_building = ns_jss.Building(etree_building)
        fixture_building.save()

    def test_put_jss(self, ns_jss, etree_building):
        # type: (JSS, ElementTree.Element) -> None
        fixture_building = ns_jss.Building(etree_building.findtext('name'))
        fixture_building.find('name').text = 'Updated Fixture'
        fixture_building.save()

    def test_delete_jss(self, ns_jss, etree_building):
        # type: (JSS, ElementTree.Element) -> None
        fixture_building = ns_jss.Building(etree_building.findtext('name'))
        fixture_building.delete()
