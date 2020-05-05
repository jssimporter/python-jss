from __future__ import absolute_import
import pytest
from xml.etree import ElementTree
import jss


@pytest.fixture
def etree_computer():  # type: () -> ElementTree.Element
    computer = ElementTree.Element('computer')
    general = ElementTree.SubElement(computer, 'general')

    name = ElementTree.SubElement(general, 'name')
    name.text = 'Fixture Computer'
    mac_address = ElementTree.SubElement(general, 'mac_address')
    mac_address.text = '00:11:22:33:44:55'

    return computer


@pytest.fixture
def computer(j, etree_computer):  # type: (JSS, ElementTree.Element) -> None
    c = jss.Computer(j, etree_computer)
    c.save()
    yield c
    c.delete()


class TestComputer(object):

    def test_get_computer_by_macaddress(self, j, computer):
        """This is a regression test for Issue #67 - Search for a computer using MAC address"""
        result = j.Computer("macaddress={}".format(computer.general.mac_address.text))
        assert result is not None
