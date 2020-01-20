from __future__ import absolute_import
import pytest
import jss


class TestDepartments(object):

    def test_new_department(self, j, etree_department):
        fixture_department = jss.Department(j, etree_department)
        fixture_department.save()
        assert fixture_department.id is not None

    def test_get_department(self, j, etree_department):
        fixture_department = j.Department(etree_department.findtext('name'))
        assert fixture_department is not None
        assert fixture_department.id is not None

    def test_update_department(self, j, etree_department):
        fixture_department = j.Department(etree_department.findtext('name'))
        fixture_department.find('name').text = 'Updated Fixture'
        fixture_department.save()

    def test_delete_department(self, j, etree_department):
        fixture_department = j.Department(etree_department.findtext('name'))
        fixture_department.delete()
