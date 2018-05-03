import pytest
import jss
from xml.etree import ElementTree


class TestObjectsPatch(object):
    """Test JSSObjects related to Patch Management"""

    def test_get_patchavailabletitles(self, j):
        patch_available_titles = j.PatchAvailableTitle("1")
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

    def test_get_patchinternalsource(self, j):
        internal_source = j.PatchInternalSource(1)
        assert internal_source is not None

    def test_list_patchpolicies(self, j):
        patch_policies = j.PatchPolicy()
        assert patch_policies is not None

    def test_get_patchreports_by_title(self, j):
        patch_reports = j.PatchReport("1")
        assert patch_reports is not None

    def test_get_patchreports_by_title_version(self, j):
        patch_reports = j.PatchReport(1, version="x")
        assert patch_reports is not None

    def test_list_patchsoftwaretitles(self, j):
        patch_software_titles = j.PatchSoftwareTitle()
        assert patch_software_titles is not None

    def test_post_patchsoftwaretitle(self, j):
        patch_software_title = jss.PatchSoftwareTitle(j, "Fixture")
        patch_software_title.find('name_id').text = "Fixture"
        patch_software_title.find('source_id').text = "1"
        first_version = ElementTree.SubElement(patch_software_title.find('versions'), 'version')
        ElementTree.SubElement(first_version, 'software_version', text="1.0.0")

        xmlstr = ElementTree.tostring(patch_software_title)
        print(xmlstr)
        patch_software_title.save()
