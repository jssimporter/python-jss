import pytest
from jss.distribution_point import JCDS


class TestJCDS(object):

    def test_jcds_scrape_baseurl(self):
        """Assert that we can scrape the jcds upload base url from the ``legacy/packages.html`` page,
        from <div class='chunked-uploader' data-base-url>"""
        pass

    def test_jcds_scrape_token(self):
        """Assert that we can scrape the jcds upload token from the ``legacy/packages.html`` page,
        from <div class='chunked-uploader' data-upload-token>"""
        pass

    def test_jcds_upload_chunks(self):
        """Assert that we can POST a chunked file as multipart form data, with form field name = ``file`` and filename
        = ``blob`. eg.

        POST https://regioncode-jcds.jamfcloud.com//api/file/v1/<tenant code>/package.pkg/part?chunk=0&chunks=12
        """
        pass


