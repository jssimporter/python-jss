import pytest
from xml.etree import ElementTree


@pytest.fixture
def etree_building():  # type: () -> ElementTree.Element
    building = ElementTree.Element('building')
    name = ElementTree.SubElement(building, 'name')
    name.text = 'Fixture Building'
    # id = ElementTree.SubElement(building, 'id')
    # id.text = '0'

    return building


@pytest.fixture
def etree_department():  # type: () -> ElementTree.Element
    department = ElementTree.Element('department')
    name = ElementTree.SubElement(department, 'name')
    name.text = 'Fixture Department'

    return department


@pytest.fixture
def etree_network_segment():  # type: () -> ElementTree.Element
    network_segment = ElementTree.Element('network_segment')

    name = ElementTree.SubElement(network_segment, 'name')
    name.text = 'Amsterdam Office'
    starting_address = ElementTree.SubElement(network_segment, 'starting_address')
    starting_address.text = '10.1.1.1'
    ending_address = ElementTree.SubElement(network_segment, 'ending_address')
    ending_address.text = '10.10.1.1'
    override_buildings = ElementTree.SubElement(network_segment, 'override_buildings')
    override_buildings.text = 'false'
    override_departments = ElementTree.SubElement(network_segment, 'override_departments')
    override_departments.text = 'false'

    return network_segment
