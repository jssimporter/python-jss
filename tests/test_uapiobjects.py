import pytest
from jss import JSS
from UserDict import UserDict


class TestUAPIObjects(object):

    def test_get_cache(self, j):
        # type: (JSS) -> None
        result = j.uapi.Cache()
        assert result is not None
        assert isinstance(result, UserDict)

    def test_get_ebook(self, j):
        # type: (JSS) -> None
        result = j.uapi.Ebook()
        assert result is not None
        assert isinstance(result, list)

    def test_get_notifications(self, j):
        # type: (JSS) -> None
        result = j.uapi.AlertNotification()
        assert result is not None
        assert isinstance(result, list)

    def test_get_enrollment_settings(self, j):
        # type: (JSS) -> None
        result = j.uapi.EnrollmentSetting()

    def test_get_system_info(self, j):
        # type: (JSS) -> None
        result = j.uapi.SystemInformation()
        assert result is not None
