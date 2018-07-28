import pytest
import os.path
import jss
from jss import JSS, QuerySet
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

    def test_get_packages(self, j):
        result = j.Package()
        assert result is not None
        assert isinstance(result, QuerySet)

    def test_new_building(self, j, etree_building):
        fixture_building = jss.Building(j, etree_building)
        fixture_building.save()
        assert fixture_building.id is not None

    def test_get_building(self, j, etree_building):
        fixture_building = j.Building(etree_building.findtext('name'))
        assert fixture_building is not None
        assert fixture_building.id is not None

    def test_update_building(self, j, etree_building):
        fixture_building = j.Building(etree_building.findtext('name'))
        fixture_building.find('name').text = 'Updated Fixture'
        fixture_building.save()
        fixture_building.delete()

    def test_delete_building(self, j, etree_building):
        fixture_building = j.Building(etree_building.findtext('name'))
        fixture_building.delete()

    def test_scrape(self, j):
        #scrape_url = '/'
        scrape_url = 'legacy/packages.html?id=-1&o=c'
        r = j.scrape(scrape_url)
        assert r is not None