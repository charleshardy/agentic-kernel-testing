"""
Resource Group Data Models

Models for organizing and managing groups of infrastructure resources.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ResourceType(Enum):
    """Type of infrastructure resource."""
    BUILD_SERVER = "build_server"
    HOST = "host"
    BOARD = "board"


@dataclass
class AllocationPolicy:
    """Policy for resource allocation within a group."""
    max_concurrent_allocations: Optional[int] = None
    reserved_for_teams: List[str] = field(default_factory=list)
    priority_boost: int = 0
    require_approval: bool = False

    def allows_team(self, team: str) -> bool:
        """Check if the policy allows allocation for the given team."""
        if not self.reserved_for_teams:
            return True
        return team in self.reserved_for_teams

    def can_allocate(self, current_allocations: int) -> bool:
        """Check if allocation is allowed based on current count."""
        if self.max_concurrent_allocations is None:
            return True
        return current_allocations < self.max_concurrent_allocations


@dataclass
class ResourceGroup:
    """A group of infrastructure resources."""
    id: str
    name: str
    resource_type: ResourceType
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    allocation_policy: AllocationPolicy = field(default_factory=AllocationPolicy)
    member_ids: List[str] = field(default_factory=list)

    def add_member(self, resource_id: str) -> bool:
        """Add a resource to the group."""
        if resource_id not in self.member_ids:
            self.member_ids.append(resource_id)
            return True
        return False

    def remove_member(self, resource_id: str) -> bool:
        """Remove a resource from the group."""
        if resource_id in self.member_ids:
            self.member_ids.remove(resource_id)
            return True
        return False

    def has_member(self, resource_id: str) -> bool:
        """Check if resource is a member of the group."""
        return resource_id in self.member_ids

    def member_count(self) -> int:
        """Get the number of members in the group."""
        return len(self.member_ids)
