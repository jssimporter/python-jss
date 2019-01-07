#!/usr/bin/env python
# Copyright (C) 2014-2017 Shea G Craig
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""uapiobjects.py

Classes representing JSS database objects and their UAPI endpoints
"""
from .uapiobject import UAPIObject, UAPIContainer

__all__ = 'Cache', 'Ebook', 'AlertNotification', 'MobileDevice', 'PatchPolicy', 'EnrollmentSetting', \
          'EnrollmentHistory', 'SelfServiceSettings', 'StartupStatus', 'SystemInformation', 'VPPSubscription', \
          'Lobby'


class AdvancedMobileDeviceSearch(UAPIContainer):
    _endpoint_path = "devices/advancedSearches"


class Building(UAPIContainer):
    _endpoint_path = "settings/obj/building"


class Category(UAPIContainer):
    _endpoint_path = "settings/obj/category"


class Cache(UAPIObject):
    _endpoint_path = "settings/obj/cache"
    can_post = False
    can_delete = False


class ClientCheckIn(UAPIObject):
    _endpoint_path = "settings/obj/checkIn"
    can_post = False
    can_delete = False


class Ebook(UAPIContainer):
    _endpoint_path = "deployable/obj/ebook"
    can_put = False
    can_post = False
    can_delete = False


class MobileDevice(UAPIObject):
    _endpoint_path = "inventory/obj/mobileDevice"
    can_put = False
    can_post = False
    can_delete = False


class AlertNotification(UAPIContainer):
    _endpoint_path = "notifications/alerts"
    can_put = False
    can_post = False


class Lobby(UAPIObject):
    _endpoint_path = ""
    can_put = False
    can_post = False
    can_delete = False


class PatchPolicy(UAPIContainer):
    _endpoint_path = "patch/obj/policy"


class EnrollmentSetting(UAPIObject):
    _endpoint_path = "settings/obj/enrollment"
    can_post = False
    can_delete = False


# Unbelievably, this has a different schema but is intended for the same usage as EnrollmentSetting
class EnrollmentSettingSetting(UAPIObject):
    _endpoint_path = "settings/obj/enrollment/settings"
    can_post = False
    can_delete = False


class EnrollmentHistory(UAPIContainer):
    _endpoint_path = "settings/obj/enrollment/history"
    can_post = False
    can_put = False
    can_delete = False


class SelfServiceSettings(UAPIObject):
    _endpoint_path = "settings/obj/selfservice"
    can_post = False
    can_delete = False


class StartupStatus(UAPIObject):
    _endpoint_path = "startup-status"
    can_put = False
    can_post = False
    can_delete = False


class SystemInformation(UAPIObject):
    _endpoint_path = "system/obj/info"
    can_put = False
    can_post = False
    can_delete = False


class VPPSubscription(UAPIContainer):
    _endpoint_path = "vpp/subscriptions"
    can_put = False
    can_post = False
    can_delete = False
