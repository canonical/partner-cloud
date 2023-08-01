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

"""Activities for managing SSH Keys."""

import asyncio
from typing import Dict, Iterable

from temporalio import activity, workflow

import partner_cloud.conf

with workflow.unsafe.imports_passed_through():
    from oslo_log import log as logging


LOG = logging.getLogger(__name__)
CONF = partner_cloud.conf.CONF


@activity.defn
async def ssh_import_id(launchpad_ids: Iterable[str]) -> Dict[str, int]:
    """Imports the SSH keys of the specified launchpad users to the local machine.

    :param launchpad_ids: a Set of strings containing launchpad ids.
    :returns: a mapping of the launchpad ID to a bool value indicating whether
              the ssh keys were successfully imported for the user.
    """
    results = dict()

    # Note: the ssh-import-id does take multiple user ids as a parameter, however
    # it stops processing after the first failure. As such, when an attempt to import
    # ssh keys fails before the last of the users then its unclear how many were
    # imported. Thus, each key is imported one-by-one in order to import as many
    # ssh keys as possible and only fail for some if there is indeed a failure.
    for lpid in launchpad_ids:
        cmd = ["ssh-import-id", f"lp:{lpid}"]
        LOG.debug(f"Issuing command: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.wait()
        if process.returncode != 0:
            LOG.debug(f"{' '.join(cmd)} failed. stdout = {process.stdout}, "
                      f"stderr={process.stderr}")

        results[lpid] = process.returncode == 0

    return results
