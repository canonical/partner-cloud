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

"""Infrastructure resources.."""

from pydantic import BaseModel
from ipaddress import IPv4Address, IPv6Address
from partner_cloud.resources import Resource
from typing import Union


class InfraNode(Resource, BaseModel):
    """An infrastructure node for a partner cloud."""
    ip_address: Union[IPv4Address, IPv6Address]
