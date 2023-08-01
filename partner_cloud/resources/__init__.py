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

from pydantic import BaseModel
from partner_cloud.objects import Group, Object, User
from typing import Union


class Resource(Object):
    """A resource which can be assigned."""
    name: str


class ResourceAccess(BaseModel):
    """Resource access list."""
    resource: Resource
    users: Union[User, Group] = []

    def add(self, *users: Union[User, Group]) -> None:
        """Add a user or list of users to access the resource."""
        for user in users:
            self.users.append(user)

    def remove(self, *users: Union[User, Group]) -> None:
        """Remove the users from the access for the resource."""
        for user in users:
            self.users.remove(user)
