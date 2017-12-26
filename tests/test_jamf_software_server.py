import pytest
import os.path
from jss import JSS


def mock_expanduser(path):
    return path


class TestJSS(object):

    def test_construct_without_jssprefs(self, jss_prefs_dict):
        j = JSS(url=jss_prefs_dict['jss_url'], user=jss_prefs_dict['jss_user'], password=jss_prefs_dict['jss_password'])
        assert j is not None

    def test_construct_with_jssprefs(self, jss_prefs, monkeypatch):
        monkeypatch.setattr(os.path, 'expanduser', lambda x: x)
        j = JSS(jss_prefs=jss_prefs)
        assert j is not None

    def test_trailing_slash_removed(self, jss_prefs_dict):
        j = JSS(url=jss_prefs_dict['jss_url']+'/')
        assert j.base_url[-1] != '/'

    def test_get(self, j):
        j.get('/JSSResource')

    def test_post(self, j):
        j.post('/JSSResource')

    def test_put(self, j):
        j.put('/JSSResource')

    def test_delete(self, j):
        j.delete('/JSSResource')

