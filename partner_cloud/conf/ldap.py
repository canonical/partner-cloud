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

"""Config options for ldap server connection."""

from oslo_config import cfg

ldap_group = cfg.OptGroup(
    "ldap",
    title="LDAP Server connection options",
    help="""Options under this group are used to define the connection
            details to an LDAP server.""",
)

ldap_opts = [
    cfg.HostAddressOpt(
        "server",
        help="The address or hostname of the ldap server",
        default="ldap.canonical.com",
    ),
    cfg.IntOpt(
        "port",
        help="The port of the ldap server to connect to.",
        default=636,
    ),
    cfg.BoolOpt(
        "use_tls",
        help="Turn on TLS connection.",
        default=True
    ),
    cfg.StrOpt(
        "bind_dn",
        help="The bind dn to query the ldap server with.",
    ),
    cfg.StrOpt(
        "password",
        help="The password to use when querying the ldap server.",
        secret=True,
    ),
    cfg.StrOpt(
        "search_base",
        help="The LDAP search_base to use when performing queries.",
        default="ou=staff,dc=canonical,dc=com",
    )
]


def register_opts(conf: cfg.CONF):
    """Register configuration options.

    :param conf: configuration option manager
    """
    conf.register_group(ldap_group)
    conf.register_opts(ldap_opts, group=ldap_group)
