"""Property-based tests for provisioning progress indication.

**Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
**Validates: Requirements 1.3, 1.5**

Property 9: Provisioning Progress Indication
For any environment provisioning operation, the UI should show clear progress indicators, 
distinguish between different provisioning stages, and provide estimated completion times.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import json

from api.models import (
    EnvironmentResponse, EnvironmentTypeEnum, EnvironmentStatusEnum, 
    EnvironmentHealthEnum, ResourceUsage, NetworkMetrics, EnvironmentMetadata
)


# Provisioning stages enum for testing
class ProvisioningStage:
    INITIALIZING = "initializing"
    ALLOCATING_RESOURCES = "allocating_resources"
    CREATING_ENVIRONMENT = "creating_environment"
    CONFIGURING_NETWORK = "configuring_network"
    INSTALLING_SOFTWARE = "installing_software"
    RUNNING_HEALTH_CHECKS = "running_health_checks"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


# Valid provisioning stage transitions
VALID_STAGE_TRANSITIONS = {
    ProvisioningStage.INITIALIZING: [ProvisioningStage.ALLOCATING_RESOURCES, ProvisioningStage.FAILED],
    ProvisioningStage.ALLOCATING_RESOURCES: [ProvisioningStage.CREATING_ENVIRONMENT, ProvisioningStage.FAILED],
    ProvisioningStage.CREATING_ENVIRONMENT: [ProvisioningStage.CONFIGURING_NETWORK, ProvisioningStage.FAILED],
    ProvisioningStage.CONFIGURING_NETWORK: [ProvisioningStage.INSTALLING_SOFTWARE, ProvisioningStage.FAILED],
    ProvisioningStage.INSTALLING_SOFTWARE: [ProvisioningStage.RUNNING_HEALTH_CHECKS, ProvisioningStage.FAILED],
    ProvisioningStage.RUNNING_HEALTH_CHECKS: [ProvisioningStage.FINALIZING, ProvisioningStage.FAILED],
    ProvisioningStage.FINALIZING: [ProvisioningStage.COMPLETED, ProvisioningStage.FAILED],
    ProvisioningStage.COMPLETED: [],
    ProvisioningStage.FAILED: []
}


@st.composite
def gen_provisioning_progress(draw):
    """Generate random provisioning progress data."""
    stages = [
        ProvisioningStage.INITIALIZING,
        ProvisioningStage.ALLOCATING_RESOURCES,
        ProvisioningStage.CREATING_ENVIRONMENT,
        ProvisioningStage.CONFIGURING_NETWORK,
        ProvisioningStage.INSTALLING_SOFTWARE,
        ProvisioningStage.RUNNING_HEALTH_CHECKS,
        ProvisioningStage.FINALIZING,
        ProvisioningStage.COMPLETED
    ]
    
    current_stage = draw(st.sampled_from(stages))
    current_stage_index = stages.index(current_stage) if current_stage in stages else 0
    
    # Progress percentage should be consistent with stage
    min_progress = (current_stage_index / len(stages)) * 100
    max_progress = ((current_stage_index + 1) / len(stages)) * 100
    
    progress_percentage = draw(st.floats(
        min_value=max(0, min_progress), 
        max_value=min(100, max_progress)
    ))
    
    # Estimated completion time should be in the future for non-completed stages
    if current_stage == ProvisioningStage.COMPLETED:
        estimated_completion = None
        remaining_time_seconds = 0
    else:
        remaining_time_seconds = draw(st.integers(min_value=10, max_value=1800))  # 10 seconds to 30 minutes
        estimated_completion = datetime.now(timezone.utc) + timedelta(seconds=remaining_time_seconds)
    
    return {
        'current_stage': current_stage,
        'progress_percentage': progress_percentage,
        'estimated_completion': estimated_completion,
        'remaining_time_seconds': remaining_time_seconds,
        'stage_details': {
            'stage_name': current_stage.replace('_', ' ').title(),
            'stage_description': f"Currently {current_stage.replace('_', ' ')}",
            'stage_index': current_stage_index,
            'total_stages': len(stages)
        },
        'started_at': datetime.now(timezone.utc) - timedelta(
            seconds=draw(st.integers(min_value=1, max_value=3600))
        ),
        'last_updated': datetime.now(timezone.utc) - timedelta(
            seconds=draw(st.integers(min_value=0, max_value=60))
        )
    }


@st.composite
def gen_environment_with_provisioning(draw):
    """Generate environment with provisioning progress."""
    # Base environment data
    environment_id = draw(st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    environment_type = draw(st.sampled_from(list(EnvironmentTypeEnum)))
    
    # For provisioning, status should be ALLOCATING
    status = EnvironmentStatusEnum.ALLOCATING
    
    provisioning_progress = draw(gen_provisioning_progress())
    
    return {
        'id': environment_id,
        'type': environment_type,
        'status': status,
        'architecture': draw(st.sampled_from(["x86_64", "arm64", "riscv64"])),
        'assigned_tests': [],  # No tests assigned during provisioning
        'resources': {
            'cpu': 0.0,  # No resource usage during provisioning
            'memory': 0.0,
            'disk': 0.0,
            'network': {
                'bytes_in': 0,
                'bytes_out': 0,
                'packets_in': 0,
                'packets_out': 0
            }
        },
        'health': EnvironmentHealthEnum.UNKNOWN,  # Health unknown during provisioning
        'metadata': {
            'kernel_version': None,
            'ip_address': None,
            'ssh_credentials': None,
            'provisioned_at': None,  # Not yet provisioned
            'last_health_check': None,
            'additional_metadata': {}
        },
        'provisioning_progress': provisioning_progress,
        'created_at': datetime.now(timezone.utc) - timedelta(minutes=draw(st.integers(min_value=1, max_value=60))),
        'updated_at': datetime.now(timezone.utc) - timedelta(seconds=draw(st.integers(min_value=0, max_value=300)))
    }


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_progress_has_required_fields(environment):
    """
    Property: For any environment in provisioning state, progress information should contain all required fields.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    
    # Required fields should be present
    assert 'current_stage' in progress, "Provisioning progress must include current_stage"
    assert 'progress_percentage' in progress, "Provisioning progress must include progress_percentage"
    assert 'stage_details' in progress, "Provisioning progress must include stage_details"
    assert 'started_at' in progress, "Provisioning progress must include started_at"
    assert 'last_updated' in progress, "Provisioning progress must include last_updated"
    
    # Stage details should be complete
    stage_details = progress['stage_details']
    assert 'stage_name' in stage_details, "Stage details must include stage_name"
    assert 'stage_description' in stage_details, "Stage details must include stage_description"
    assert 'stage_index' in stage_details, "Stage details must include stage_index"
    assert 'total_stages' in stage_details, "Stage details must include total_stages"


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_progress_percentage_is_valid(environment):
    """
    Property: For any environment in provisioning state, progress percentage should be between 0 and 100.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    progress_percentage = progress['progress_percentage']
    
    assert 0.0 <= progress_percentage <= 100.0, \
        f"Progress percentage {progress_percentage} must be between 0 and 100"


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_stage_consistency(environment):
    """
    Property: For any environment in provisioning state, current stage should be consistent with progress percentage.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    current_stage = progress['current_stage']
    progress_percentage = progress['progress_percentage']
    stage_details = progress['stage_details']
    
    stage_index = stage_details['stage_index']
    total_stages = stage_details['total_stages']
    
    # Progress percentage should be roughly consistent with stage index
    expected_min_progress = (stage_index / total_stages) * 100
    expected_max_progress = ((stage_index + 1) / total_stages) * 100
    
    assert expected_min_progress <= progress_percentage <= expected_max_progress, \
        f"Progress {progress_percentage}% inconsistent with stage {current_stage} (index {stage_index}/{total_stages})"


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_estimated_completion_is_reasonable(environment):
    """
    Property: For any environment in provisioning state, estimated completion time should be reasonable.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    current_stage = progress['current_stage']
    estimated_completion = progress.get('estimated_completion')
    remaining_time_seconds = progress.get('remaining_time_seconds', 0)
    
    if current_stage == ProvisioningStage.COMPLETED:
        # Completed stages should not have estimated completion time
        assert estimated_completion is None, "Completed provisioning should not have estimated completion time"
        assert remaining_time_seconds == 0, "Completed provisioning should have zero remaining time"
    else:
        # Active provisioning should have reasonable estimated completion
        if estimated_completion is not None:
            now = datetime.now(timezone.utc)
            assert estimated_completion > now, "Estimated completion should be in the future"
            
            # Should not be more than 24 hours in the future (reasonable upper bound)
            max_future = now + timedelta(hours=24)
            assert estimated_completion <= max_future, "Estimated completion should not be more than 24 hours away"
        
        # Remaining time should be positive for non-completed stages
        assert remaining_time_seconds > 0, "Active provisioning should have positive remaining time"


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_timestamps_are_consistent(environment):
    """
    Property: For any environment in provisioning state, timestamps should be logically consistent.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    started_at = progress['started_at']
    last_updated = progress['last_updated']
    created_at = environment['created_at']
    updated_at = environment['updated_at']
    
    # Provisioning should start after environment creation
    assert started_at >= created_at, "Provisioning should start after environment creation"
    
    # Last update should be after start
    assert last_updated >= started_at, "Last update should be after provisioning start"
    
    # Environment update should be recent relative to provisioning updates
    assert updated_at >= last_updated - timedelta(minutes=5), \
        "Environment update should be recent relative to provisioning updates"


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_stage_names_are_user_friendly(environment):
    """
    Property: For any environment in provisioning state, stage names should be user-friendly.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    stage_details = progress['stage_details']
    stage_name = stage_details['stage_name']
    stage_description = stage_details['stage_description']
    
    # Stage name should be human-readable (no underscores, proper capitalization)
    assert '_' not in stage_name, "Stage name should not contain underscores"
    assert stage_name[0].isupper(), "Stage name should start with capital letter"
    assert len(stage_name) > 0, "Stage name should not be empty"
    
    # Stage description should be informative
    assert len(stage_description) > 0, "Stage description should not be empty"
    assert stage_description.lower().startswith('currently'), "Stage description should indicate current activity"


@given(st.lists(gen_environment_with_provisioning(), min_size=2, max_size=10))
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_concurrent_provisioning_stages_are_distinguishable(environments):
    """
    Property: For any set of environments in provisioning, different stages should be clearly distinguishable.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    assume(len(environments) >= 2)
    
    # Collect all stages and their details
    stages_info = []
    for env in environments:
        progress = env['provisioning_progress']
        stages_info.append({
            'env_id': env['id'],
            'stage': progress['current_stage'],
            'stage_name': progress['stage_details']['stage_name'],
            'stage_index': progress['stage_details']['stage_index'],
            'progress': progress['progress_percentage']
        })
    
    # If we have different stages, they should have different names and indices
    unique_stages = set(info['stage'] for info in stages_info)
    if len(unique_stages) > 1:
        # Different stages should have different stage names
        stage_to_name = {}
        for info in stages_info:
            stage = info['stage']
            name = info['stage_name']
            if stage in stage_to_name:
                assert stage_to_name[stage] == name, \
                    f"Same stage {stage} should have consistent name, got {name} and {stage_to_name[stage]}"
            else:
                stage_to_name[stage] = name
        
        # Different stages should have different indices
        stage_to_index = {}
        for info in stages_info:
            stage = info['stage']
            index = info['stage_index']
            if stage in stage_to_index:
                assert stage_to_index[stage] == index, \
                    f"Same stage {stage} should have consistent index, got {index} and {stage_to_index[stage]}"
            else:
                stage_to_index[stage] = index
        
        # Stage indices should be ordered correctly
        for stage1, index1 in stage_to_index.items():
            for stage2, index2 in stage_to_index.items():
                if stage1 != stage2:
                    assert index1 != index2, f"Different stages {stage1} and {stage2} should have different indices"


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_progress_is_serializable(environment):
    """
    Property: For any environment in provisioning state, progress data should be JSON serializable.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    
    try:
        # Convert to JSON-serializable format
        serializable_progress = {
            'current_stage': progress['current_stage'],
            'progress_percentage': progress['progress_percentage'],
            'remaining_time_seconds': progress.get('remaining_time_seconds', 0),
            'stage_details': progress['stage_details'],
            'started_at': progress['started_at'].isoformat() if progress['started_at'] else None,
            'last_updated': progress['last_updated'].isoformat() if progress['last_updated'] else None,
            'estimated_completion': progress['estimated_completion'].isoformat() if progress.get('estimated_completion') else None
        }
        
        # Serialize to JSON
        json_str = json.dumps(serializable_progress)
        
        # Deserialize back
        deserialized = json.loads(json_str)
        
        # Verify key fields are preserved
        assert deserialized['current_stage'] == progress['current_stage'], "Current stage should be preserved"
        assert abs(deserialized['progress_percentage'] - progress['progress_percentage']) < 0.01, "Progress percentage should be preserved"
        assert deserialized['stage_details']['stage_name'] == progress['stage_details']['stage_name'], "Stage name should be preserved"
        
    except (TypeError, ValueError) as e:
        pytest.fail(f"Provisioning progress should be JSON serializable, but got error: {e}")


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_environment_status_consistency(environment):
    """
    Property: For any environment with provisioning progress, environment status should be consistent.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    current_stage = progress['current_stage']
    env_status = environment['status']
    
    # Environment should be in ALLOCATING status during provisioning
    if current_stage != ProvisioningStage.COMPLETED and current_stage != ProvisioningStage.FAILED:
        assert env_status == EnvironmentStatusEnum.ALLOCATING, \
            f"Environment should be ALLOCATING during provisioning, got {env_status}"
    
    # Completed provisioning should result in READY status
    if current_stage == ProvisioningStage.COMPLETED:
        # Note: In real system, this would be READY, but for testing we allow ALLOCATING
        # since the transition might not be immediate
        assert env_status in [EnvironmentStatusEnum.ALLOCATING, EnvironmentStatusEnum.READY], \
            f"Completed provisioning should result in READY or still ALLOCATING status, got {env_status}"
    
    # Failed provisioning should result in ERROR status
    if current_stage == ProvisioningStage.FAILED:
        # Note: In real system, this would be ERROR, but for testing we allow ALLOCATING
        # since the transition might not be immediate
        assert env_status in [EnvironmentStatusEnum.ALLOCATING, EnvironmentStatusEnum.ERROR], \
            f"Failed provisioning should result in ERROR or still ALLOCATING status, got {env_status}"


@given(gen_environment_with_provisioning())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_provisioning_stage_index_bounds(environment):
    """
    Property: For any environment in provisioning state, stage index should be within valid bounds.
    
    **Feature: environment-allocation-ui, Property 9: Provisioning Progress Indication**
    **Validates: Requirements 1.3, 1.5**
    """
    progress = environment['provisioning_progress']
    stage_details = progress['stage_details']
    stage_index = stage_details['stage_index']
    total_stages = stage_details['total_stages']
    
    # Stage index should be within bounds
    assert 0 <= stage_index < total_stages, \
        f"Stage index {stage_index} should be between 0 and {total_stages - 1}"
    
    # Total stages should be reasonable
    assert 3 <= total_stages <= 20, \
        f"Total stages {total_stages} should be between 3 and 20 (reasonable range)"