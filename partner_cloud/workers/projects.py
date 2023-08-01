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
"""Logic for the projects worker daemon."""
import asyncio
import sys
from typing import List, Optional

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

import partner_cloud.conf
from partner_cloud.activities.jira import get_access_for_current_sprint
from partner_cloud.activities.launchpad import add_users_to_group
from partner_cloud.activities.ldap import resolve_users
from partner_cloud.workflows import grant_access

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from oslo_log import log as logging
    from partner_cloud import config
    # from pydantic import BaseModel
    from partner_cloud.converters import pydantic_data_converter


CONF = partner_cloud.conf.CONF
LOG = logging.getLogger(__name__)


async def async_main(argv: Optional[List[str]] = None):
    """Async entry point for the archive backport worker.

    :param argv: list of CLI arguments.
    """
    if argv is None:
        argv = sys.argv

    config.parse_args(argv)
    logging.setup(CONF, "partner_cloud")

    CONF.log_opt_values(LOG, logging.DEBUG)
    LOG.info(f"Testing... {CONF.get('PC 5a').infra_group}")

    client = await Client.connect(
        f"{CONF.temporal.host}:{CONF.temporal.port}",
        namespace=CONF.temporal.namespace,
        data_converter=pydantic_data_converter,
    )

    # Run the worker
    worker = Worker(
        client,
        task_queue=grant_access.TASK_QUEUE,
        workflows=[
            grant_access.PartnerCloudGrantAccessWorkflow,
        ],
        activities=[
            get_access_for_current_sprint,
            add_users_to_group,
            resolve_users
        ],
    )
    await worker.run()


def main(argv: Optional[List[str]] = None):
    """Entry point for the project worker.

    :param argv: list of CLI arguments.
    """
    return asyncio.run(async_main(argv))
