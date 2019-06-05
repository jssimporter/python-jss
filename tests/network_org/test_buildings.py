import pytest
import jss


class TestBuildings(object):

    def test_new_building(self, j, etree_building):
        fixture_building = jss.Building(j, etree_building)
        fixture_building.save()
        assert fixture_building.id is not None

    def test_get_building(self, j, etree_building):
        fixture_building = j.Building(etree_building.findtext('name'))
        assert fixture_building is not None
        assert fixture_building.id is not None

    def test_update_building(self, j, etree_building):
        fixture_building = j.Building(etree_building.findtext('name'))
        fixture_building.find('name').text = 'Updated Fixture'
        fixture_building.save()
        fixture_building.delete()

    def test_delete_building(self, j, etree_building):
        fixture_building = j.Building(etree_building.findtext('name'))
        fixture_building.delete()
