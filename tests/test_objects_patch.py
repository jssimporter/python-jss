import pytest
import jss


class TestObjectsPatch(object):
    """Test JSSObjects related to Patch Management"""

    def test_get_patchavailabletitles(self, j):
        patch_available_titles = j.PatchAvailableTitle()
        assert patch_available_titles is not None

    def test_list_patchexternalsources(self, j):
        patch_external_sources = j.PatchExternalSource()
        assert patch_external_sources is not None

    def test_get_patchexternalsource(self, j):
        patch_external_source = j.PatchExternalSource(1)
        assert patch_external_source is not None

    def test_post_patchexternalsource(self, j):
        new_external_source = jss.PatchExternalSource(j, "Fixture")
        new_external_source.find('host_name').text = 'localhost'
        new_external_source.save()

    def test_put_patchexternalsource(self, j):
        existing_external_source = j.PatchExternalSource("Fixture")
        existing_external_source.find('host_name').text = '127.0.0.1'
        existing_external_source.save()

    def test_delete_patchexternalsource(self, j):
        existing_external_source = j.PatchExternalSource("Fixture")
        existing_external_source.delete()

