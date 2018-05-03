import pytest
from jss import JSS
from UserDict import UserDict


class TestUAPIObjects(object):

    def test_get_cache(self, j):
        # type: (JSS) -> None
        result = j.Cache()
        assert result is not None
        assert isinstance(result, UserDict)

    def test_get_ebook(self, j):
        # type: (JSS) -> None
        result = j.UAPIEbook()
        assert result is not None
        assert isinstance(result, list)

    def test_get_notifications(self, j):
        # type: (JSS) -> None
        result = j.AlertNotification()
        assert result is not None
        assert isinstance(result, list)
