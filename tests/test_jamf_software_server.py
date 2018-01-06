import pytest
import os.path
from jss import JSS
from xml.etree import ElementTree
from jss.exceptions import GetError


def mock_expanduser(path):
    return path


class TestJSS(object):

    def test_construct_without_jssprefs(self, jss_prefs_dict):
        j = JSS(url=jss_prefs_dict['jss_url'], user=jss_prefs_dict['jss_user'], password=jss_prefs_dict['jss_password'])
        assert j is not None

    def test_construct_with_jssprefs(self, jss_prefs, monkeypatch, tmpdir):
        def mock_expanduser(path):
            return tmpdir.join(path.replace('~', 'HOME'))

        monkeypatch.setattr(os.path, 'expanduser', mock_expanduser)
        # monkeypatch.setattr(os.path, 'startswith', lambda p: False)
        j = JSS(jss_prefs=jss_prefs)
        assert j is not None

    def test_trailing_slash_removed(self, jss_prefs_dict):
        j = JSS(url=jss_prefs_dict['jss_url']+'/')
        assert j.base_url[-1] != '/'

    def test_get(self, j):
        result = j.get('packages')
        assert result is not None
        assert isinstance(result, ElementTree.Element)

    def test_post(self, j, etree_building):
        new_id = j.post('buildings/id/0', data=etree_building)
        assert new_id is not None
        result = j.get('buildings/id/{}'.format(new_id))
        assert result is not None
        assert isinstance(result, ElementTree.Element)

    def test_put(self, j, etree_building):
        etree_building.find('name').text = 'UpdatedFixture'
        j.put('buildings/name/Fixture', data=etree_building)
        result = j.get('buildings/name/UpdatedFixture')
        assert result is not None
        assert isinstance(result, ElementTree.Element)

    def test_delete(self, j):
        j.delete('buildings/name/UpdatedFixture')

        with pytest.raises(GetError):
            result = j.get('buildings/name/UpdatedFixture')
            assert result is None

    def test_scrape(self, j):
        r = j.scrape('legacy/cloudDistributionPoint.html?id=0&o=r')
        assert r is not None