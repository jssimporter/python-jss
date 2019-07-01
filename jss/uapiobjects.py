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

__all__ = 'AdvancedMobileDeviceSearch', 'AlertNotification', 'Building', 'Cache', 'Category', 'ClientCheckIn', \
          'Department', 'DeviceEnrollment', 'Ebook', 'Engage', 'EnrollmentHistory', 'EnrollmentSetting', \
          'EnrollmentSettingSetting', 'Lobby', \
          'MobileDevice', 'PatchPolicy', 'ReEnrollmentSetting', 'Script', 'SelfServiceBrandingConfiguration', \
          'SelfServiceSettings', 'SSOCertificate', 'SSOSetting', 'Site', 'StartupStatus', 'SystemInformation', \
          'SystemInitialize', 'User', 'VPPAdminAccount', 'VPPSubscription'


class AdvancedMobileDeviceSearch(UAPIContainer):
    _endpoint_path = "devices/advancedSearches"


class AlertNotification(UAPIContainer):
    _endpoint_path = "notifications/alerts"
    can_put = False
    can_post = False


class APIIntegration(UAPIContainer):
    _endpoint_path = "api-integrations"


class Building(UAPIContainer):
    _endpoint_path = "settings/obj/building"


class Cache(UAPIObject):
    _endpoint_path = "settings/obj/cache"
    can_post = False
    can_delete = False


class Category(UAPIContainer):
    _endpoint_path = "settings/obj/category"


class ClientCheckIn(UAPIObject):
    _endpoint_path = "settings/obj/checkIn"
    can_post = False
    can_delete = False


class Department(UAPIContainer):
    _endpoint_path = "settings/obj/department"


class DeviceEnrollment(UAPIObject):
    _endpoint_path = "device-enrollment"


class DeviceEnrollmentPublicKey(UAPIObject):
    _endpoint_path = "device-enrollment/public-key"


class Ebook(UAPIContainer):
    _endpoint_path = "deployable/obj/ebook"
    can_put = False
    can_post = False
    can_delete = False


class Engage(UAPIObject):
    _endpoint_path = "engage"
    can_post = False
    can_delete = False


class EnrollmentHistory(UAPIContainer):
    _endpoint_path = "settings/obj/enrollment/history"
    can_post = False
    can_put = False
    can_delete = False


class EnrollmentSetting(UAPIObject):
    _endpoint_path = "settings/enrollment"  # was: settings/obj/enrollment until about 10.9
    can_post = False
    can_delete = False


# Unbelievably, this has a different schema but is intended for the same usage as EnrollmentSetting
class EnrollmentSettingSetting(UAPIObject):
    _endpoint_path = "settings/enrollment/settings"  # was: settings/obj/enrollment/settings until about 10.9
    can_post = False
    can_delete = False


class InventoryPreload(UAPIContainer):
    _endpoint_path = "inventory-preload"


class JAMFProServerURL(UAPIObject):
    _endpoint_path = "v1/jamf-pro-server-url"


class LDAPGroup(UAPIContainer):
    _endpoint_path = "ldap/groups"
    can_delete = False
    can_post = False
    can_put = False


class LDAPServer(UAPIContainer):
    _endpoint_path = "ldap/servers"
    can_delete = False
    can_post = False
    can_put = False


class Lobby(UAPIObject):
    _endpoint_path = ""
    can_put = False
    can_post = False
    can_delete = False


class MobileDevice(UAPIObject):
    _endpoint_path = "inventory/obj/mobileDevice"
    can_put = False
    can_post = False
    can_delete = False


class MobileDeviceExtensionAttribute(UAPIContainer):
    _endpoint_path = "devices/extensionAttributes"
    can_put = False
    can_post = False
    can_delete = False


class MobileDevicePrestage(UAPIContainer):
    _endpoint_path = "v1/mobile-device-prestages"
    can_put = False
    can_post = False
    can_delete = False


class PatchPolicy(UAPIContainer):
    # _endpoint_path = "patch/obj/policy"
    _endpoint_path = "patch/patch-policies"
    can_put = False
    can_post = False
    can_delete = False


# class PatchPolicyLog(UAPIContainer):
#     _endpoint_path = "patch/patch-policies/id/logs"
#     can_put = False
#     can_post = False
#     can_delete = False

class Patch(UAPIContainer):
    _endpoint_path = "patch/obj/policy"


class ReEnrollmentSetting(UAPIObject):
    _endpoint_path = "settings/obj/reenrollment"


class Script(UAPIContainer):
    _endpoint_path = "settings/scripts"


class SelfServiceBrandingConfiguration(UAPIContainer):
    _endpoint_path = "self-service/branding/configurations"


class SelfServiceSettings(UAPIObject):
    _endpoint_path = "settings/obj/selfservice"
    can_post = False
    can_delete = False


class Site(UAPIContainer):
    _endpoint_path = "settings/sites"
    can_delete = False
    can_post = False
    can_put = False


class SSOCertificate(UAPIObject):
    _endpoint_path = "settings/sso/cert"


class SSOSetting(UAPIObject):
    _endpoint_path = "settings/sso"
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


class SystemInitialize(UAPIObject):
    _endpoint_path = "system/initialize"
    can_get = False
    can_put = False
    can_delete = False
    can_post = True


class User(UAPIContainer):
    _endpoint_path = "user"
    can_delete = False
    can_post = False
    can_put = False


class UserAccountSetting(UAPIContainer):
    _endpoint_path = "user/obj/preference"
    can_post = False


class VPPAdminAccount(UAPIContainer):
    _endpoint_path = "vpp/admin-accounts"
    can_put = False
    can_post = False
    can_delete = False


class VPPSubscription(UAPIContainer):
    _endpoint_path = "vpp/subscriptions"
    can_put = False
    can_post = False
    can_delete = False
