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

"""Configuration options for connecting to Launchpad."""

from oslo_config import cfg

launchpad_group = cfg.OptGroup(
    "launchpad",
    title="Launchpad Server Connection Options",
    help="""Options under this group are used to define the connection
            details to a Launchpad service.""",
)

opts = [
    cfg.StrOpt(
        "credentials_file",
        help="The file containing the credentials for accessing the Launchpad service.",
    ),
    cfg.StrOpt("version", default="devel", help="Launchpad API version to use. Default is devel."),
    cfg.StrOpt(
        "service_root",
        default="production",
        help="Launchpad API service root to use. Default is production.",
    ),
]


def register_opts(conf: cfg.CONF):
    """Register configuration options.

    :param conf: configuration option manager
    """
    conf.register_group(launchpad_group)
    conf.register_opts(opts, group=launchpad_group)
