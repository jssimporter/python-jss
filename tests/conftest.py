import pytest
import plistlib
from jss import JSSPrefs, JSS
from xml.etree import ElementTree
from jss.requests_adapter import RequestsAdapter
from jss.gurl_adapter import GurlAdapter

JSS_PREFS = {
    'jss_url': 'https://localhost:8444',
    'jss_user': 'admin',
    'jss_password': 'passw0rd',
    'verify': False,
    'suppress_warnings': False,
    'repos': [],
}


@pytest.fixture
def jss_prefs_dict():  # () -> dict
    return JSS_PREFS


@pytest.fixture
def jss_prefs_file(tmpdir):  # () -> str
    prefs_path = tmpdir.join('com.github.sheagcraig.python-jss.plist')
    plistlib.writePlist(JSS_PREFS, prefs_path)
    return prefs_path


@pytest.fixture
def jss_prefs(jss_prefs_file):  # (str) -> JSSPrefs
    prefs = JSSPrefs(preferences_file=jss_prefs_file)
    return prefs


@pytest.fixture
def j(jss_prefs_dict):  # (dict) -> JSS
    o = JSS(
        url=jss_prefs_dict['jss_url'],
        user=jss_prefs_dict['jss_user'],
        password=jss_prefs_dict['jss_password'],
        ssl_verify=jss_prefs_dict['verify'],
    )
    return o


@pytest.fixture
def jrequests(jss_prefs_dict):  # (dict) -> JSS
    o = JSS(
        url=jss_prefs_dict['jss_url'],
        user=jss_prefs_dict['jss_user'],
        password=jss_prefs_dict['jss_password'],
        ssl_verify=jss_prefs_dict['verify'],
        adapter=RequestsAdapter(jss_prefs_dict['jss_url']),
    )
    return o


@pytest.fixture
def gurl_adapter():  # () -> GurlAdapter
    adapter = GurlAdapter()
    return adapter


@pytest.fixture
def requests_adapter(jss_prefs_dict):  # () -> RequestsAdapter
    adapter = RequestsAdapter(jss_prefs_dict['jss_url'])
    return adapter

@pytest.fixture
def etree_building():  # () -> ElementTree.Element
    building = ElementTree.Element('building')
    name = ElementTree.SubElement(building, 'name')
    name.text = 'Fixture'
    
    return building