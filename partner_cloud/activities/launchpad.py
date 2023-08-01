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

"""Launchpad based activities."""

from typing import Iterable, List, Tuple, Union

from launchpadlib.launchpad import Launchpad
from launchpadlib.uris import lookup_service_root
from temporalio import activity, workflow

import partner_cloud.conf

with workflow.unsafe.imports_passed_through():
    from oslo_log import log as logging
    from partner_cloud.objects import Object
    from partner_cloud.objects import Group, User


LOG = logging.getLogger(__name__)
CONF = partner_cloud.conf.CONF


APPLICATION_NAME = "partner-cloud-access-tool"


class LaunchpadGroupChangeResult(Object):
    group: str
    success: List[Union[Group, User]] = []
    failed: List[Tuple[Union[Group, User], str]] = []

    def has_failures(self):
        return len(self.failed) == 0

    def add_success(self, user: User):
        self.success.append(user)

    def add_failure(self, user: User, reason: str):
        self.failed.append((user, reason))


def _get_launchpad_client() -> Launchpad:
    """Returns the launchpad client.

    :return: the Launchpad client
    """
    client = Launchpad.login_with(
        APPLICATION_NAME,
        credentials_file=CONF.launchpad.credentials_file,
        service_root=lookup_service_root(CONF.launchpad.service_root),
        version=CONF.launchpad.version,
    )

    return client


def _check_memberships(lp_user, canonical_group, target_group) -> Tuple[bool, bool]:
    """Checks if the user is a canonical employee or already in the group.

    :param lp_user: the launchpad user
    :param canonical_group: the launchpad group for Canonical
    :param target_group: the targeted group to check membership
    :return: a (bool, bool) tuple indicating if the user is an
             employee, and already in the group
    """
    is_employee = False
    already_in_group = False

    for membership in lp_user.memberships_details:
        if membership.team == canonical_group:
            is_employee = True
            if already_in_group:
                break
            continue

        if membership.team == target_group and membership.status in ("Approved", "Administrator"):
            already_in_group = True
            if is_employee:
                break
            continue

    return is_employee, already_in_group


@activity.defn
async def add_users_to_group(group: str, users: Iterable[User]) -> LaunchpadGroupChangeResult:
    """Adds the specified set of users to the group.

    :param group: the name of the group to add the users to
    :param users: an Iterable of the users to add to the group
    :return: a Dict where the key is the userid and the value is a bool indicating
             whether the user is now a member of the group or not.
    """
    LOG.info(f"Adding users {users} to group {group}")
    launchpad = _get_launchpad_client()
    result = LaunchpadGroupChangeResult(group=group)

    lp_group = launchpad.people[group]
    lp_canonical = launchpad.people["canonical"]
    for user in users:
        try:
            LOG.info(f"Looking at user {user.name}")
            if not user.launchpad_id:
                LOG.warning(f"User {user.name} does not have a launchpad id!")
                result.add_failure(user, "no launchpad id")
                continue

            lp_user = launchpad.people[user.launchpad_id]

            if not lp_user.is_valid:
                LOG.error(f"User '{user.launchpad_id}' is not valid. Skipping")
                result.add_failure(user, "invalid launchpad user")
                continue

            is_employee, in_group = _check_memberships(lp_user, lp_canonical, lp_group)

            if not is_employee:
                LOG.error(f"User '{user.name}' is not a Canonical employee. Skipping")
                result.add_failure(user, "not a Canonical employee")
                continue

            if in_group:
                LOG.info(f"User '{user.name}' is already in group '{group}'")
                result.add_success(user)
                continue

            LOG.info(f"Adding user '{user.name}' to group '{group}'")
            lp_group.addMember(person=lp_user, status="Approved")
            result.add_success(user)

        except KeyError:
            LOG.error(f"Unable to find user '{user.name}' in launchpad. Skipping")
            result.add_failure(user, "User not in launchpad")

    return result
