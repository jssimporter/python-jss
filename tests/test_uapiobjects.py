import pytest
from jss import JSS


class TestUAPIObjects(object):

    def test_get_cache(self, j, uapi_token):
        # type: (JSS) -> None
        result = j.Cache()
        assert result is not None
        assert isinstance(result, dict)
