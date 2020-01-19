from __future__ import absolute_import
from __future__ import print_function
import pytest

from xml.etree import ElementTree
from jss.casper import Casper


class TestCasper(object):

    @pytest.mark.jamfcloud
    def test_cloud_casper(self, cloud_j):  # (jss) -> None
        c = Casper(cloud_j)
        print(c)




