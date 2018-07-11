import pytest
import re
import os
import urllib
from jss.jamf_software_server import JSS
import jss
from jss.distribution_point import JCDS

try:
    # Python 2.6-2.7
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser


@pytest.mark.jamfcloud
class TestJCDS(object):

    def test_jcds_scrape_baseurl(self, cloud_j):  # type: (JSS) -> None
        """Assert that we can scrape the jcds upload base url from the ``legacy/packages.html`` page,
        from <div class='chunked-uploader' data-base-url>"""
        response = cloud_j.scrape('legacy/packages.html?id=-1&o=c')
        re_data_base_url = re.compile('data-base-url="([^"]*)"')
        # print(response.content)
        matches = re_data_base_url.search(response.content)
        print(matches.group(1))
        h = HTMLParser()

        print(h.unescape(matches.group(1)))

    def test_jcds_scrape_token(self, cloud_j):  # type: (JSS) -> None
        """Assert that we can scrape the jcds upload token from the ``legacy/packages.html`` page,
        from <div class='chunked-uploader' data-upload-token>"""
        response = cloud_j.scrape('legacy/packages.html?id=-1&o=c')
        re_data_base_url = re.compile('data-upload-token="([^"]*)"')
        # print(response.content)
        matches = re_data_base_url.search(response.content)
        print(matches.group(1))
        h = HTMLParser()

        print(h.unescape(matches.group(1)))

    def test_jcds_scrape_info(self, cloud_j):   # type: (JSS) -> None
        """Test that the JCDS distribution server object can scrape all needed information from the jamfcloud packages
        page."""
        jcds = JCDS(jss=cloud_j)
        jcds._scrape_tokens()
        assert 'jcds_base_url' in jcds.connection
        print(jcds.connection['jcds_base_url'])
        assert 'jcds_upload_token' in jcds.connection
        print(jcds.connection['jcds_upload_token'])

    def test_jcds_upload_chunks(self, cloud_j, pkg_path):  # type: (JSS) -> None
        """Assert that we can POST a chunked file as multipart form data, with form field name = ``file`` and filename
        = ``blob`. eg.

        POST https://regioncode-jcds.jamfcloud.com//api/file/v1/<tenant code>/package.pkg/part?chunk=0&chunks=12
        """
        jcds = JCDS(jss=cloud_j)
        jcds._scrape_tokens()
        assert 'jcds_base_url' in jcds.connection
        print(jcds.connection['jcds_base_url'])
        assert 'jcds_upload_token' in jcds.connection
        print(jcds.connection['jcds_upload_token'])
        jcds.copy_pkg(pkg_path)

    def test_jcds_create_and_upload(self, cloud_j, pkg_path):  # type: (JSS) -> None
        """Assert that we can create a package object, then upload an associated package via JCDS."""
        jcds = JCDS(jss=cloud_j)
        jcds._scrape_tokens()
        assert 'jcds_base_url' in jcds.connection
        print(jcds.connection['jcds_base_url'])
        assert 'jcds_upload_token' in jcds.connection
        print(jcds.connection['jcds_upload_token'])
        jcds.copy_pkg(pkg_path)

        pkg = jss.Package(cloud_j, os.path.basename(pkg_path))
        pkg.save()

    def test_jcds_fixup(self, cloud_j, pkg_path):  # type: (JSS) -> None
        pkg = cloud_j.Package(os.path.basename(pkg_path))
        print(pkg)
        pkg.save()
