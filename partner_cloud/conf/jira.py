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

"""Config options for jira server connection."""

from oslo_config import cfg

jira_group = cfg.OptGroup(
    "jira",
    title="Jira Server Connection Options",
    help="""Options under this group are used to define the connection
            details to a Jira server.""",
)

opts = [
    cfg.URIOpt(
        "server_url",
        default="https://warthogs.atlassian.net",
        help="URL of the Jira server to connect to.",
    ),
    cfg.StrOpt("email", help="Email address of the user to connect to the Jira server with."),
    cfg.StrOpt(
        "api_token", secret=True, help="API Token used to connect to the Jira server with."
    ),
    cfg.StrOpt("project", default="PACLOUD", help="Project name for Jira tasks."),
]


def register_opts(conf: cfg.CONF):
    """Register configuration options.

    :param conf: configuration option manager
    """
    conf.register_group(jira_group)
    conf.register_opts(opts, group=jira_group)
