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

"""Logic for jira related activities."""

from collections import defaultdict
from typing import Dict, DefaultDict, List, Optional, Set, TypeVar
import ipaddress

from temporalio import activity, workflow

import partner_cloud.conf

with workflow.unsafe.imports_passed_through():
    from jira import JIRA
    from jira.exceptions import JIRAError
    from jira.resources import Issue
    from jira.resources import User as JiraUser
    from oslo_log import log as logging
    from partner_cloud.resources import Resource
    from partner_cloud.objects import Object, User
    from partner_cloud.resources.infra import InfraNode
    from partner_cloud.resources.openstack import OpenStackProject


T = TypeVar("T", OpenStackProject, InfraNode, Resource)

LOG = logging.getLogger(__name__)
CONF = partner_cloud.conf.CONF

# This is the name of the field that indicates whether the integration being tested is
# at the application or infrastructure layer.
FIELD_INTEGRATION_LAYER = "customfield_10579"

# The field that determines which cloud this task is scheduled for
FIELD_PARTNER_CLOUD_NAME = "customfield_10580"

# Tha field for the list of collaborators on a Jira ticket.
FIELD_COLLABORATORS = "customfield_10112"

# The field for the assignee of a Jira ticket.
FIELD_ASSIGNEE = "assignee"

# The field for the status of a Jira ticket.
FIELD_STATUS = "status"


class JiraClient:

    def __init__(self):
        self.client = JIRA(server=CONF.jira.server_url, basic_auth=(CONF.jira.email, CONF.jira.api_token))

    def get_issues_for_current_sprint(self, cloud: Optional[str] = None):
        """Retrieves the issues scheduled into the current sprint."""
        jql = f'Project = "{CONF.jira.project}" AND sprint in openSprints()'
        if cloud:
            jql += f' AND "Partner Cloud name" = "{cloud}"'
        return self.client.search_issues(jql)

    def get_issues_by_keys(self, *issue_keys: str):
        """Retrieves the issues by the specified keys."""
        keys = ", ".join(issue_keys)
        return self.client.search_issues(
            f'Project = "{CONF.jira.project}" AND IssueKey in ({keys})'
        )

    def is_issue_completed(self, issue: Issue) -> bool:  # noqa
        """Return True if the issue status indicates it is completed.

        :param issue: the Issue to check the status of
        :return: True if the issue is completed, False otherwise.
        """
        return issue.get_field(FIELD_STATUS).name == "Done"

    def assign_issue(self, issue: Issue, user: User) -> bool:
        """Assigns the issue specified to the user specified.

        :param issue: the issue to assign
        :param user: the user to assign
        :return: True if the issue is successfully assigned, False otherwise.
        """
        if not user.email:
            raise ValueError("User provided must have an email address")
        return self.client.assign_issue(issue.key, user.email)

    def get_pending_prerequisite_issues(self, issue: Issue) -> Optional[List[str]]:
        """Returns the set of jira Issues that are pre-requisites for the given task.

        Examines the Jira task and returns a list of issue keys which have not yet
        completed but are required to start the activity. For example, a user requiring
        a project on an OpenStack cloud must have the deployment task completed first
        before the activity task can start.

        :param issue: the jira issue
        :return: a list of issue keys that have yet to complete but are required
                 to complete.
        """
        # If there are no issues linked, then simply return None
        if not hasattr(issue.fields, "issuelinks"):
            return None

        prerequisite_issues = []
        for link in issue.fields.issuelinks:
            # If the link is not a Finish-to-Start type link (meaning the linked issue
            # must finish in order for the current issue to start), then skip this link.
            if not link.type.name.startswith("Finish-to-Start"):
                continue

            # If the link does not have an inwardIssue (e.g. something that is a predecessor
            # to this issue), then skip this link.
            if not hasattr(link, "inwardIssue"):
                continue

            prerequisite_issues.append(link.inwardIssue.key)

        if not prerequisite_issues:
            return None

        pending = []
        for task in self.get_issues_by_keys(*prerequisite_issues):
            if not self.is_issue_completed(task):
                pending.append(task.key)

        return pending


def convert_user(user: JiraUser) -> User:
    """Converts a JiraUser to a PartnerCloud User."""
    return User(name=user.displayName, email=user.emailAddress)


class AccessResult(Object):
    """The results for getting access for current sprints."""
    resources: List[T] = []
    users: Dict[str, Set[User]] = {}

    @staticmethod
    def from_map(data: Dict[T, Set[User]]) -> 'AccessResult':
        """Creates an AccessResult from a map."""
        resources = []
        user_map: Dict[str, Set[User]] = {}
        for resource, users in data.items():
            resources.append(resource)
            user_map[resource.name] = users

        return AccessResult(resources=resources, users=user_map)

    def to_map(self) -> Dict[T, Set[User]]:
        """Converts to a mapping of resource -> set(users).
        """
        mapping: Dict[T, Set[User]] = {}
        for resource in self.resources:
            mapping[resource] = self.users.get(resource.name, set())

        return mapping


@activity.defn
async def get_access_for_current_sprint(cloud: str) -> AccessResult:
    """Returns the access lists for the current sprint.

    Returns a tuple(list(str), list(str)) which contains the list of users that should be
    granted access. The first list will be the list of users which require access to the
    underlying infra nodes and the second list will be the list of users which require access
    as tenants in the cloud.

    :param cloud: the PartnerCloud to determine access for
    :return: a Mapping of resources to the users that need access to the resource.
    """
    jira = JiraClient()

    try:
        issues = jira.get_issues_for_current_sprint(cloud)
        LOG.info(f"Found issues: {issues}")

        resource_map: DefaultDict[Resource, Set[User]] = defaultdict(set)
        LOG.info(f"Checking: {CONF.clouds}")
        infra_node = InfraNode(
            name=f"{cloud}-infra-node",
            ip_address=ipaddress.ip_address(CONF.get(cloud).infra_node)
        )

        for issue in issues:
            LOG.info(f"Checking issue {issue.key} for access requirements.")
            if jira.is_issue_completed(issue):
                LOG.debug(f"Issue has already been completed. Skipping.")
                continue

            if pending_issues := jira.get_pending_prerequisite_issues(issue):
                LOG.info(f"Issue {issue.key} cannot start as it is awaiting the completion "
                         f"of issues: {' '.join(pending_issues)}. Not determining access.")
                continue

            integrations = issue.get_field(FIELD_INTEGRATION_LAYER) or []
            jira_users: List[JiraUser] = issue.get_field(FIELD_COLLABORATORS) or []
            jira_users.append(issue.get_field(FIELD_ASSIGNEE))
            # Convert the Jira users to ProjectCloud users
            users = [convert_user(user) for user in jira_users]

            for integration in integrations:
                if integration.value == "Infrastructure":
                    # The completion of the task requires access to the infrastructure
                    # itself, e.g. a deployment of a node needs to occur.
                    LOG.debug(f"Adding users {users} to infra node {infra_node.name}")
                    resource_map[infra_node].update(users)
                elif integration.value == "Platform":
                    # TODO(wolsen) Determine how to determine which platform is deployed
                    #  in order to give the right resource.
                    #
                    # The completion of this issue requires access to the platform, e.g.
                    # an OpenStack project is required. Create a project based on the
                    # issue key (e.g. PACLOUD-102) that allows to map back to the Jira
                    # ticket.
                    project = OpenStackProject(name=issue.key.lower(), cloud=cloud)
                    LOG.debug(f"Adding users {users} to project {project.name}")
                    resource_map[project].update(users)
                elif integration.value == "Application":
                    # Requires access to the application running on top of the platform.
                    LOG.warning(f"Task requires application access, but this is not yet available.")
                    continue
                else:
                    # Unknown integration level
                    LOG.error(f"Unknown integration level {integration}, {type(integration)}. "
                              "Unable to grant access for users to resources of this type.")
                    continue

        return AccessResult.from_map(resource_map)
    except JIRAError as e:
        LOG.exception("Failed to query issues from Jira.")
        raise e
