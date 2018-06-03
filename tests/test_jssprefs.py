import pytest
# import __builtin__
from jss import JSSPrefs, tools
import os.path


def mock_raw_input(prompt):
    return 'dummy'


class TestJSSPrefs(object):

    @pytest.mark.skip(reason='disabled')
    def test_configure_without_prefs(self, monkeypatch):
        # monkeypatch.setattr(__builtin__, 'raw_input', mock_raw_input)
        p = JSSPrefs()
        assert p is not None

    def test_unsupported_os(self, monkeypatch, tmpdir):
        def mock_expanduser(path):
            return tmpdir.join(path.replace('~', 'HOME'))

        monkeypatch.setattr(tools, 'is_linux', lambda x: False)
        monkeypatch.setattr(tools, 'is_osx', lambda x: False)
        monkeypatch.setattr(os.path, 'expanduser', mock_expanduser)
        
        p = JSSPrefs()
        assert p is not None

    @pytest.mark.skip(reason='todo')
    def test_user_required(self):
        pass

    @pytest.mark.skip(reason='todo')
    def test_password_required(self):
        pass

    @pytest.mark.skip(reason='todo')
    def test_url_required(self):
        pass

    