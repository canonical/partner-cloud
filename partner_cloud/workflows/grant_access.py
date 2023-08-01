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

"""Temporal Workflow for granting access to Partner Clouds."""

import argparse
import asyncio
import sys
from datetime import timedelta
from typing import List, Dict, Optional, Set, Tuple

from temporalio import workflow
from temporalio.client import Client

with workflow.unsafe.imports_passed_through():
    from oslo_log import log as logging

    import partner_cloud.conf
    from partner_cloud import config
    from partner_cloud.objects import User
    from partner_cloud.resources import Resource
    from partner_cloud.resources.infra import InfraNode
    from partner_cloud.resources.openstack import OpenStackProject
    from partner_cloud.activities import jira, launchpad, ldap
    from partner_cloud.converters import pydantic_data_converter


CONF = partner_cloud.conf.CONF
LOG = logging.getLogger(__name__)
TASK_QUEUE = "partner-cloud-access"


@workflow.defn
class PartnerCloudGrantAccessWorkflow:
    """Workflow to describe granting access to the various Partner Clouds."""

    @workflow.run
    async def run(self, project: str, cloud: str) -> Tuple[int, int]:
        """Grant access to the partner cloud.

        This workflow will grant users access to the specified partner
        cloud as defined in Jira tasks. Specifically, it will query
        Jira to determine which users need access and add them to the
        appropriate launchpad group (either user-level access or infra-
        level access).

        Depending on the appropriate level of access, it will either
        import their ssh keys to the infra node (infra-level access) or
        create a project that they can access and use as a project on top
        of the cloud.

        :param project: the JIRA project name to resolve
        :param cloud: the name of the partner cloud to grant access
        :return:
        """
        LOG.info(f"Fetching list of users to grant access to {cloud}")

        cloud_config = None
        for c in CONF.clouds:
            LOG.info(f"Looking at cloud {c}")
            config = CONF.get(c)
            LOG.info(f"Found config {config}")
            if config.name == cloud:
                cloud_config = config
                break

        if not cloud_config:
            LOG.error(f"Unable to find configuration for cloud {cloud}")
            raise Exception(f"Unable to find configuration for cloud {cloud}")
        LOG.info(f"Found cloud_config {cloud_config}")

        access_result = await workflow.execute_activity(
            jira.get_access_for_current_sprint,
            args=[cloud_config.name],
            start_to_close_timeout=timedelta(minutes=2),
        )
        resource_map: Dict[Resource, Set[User]] = access_result.to_map()

        LOG.info(f"Found resource_map: {resource_map}")

        # Resolve all the users to ensure we have updated information
        # for the user's email address, launchpad id, etc.
        for resource, users in resource_map.copy().items():
            LOG.info(f"Resolving users for {resource.name}")
            resolved_users = await workflow.execute_activity(
                ldap.resolve_users,
                args=[users],
                start_to_close_timeout=timedelta(minutes=5),
            )
            resource_map[resource] = resolved_users

        tasks = []
        for resource, users in resource_map.items():
            if not users:
                LOG.info(f"No users need access to {resource}")
                continue

            LOG.info(f"Examining resource {resource} ({type(resource)} for users: {users}")
            if isinstance(resource, InfraNode):
                # grant infra access
                LOG.info(f"Starting activity to add users {users} to launchpad "
                         f"group {cloud_config.infra_group}")
                tasks.append(asyncio.create_task(workflow.execute_activity(
                    launchpad.add_users_to_group,
                    args=[cloud_config.infra_group, users],
                    start_to_close_timeout=timedelta(minutes=5),
                )))

            if isinstance(resource, OpenStackProject):
                # grant project access
                LOG.info(f"Starting activity to add users {users} to launchpad "
                         f"group {cloud_config.user_group}")
                tasks.append(asyncio.create_task(workflow.execute_activity(
                    launchpad.add_users_to_group,
                    args=[cloud_config.user_group, users],
                    start_to_close_timeout=timedelta(minutes=5)
                )))

        if tasks:
            await asyncio.wait(tasks)

        # TODO(wolsen) - let's get a better return set here for the commandline
        return 0, 0


def setup_opts(argv: Optional[List[str]]):
    """Parse CLI arguments.

    :param argv: list of arguments to parse
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cloud", dest="cloud", required=True, help="Name of the cloud to grant access to."
    )
    return parser.parse_known_args(argv)


async def async_main(argv: Optional[List[str]] = None):
    """Async entry point for the grant access workflow.

    :param argv: list of CLI arguments
    """
    if argv is None:
        argv = sys.argv

    (options, args) = setup_opts(argv)
    config.parse_args(args)

    # Create client connected to server at the given address.
    client = await Client.connect(
        f"{CONF.temporal.host}:{CONF.temporal.port}", namespace=CONF.temporal.namespace,
        data_converter=pydantic_data_converter,
    )

    # Execute a workflow
    workflow_id = f"partner-cloud-{options.cloud}-grant-access"
    result = await client.execute_workflow(
        PartnerCloudGrantAccessWorkflow.run,
        args=[CONF.jira.project, options.cloud],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"Result: {result}")


def main(argv: Optional[List[str]] = None):
    """Entry point for the grant access workflow.

    :param argv: list of CLI arguments.
    """
    return asyncio.run(async_main())
