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
"""Connection options to the Temporal server."""

from oslo_config import cfg

temporal_group = cfg.OptGroup(
    "temporal",
    title="Temporal Server Connection options",
    help="Options defined in this group are used to define the connection "
    "details to a Temporal server.",
)

opts = [
    cfg.StrOpt(
        "host",
        default="localhost",
        help="Connect to the Temporal server on the given host.",
    ),
    cfg.IntOpt(
        "port",
        default=7233,
        help="The TCP/IP port number to use for the connection.",
    ),
    cfg.StrOpt(
        "namespace", default="default", help="Namespace to connect to in the Temporal server."
    ),
]


def register_opts(conf: cfg.CONF):
    """Register configuration options.

    :param conf: configuration option manager.
    """
    conf.register_group(temporal_group)
    conf.register_opts(opts, group=temporal_group)
