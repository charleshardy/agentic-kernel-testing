"""
Resource Group Manager

Manages resource grouping by labels and purpose, with allocation policy enforcement.

**Feature: test-infrastructure-management**
**Validates: Requirements 14.1-14.5**
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of infrastructure resources."""
    BUILD_SERVER = "build_server"
    QEMU_HOST = "qemu_host"
    PHYSICAL_BOARD = "physical_board"


@dataclass
class AllocationPolicy:
    """
    Policy for resource allocation within a group.
    
    **Requirement 14.2**: Enforce rules such as max concurrent, team restrictions, priority
    """
    max_concurrent_allocations: Optional[int] = None
    reserved_for_teams: List[str] = field(default_factory=list)
    priority_boost: int = 0
    require_approval: bool = False
    max_allocation_duration_seconds: Optional[int] = None
    allow_preemption: bool = False


@dataclass
class ResourceGroup:
    """
    A group of infrastructure resources.
    
    **Requirement 14.1**: Allow grouping by labels such as architecture, location, team, or purpose
    """
    id: str
    name: str
    resource_type: ResourceType
    description: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    allocation_policy: AllocationPolicy = field(default_factory=AllocationPolicy)
    member_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GroupStatistics:
    """
    Aggregate statistics for a resource group.
    
    **Requirement 14.5**: Display aggregate capacity, utilization, and workload distribution
    """
    group_id: str
    group_name: str
    resource_type: ResourceType
    total_members: int
    online_members: int
    offline_members: int
    maintenance_members: int
    # Capacity
    total_cpu_cores: int = 0
    total_memory_mb: int = 0
    total_storage_gb: int = 0
    # Utilization
    avg_cpu_percent: float = 0.0
    avg_memory_percent: float = 0.0
    avg_storage_percent: float = 0.0
    # Workload
    active_workloads: int = 0
    queued_workloads: int = 0
    # Allocation
    current_allocations: int = 0
    max_allocations: Optional[int] = None


@dataclass
class AllocationRequest:
    """Request to allocate a resource from a group."""
    id: str
    group_id: str
    requester_team: Optional[str] = None
    requester_user: Optional[str] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AllocationResult:
    """Result of an allocation request."""
    success: bool
    resource_id: Optional[str] = None
    allocation_id: Optional[str] = None
    error_message: Optional[str] = None
    policy_violations: List[str] = field(default_factory=list)
    wait_time_estimate_seconds: Optional[int] = None


@dataclass
class Allocation:
    """An active resource allocation."""
    id: str
    group_id: str
    resource_id: str
    requester_team: Optional[str] = None
    requester_user: Optional[str] = None
    allocated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    released_at: Optional[datetime] = None


class ResourceGroupManager:
    """
    Manages resource groups and allocation policies.
    
    **Requirement 14.1**: Create resource groups by labels
    **Requirement 14.2**: Enforce allocation policies
    **Requirement 14.3**: Validate group membership
    **Requirement 14.4**: Handle policy conflicts
    **Requirement 14.5**: Provide group statistics
    """
    
    def __init__(self):
        """Initialize the resource group manager."""
        # Groups by ID
        self._groups: Dict[str, ResourceGroup] = {}
        
        # Resource to group mapping (resource_id -> group_id)
        self._resource_groups: Dict[str, str] = {}
        
        # Active allocations by group
        self._allocations: Dict[str, List[Allocation]] = {}
        
        # Resource info cache (for statistics)
        self._resource_info: Dict[str, Dict[str, Any]] = {}
    
    def create_group(
        self,
        name: str,
        resource_type: ResourceType,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        allocation_policy: Optional[AllocationPolicy] = None
    ) -> ResourceGroup:
        """
        Create a new resource group.
        
        **Requirement 14.1**: Allow grouping by labels
        
        Args:
            name: Group name
            resource_type: Type of resources in this group
            description: Optional description
            labels: Labels for filtering
            allocation_policy: Allocation policy
            
        Returns:
            Created ResourceGroup
        """
        group = ResourceGroup(
            id=str(uuid4()),
            name=name,
            resource_type=resource_type,
            description=description,
            labels=labels or {},
            allocation_policy=allocation_policy or AllocationPolicy()
        )
        
        self._groups[group.id] = group
        self._allocations[group.id] = []
        
        logger.info(f"Created resource group: {name} ({group.id})")
        return group
    
    def get_group(self, group_id: str) -> Optional[ResourceGroup]:
        """Get a group by ID."""
        return self._groups.get(group_id)
    
    def get_group_by_name(self, name: str) -> Optional[ResourceGroup]:
        """Get a group by name."""
        for group in self._groups.values():
            if group.name == name:
                return group
        return None
    
    def list_groups(
        self,
        resource_type: Optional[ResourceType] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[ResourceGroup]:
        """
        List groups with optional filters.
        
        Args:
            resource_type: Filter by resource type
            labels: Filter by labels (all must match)
            
        Returns:
            List of matching groups
        """
        groups = list(self._groups.values())
        
        if resource_type:
            groups = [g for g in groups if g.resource_type == resource_type]
        
        if labels:
            groups = [
                g for g in groups
                if all(g.labels.get(k) == v for k, v in labels.items())
            ]
        
        return groups
    
    def update_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        allocation_policy: Optional[AllocationPolicy] = None
    ) -> Optional[ResourceGroup]:
        """
        Update a resource group.
        
        Args:
            group_id: Group ID
            name: New name
            description: New description
            labels: New labels
            allocation_policy: New policy
            
        Returns:
            Updated group or None if not found
        """
        group = self._groups.get(group_id)
        if not group:
            return None
        
        if name is not None:
            group.name = name
        if description is not None:
            group.description = description
        if labels is not None:
            group.labels = labels
        if allocation_policy is not None:
            group.allocation_policy = allocation_policy
        
        group.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated resource group: {group.name} ({group_id})")
        return group
    
    def delete_group(self, group_id: str) -> bool:
        """
        Delete a resource group.
        
        Args:
            group_id: Group ID
            
        Returns:
            True if deleted, False if not found
        """
        group = self._groups.get(group_id)
        if not group:
            return False
        
        # Remove resource associations
        for resource_id in group.member_ids:
            self._resource_groups.pop(resource_id, None)
        
        # Remove allocations
        self._allocations.pop(group_id, None)
        
        # Remove group
        del self._groups[group_id]
        
        logger.info(f"Deleted resource group: {group.name} ({group_id})")
        return True
    
    def add_resource_to_group(
        self,
        group_id: str,
        resource_id: str,
        resource_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a resource to a group.
        
        **Requirement 14.3**: Validate group membership
        
        Args:
            group_id: Group ID
            resource_id: Resource ID
            resource_info: Optional resource info for statistics
            
        Returns:
            True if added, False if group not found
        """
        group = self._groups.get(group_id)
        if not group:
            return False
        
        # Check if resource is already in another group
        existing_group = self._resource_groups.get(resource_id)
        if existing_group and existing_group != group_id:
            # Remove from existing group
            existing = self._groups.get(existing_group)
            if existing and resource_id in existing.member_ids:
                existing.member_ids.remove(resource_id)
        
        # Add to new group
        if resource_id not in group.member_ids:
            group.member_ids.append(resource_id)
        
        self._resource_groups[resource_id] = group_id
        
        if resource_info:
            self._resource_info[resource_id] = resource_info
        
        group.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Added resource {resource_id} to group {group.name}")
        return True
    
    def remove_resource_from_group(self, group_id: str, resource_id: str) -> bool:
        """
        Remove a resource from a group.
        
        Args:
            group_id: Group ID
            resource_id: Resource ID
            
        Returns:
            True if removed, False if not found
        """
        group = self._groups.get(group_id)
        if not group:
            return False
        
        if resource_id in group.member_ids:
            group.member_ids.remove(resource_id)
            self._resource_groups.pop(resource_id, None)
            group.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Removed resource {resource_id} from group {group.name}")
            return True
        
        return False
    
    def get_resource_group(self, resource_id: str) -> Optional[ResourceGroup]:
        """Get the group a resource belongs to."""
        group_id = self._resource_groups.get(resource_id)
        if group_id:
            return self._groups.get(group_id)
        return None
    
    def update_resource_info(
        self,
        resource_id: str,
        info: Dict[str, Any]
    ) -> None:
        """Update cached resource info for statistics."""
        self._resource_info[resource_id] = info
    
    def check_allocation_policy(
        self,
        group_id: str,
        requester_team: Optional[str] = None,
        requester_user: Optional[str] = None
    ) -> AllocationResult:
        """
        Check if an allocation is allowed by policy.
        
        **Requirement 14.2**: Enforce allocation policies
        
        Args:
            group_id: Group ID
            requester_team: Team requesting allocation
            requester_user: User requesting allocation
            
        Returns:
            AllocationResult with policy check results
        """
        group = self._groups.get(group_id)
        if not group:
            return AllocationResult(
                success=False,
                error_message="Group not found"
            )
        
        policy = group.allocation_policy
        violations = []
        
        # Check team restrictions
        if policy.reserved_for_teams and requester_team:
            if requester_team not in policy.reserved_for_teams:
                violations.append(
                    f"Group is reserved for teams: {', '.join(policy.reserved_for_teams)}"
                )
        
        # Check max concurrent allocations
        if policy.max_concurrent_allocations is not None:
            current = len([
                a for a in self._allocations.get(group_id, [])
                if a.released_at is None
            ])
            if current >= policy.max_concurrent_allocations:
                violations.append(
                    f"Max concurrent allocations reached: {current}/{policy.max_concurrent_allocations}"
                )
        
        # Check approval requirement
        if policy.require_approval:
            violations.append("Allocation requires approval")
        
        if violations:
            return AllocationResult(
                success=False,
                policy_violations=violations,
                error_message="; ".join(violations)
            )
        
        return AllocationResult(success=True)
    
    def allocate_resource(
        self,
        group_id: str,
        resource_id: str,
        requester_team: Optional[str] = None,
        requester_user: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> AllocationResult:
        """
        Allocate a resource from a group.
        
        **Requirement 14.2**: Enforce policies during allocation
        
        Args:
            group_id: Group ID
            resource_id: Resource ID to allocate
            requester_team: Team requesting allocation
            requester_user: User requesting allocation
            duration_seconds: Optional allocation duration
            
        Returns:
            AllocationResult
        """
        # Check policy first
        policy_result = self.check_allocation_policy(
            group_id, requester_team, requester_user
        )
        if not policy_result.success:
            return policy_result
        
        group = self._groups.get(group_id)
        if not group:
            return AllocationResult(
                success=False,
                error_message="Group not found"
            )
        
        # Verify resource is in group
        if resource_id not in group.member_ids:
            return AllocationResult(
                success=False,
                error_message="Resource not in group"
            )
        
        # Check if resource is already allocated
        for allocation in self._allocations.get(group_id, []):
            if allocation.resource_id == resource_id and allocation.released_at is None:
                return AllocationResult(
                    success=False,
                    error_message="Resource already allocated"
                )
        
        # Create allocation
        now = datetime.now(timezone.utc)
        expires_at = None
        
        if duration_seconds:
            from datetime import timedelta
            expires_at = now + timedelta(seconds=duration_seconds)
        elif group.allocation_policy.max_allocation_duration_seconds:
            from datetime import timedelta
            expires_at = now + timedelta(
                seconds=group.allocation_policy.max_allocation_duration_seconds
            )
        
        allocation = Allocation(
            id=str(uuid4()),
            group_id=group_id,
            resource_id=resource_id,
            requester_team=requester_team,
            requester_user=requester_user,
            allocated_at=now,
            expires_at=expires_at
        )
        
        if group_id not in self._allocations:
            self._allocations[group_id] = []
        self._allocations[group_id].append(allocation)
        
        logger.info(f"Allocated resource {resource_id} from group {group.name}")
        
        return AllocationResult(
            success=True,
            resource_id=resource_id,
            allocation_id=allocation.id
        )
    
    def release_allocation(self, allocation_id: str) -> bool:
        """
        Release a resource allocation.
        
        Args:
            allocation_id: Allocation ID
            
        Returns:
            True if released, False if not found
        """
        for group_id, allocations in self._allocations.items():
            for allocation in allocations:
                if allocation.id == allocation_id and allocation.released_at is None:
                    allocation.released_at = datetime.now(timezone.utc)
                    logger.info(f"Released allocation {allocation_id}")
                    return True
        
        return False
    
    def get_active_allocations(self, group_id: str) -> List[Allocation]:
        """Get active allocations for a group."""
        return [
            a for a in self._allocations.get(group_id, [])
            if a.released_at is None
        ]
    
    def get_group_statistics(self, group_id: str) -> Optional[GroupStatistics]:
        """
        Get aggregate statistics for a group.
        
        **Requirement 14.5**: Display aggregate capacity and utilization
        
        Args:
            group_id: Group ID
            
        Returns:
            GroupStatistics or None if group not found
        """
        group = self._groups.get(group_id)
        if not group:
            return None
        
        # Initialize counters
        total_members = len(group.member_ids)
        online_members = 0
        offline_members = 0
        maintenance_members = 0
        
        total_cpu = 0
        total_memory = 0
        total_storage = 0
        
        cpu_sum = 0.0
        memory_sum = 0.0
        storage_sum = 0.0
        utilization_count = 0
        
        active_workloads = 0
        queued_workloads = 0
        
        # Aggregate from resource info
        for resource_id in group.member_ids:
            info = self._resource_info.get(resource_id, {})
            
            # Status
            status = info.get("status", "unknown")
            if status == "online" or status == "available":
                online_members += 1
            elif status == "offline":
                offline_members += 1
            elif status == "maintenance":
                maintenance_members += 1
            
            # Capacity
            total_cpu += info.get("total_cpu_cores", 0)
            total_memory += info.get("total_memory_mb", 0)
            total_storage += info.get("total_storage_gb", 0)
            
            # Utilization
            if "cpu_percent" in info:
                cpu_sum += info["cpu_percent"]
                utilization_count += 1
            if "memory_percent" in info:
                memory_sum += info["memory_percent"]
            if "storage_percent" in info:
                storage_sum += info["storage_percent"]
            
            # Workloads
            active_workloads += info.get("active_workloads", 0)
            queued_workloads += info.get("queued_workloads", 0)
        
        # Calculate averages
        avg_cpu = cpu_sum / utilization_count if utilization_count > 0 else 0.0
        avg_memory = memory_sum / utilization_count if utilization_count > 0 else 0.0
        avg_storage = storage_sum / utilization_count if utilization_count > 0 else 0.0
        
        # Current allocations
        current_allocations = len(self.get_active_allocations(group_id))
        
        return GroupStatistics(
            group_id=group_id,
            group_name=group.name,
            resource_type=group.resource_type,
            total_members=total_members,
            online_members=online_members,
            offline_members=offline_members,
            maintenance_members=maintenance_members,
            total_cpu_cores=total_cpu,
            total_memory_mb=total_memory,
            total_storage_gb=total_storage,
            avg_cpu_percent=avg_cpu,
            avg_memory_percent=avg_memory,
            avg_storage_percent=avg_storage,
            active_workloads=active_workloads,
            queued_workloads=queued_workloads,
            current_allocations=current_allocations,
            max_allocations=group.allocation_policy.max_concurrent_allocations
        )
    
    def is_resource_in_maintenance(self, resource_id: str) -> bool:
        """
        Check if a resource is in maintenance mode.
        
        **Requirement 12.1**: Maintenance mode blocks allocations
        
        Args:
            resource_id: Resource ID
            
        Returns:
            True if in maintenance
        """
        info = self._resource_info.get(resource_id, {})
        return info.get("maintenance_mode", False) or info.get("status") == "maintenance"
    
    def has_active_workloads(self, resource_id: str) -> bool:
        """
        Check if a resource has active workloads.
        
        **Requirement 12.4**: Decommission requires no active workloads
        
        Args:
            resource_id: Resource ID
            
        Returns:
            True if has active workloads
        """
        info = self._resource_info.get(resource_id, {})
        
        # Check various workload indicators
        if info.get("active_workloads", 0) > 0:
            return True
        if info.get("active_build_count", 0) > 0:
            return True
        if info.get("running_vm_count", 0) > 0:
            return True
        if info.get("assigned_test_id") is not None:
            return True
        
        # Check allocations
        group_id = self._resource_groups.get(resource_id)
        if group_id:
            for allocation in self._allocations.get(group_id, []):
                if allocation.resource_id == resource_id and allocation.released_at is None:
                    return True
        
        return False
    
    def can_decommission(self, resource_id: str, force: bool = False) -> tuple[bool, str]:
        """
        Check if a resource can be decommissioned.
        
        **Requirement 12.4**: Decommission requires no active workloads
        
        Args:
            resource_id: Resource ID
            force: Force decommission even with active workloads
            
        Returns:
            Tuple of (can_decommission, reason)
        """
        if force:
            return True, "Force decommission requested"
        
        if self.has_active_workloads(resource_id):
            return False, "Resource has active workloads"
        
        return True, "Resource can be decommissioned"
    
    def get_resources_by_labels(
        self,
        resource_type: ResourceType,
        labels: Dict[str, str]
    ) -> List[str]:
        """
        Get resources matching labels.
        
        Args:
            resource_type: Resource type
            labels: Labels to match
            
        Returns:
            List of matching resource IDs
        """
        matching = []
        
        for group in self._groups.values():
            if group.resource_type != resource_type:
                continue
            
            # Check if group labels match
            if all(group.labels.get(k) == v for k, v in labels.items()):
                matching.extend(group.member_ids)
        
        return matching
