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

"""Configuration definition and parsing."""
from typing import List

from oslo_config import cfg
from oslo_log import log

import partner_cloud.conf
from partner_cloud import version
from partner_cloud.conf.cloud import cloud_opts

CONF = partner_cloud.conf.CONF

LOG = log.getLogger(__name__)


def parse_args(argv: List[str], default_config_files: str = None):
    """Parse command line arguments to load the configuration.

    :param argv: list of arguments to parse.
    :param default_config_files: Path to a configuration file to use.
    """
    log.register_options(CONF)

    CONF(
        argv[1:],
        project="partner_cloud",
        version=version.version_string(),
    )

    # Dynamic cloud sections calls for this bit here.
    for cloud in CONF.clouds:
        CONF.register_group(cfg.OptGroup(cloud, dynamic_group_owner="clouds"))
        CONF.register_opts(cloud_opts, cloud)
