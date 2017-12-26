import pytest
import __builtin__
from jss import JSSPrefs, tools


def mock_raw_input(prompt):
    return 'dummy'


class TestJSSPrefs(object):

    def test_configure_without_prefs(self, monkeypatch):
        monkeypatch.setattr(__builtin__, 'raw_input', mock_raw_input)
        p = JSSPrefs()

    def test_unsupported_os(self, monkeypatch):
        monkeypatch.setattr(tools, 'is_linux', lambda x: False)
        monkeypatch.setattr(tools, 'is_osx', lambda x: False)
        p = JSSPrefs()

    def test_user_required(self):
        pass

    def test_password_required(self):
        pass

    def test_url_required(self):
        pass

    