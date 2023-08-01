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

"""Shared objects for various activities and workflows."""

from typing import Optional
from pydantic import BaseModel


class Object(BaseModel):
    """An Object for Partner Cloud"""

    def __hash__(self):
        if hasattr(self, 'name'):
            return hash(self.name)

        raise TypeError(f"unhashable type: {type(self)}")


class User(Object):
    """A user requiring access."""
    name: str
    email: Optional[str] = None
    launchpad_id: Optional[str] = None


class Group(Object):
    """A group of users."""
    launchpad_id: Optional[str] = None
