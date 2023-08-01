#
# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

"""OpenStack Resource Definitions."""

from ipaddress import ip_address, IPv4Address, IPv6Address
from partner_cloud.resources import Resource
from typing import Optional, Union


class OpenStackProject(Resource):
    """An OpenStack Project resource."""
    project_id: Optional[str] = None
    cloud: str = None


class OpenStackBastion(Resource):
    """A bastion instance on a partner cloud."""
    project: OpenStackProject
    instance_id: Optional[str]
    ip_address: Optional[Union[IPv4Address, IPv6Address]] = None
