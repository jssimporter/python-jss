from __future__ import absolute_import
import pytest
import jss


class TestNetworkSegments(object):

    def test_new_network_segment(self, j, etree_network_segment):
        fixture_network_segment = jss.NetworkSegment(j, etree_network_segment)
        fixture_network_segment.save()
        assert fixture_network_segment.id is not None

    def test_get_network_segment(self, j, etree_network_segment):
        fixture_network_segment = j.NetworkSegment(etree_network_segment.findtext('name'))
        assert fixture_network_segment is not None
        assert fixture_network_segment.id is not None

    def test_update_network_segment(self, j, etree_network_segment):
        fixture_network_segment = j.NetworkSegment(etree_network_segment.findtext('name'))
        fixture_network_segment.find('name').text = 'Updated Fixture'
        fixture_network_segment.save()

    def test_delete_network_segment(self, j, etree_network_segment):
        fixture_network_segment = j.NetworkSegment('Updated Fixture')
        fixture_network_segment.delete()
