import pytest


class TestGurlAdapter(object):

    def test_get(self, gurl_adapter, jss_prefs_dict):
        response = gurl_adapter.get(jss_prefs_dict['jss_url'])
        assert response is not None
