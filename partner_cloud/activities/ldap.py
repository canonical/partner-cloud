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

"""Activities for resolving user information."""

import textwrap
from typing import Iterable, Set
from temporalio import activity, workflow
from collections import defaultdict

with workflow.unsafe.imports_passed_through():
    import partner_cloud.conf
    from oslo_log import log as logging
    from pydantic import BaseModel
    from partner_cloud.objects import User
    from ldap3 import Server, Connection, SCHEMA
    from ldap3.core.exceptions import LDAPException


LOG = logging.getLogger(__name__)
CONF = partner_cloud.conf.CONF

ATTR_CN = 'cn'
ATTR_LAUNCHPAD_ID = 'launchpadId'
ATTR_MAIL = 'mail'

LDAP_ATTRIBUTES = [ATTR_CN, ATTR_LAUNCHPAD_ID, ATTR_MAIL]


def get_identity_attribute(user: User) -> str:
    """Returns the name of the ldap attribute to use as the user identity.

    :param user: the User to get the identifying key
    :return: the identifying ldap attribute
    """
    if user.email is not None:
        return "mail"

    if user.launchpad_id is not None:
        return "launchpadId"

    return "cn"


def get_filter_parameter(user: User) -> str:
    """Return a search filter parameter for an ldap query.

    Returns a search filter parameter that most uniquely identifies
    the user provided in the form of "(<attribute>=<value)". A search
    attribute matching the user's email address or launchpad id will
    be returned if one is available. A search attribute for the User's
    name will be returned if no other options are available.

    :param user: the User to get the search filter for
    :return: the search filter parameter
    """
    if user.email is not None:
        return f"(mail={user.email})"

    if user.launchpad_id is not None:
        return f"(launchpadId={user.launchpad_id})"

    LOG.warning(f"Using name for {user.name}, query may return false "
                "positives if there are duplicate names.")
    return f"(cn={user.name})"


def is_fully_resolved(user: User) -> bool:
    """Indicate whether the user is fully resolved or not.

    This method returns True if all fields of the User object are
    filled out with information.

    :param user: the User to resolve
    :return: True if the user has all available information,
             False otherwise.
    """
    return (user.email is not None
            and user.launchpad_id is not None
            and user.name is not None)


@activity.defn
async def resolve_users(users: Iterable[User]) -> Set[User]:
    """Returns the iterable of users provided, updated with email and launchpad.

    Updates the users provided with missing information such as launchpad id and
    email address.

    :param users: the Users to resolve
    :return: an Iterable containing the updated users.
    """
    if not users:
        LOG.info("No users to resolve.")
        return set()

    if all(map(is_fully_resolved, users)):
        LOG.info("All users are fully resolved, no need to do anything")
        return set(users)

    ldap_server = Server(CONF.ldap.server, port=CONF.ldap.port, use_ssl=CONF.ldap.use_tls,
                         get_info=SCHEMA)
    try:
        client = Connection(ldap_server, CONF.ldap.bind_dn, CONF.ldap.password)
        client.bind()

        filter_parameters = [get_filter_parameter(u) for u in users]

        search_filter = textwrap.dedent(f"""
            (&
                (|
                    {''.join(filter_parameters)}
                )
                (objectclass=person)
            )
        """).strip()

        if not client.search(CONF.ldap.search_base, search_filter,
                             attributes=[ATTR_CN, ATTR_LAUNCHPAD_ID, ATTR_MAIL]):
            msg = ("No search results matched query with search base = "
                   f"'{CONF.ldap.search_base}' and search filter = {search_filter}")
            LOG.error(msg)
            # TODO(wolsen) get a real exception
            raise Exception(msg)

        results_map = defaultdict(dict)
        for entry in client.entries:
            results_map[ATTR_CN][entry.cn.value] = entry
            results_map[ATTR_MAIL][entry.mail.value] = entry
            results_map[ATTR_LAUNCHPAD_ID][entry.launchpadId.value] = entry

        resolved_users: Set[User] = set()
        for user in users:
            if attr := get_identity_attribute(user) == ATTR_MAIL:
                result = results_map[ATTR_MAIL].get(user.email)
            elif attr == ATTR_LAUNCHPAD_ID:
                result = results_map[ATTR_LAUNCHPAD_ID].get(user.launchpad_id)
            else:
                result = results_map[ATTR_CN].get(user.name)

            resolved_users.add(User(
                name=result.cn.value, email=result.mail.value,
                launchpad_id=result.launchpadId.value
            ))

        return resolved_users
    except LDAPException as e:
        LOG.exception("Failed to query users from LDAP server.")
        raise e
