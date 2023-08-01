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

"""Config options for cloud configurations."""

from oslo_config import cfg

opts = [
    cfg.ListOpt(
        "clouds",
        help="The list of clouds which are available. Each cloud should have "
        "their own configuration section which matches the name.",
    ),
]

cloud_opts = [
    cfg.StrOpt(
        "name",
        help="The friendly name of the cloud",
    ),
    cfg.StrOpt(
        "infra_group",
        help="The launchpad group which determines which users have access to "
        "the infrastructure nodes.",
    ),
    cfg.StrOpt(
        "user_group",
        help="The launchpad group which determines which users have access to "
        "the cloud itself as tenants.",
    ),
    cfg.IPOpt("infra_node", help="The IP address of the infra node for the cloud."),
]


def register_opts(conf: cfg.CONF):
    """Register configuration options.

    :param conf: configuration option manager
    """
    conf.register_opts(opts)
