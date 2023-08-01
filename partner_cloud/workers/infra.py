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
"""Logic for the infra worker daemon."""
import asyncio
import sys
from typing import List, Optional

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

import partner_cloud.conf
from partner_cloud.activities.sshkeys import ssh_import_id
from partner_cloud.workflows import grant_access

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from oslo_log import log as logging
    from partner_cloud import config


CONF = partner_cloud.conf.CONF
LOG = logging.getLogger(__name__)


async def async_main(argv: Optional[List[str]] = None):
    """Async entry point for the archive backport worker.

    :param argv: list of CLI arguments.
    """
    if argv is None:
        argv = sys.argv

    config.parse_args(argv)
    logging.setup(CONF, "partner-cloud")
    client = await Client.connect(
        f"{CONF.temporal.host}:{CONF.temporal.port}",
        namespace=CONF.temporal.namespace,
    )

    # Run the worker
    worker = Worker(
        client,
        task_queue=grant_access.TASK_QUEUE,
        workflows=[
            grant_access.PartnerCloudGrantAccessWorkflow,
        ],
        activities=[
            ssh_import_id,
        ],
    )
    await worker.run()


def main(argv: Optional[List[str]] = None):
    """Entry point for the project worker.

    :param argv: list of CLI arguments.
    """
    return asyncio.run(async_main(argv))
