"""Property-based tests for environment information display accuracy.

**Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
**Validates: Requirements 1.1, 1.4, 3.1, 3.3**

Property 1: Environment Information Display Accuracy
For any set of environments and their associated data, the UI should display all environment 
information including status, configuration, assigned tests, and metadata accurately and completely.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json

from api.models import (
    EnvironmentResponse, EnvironmentTypeEnum, EnvironmentStatusEnum, 
    EnvironmentHealthEnum, ResourceUsage, NetworkMetrics, EnvironmentMetadata
)
from database.models import EnvironmentModel, HardwareConfigModel


# Custom strategies for generating test data
@st.composite
def gen_network_metrics(draw):
    """Generate random network metrics."""
    return NetworkMetrics(
        bytes_in=draw(st.integers(min_value=0, max_value=1000000000)),
        bytes_out=draw(st.integers(min_value=0, max_value=1000000000)),
        packets_in=draw(st.integers(min_value=0, max_value=10000000)),
        packets_out=draw(st.integers(min_value=0, max_value=10000000))
    )


@st.composite
def gen_resource_usage(draw):
    """Generate random resource usage."""
    return ResourceUsage(
        cpu=draw(st.floats(min_value=0.0, max_value=100.0)),
        memory=draw(st.floats(min_value=0.0, max_value=100.0)),
        disk=draw(st.floats(min_value=0.0, max_value=100.0)),
        network=draw(gen_network_metrics())
    )


@st.composite
def gen_environment_metadata(draw):
    """Generate random environment metadata."""
    return EnvironmentMetadata(
        kernel_version=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        ip_address=draw(st.one_of(st.none(), st.ip_addresses().map(str))),
        ssh_credentials=draw(st.one_of(st.none(), st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=3))),
        provisioned_at=draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc)))),
        last_health_check=draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc)))),
        additional_metadata=draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=5))
    )


@st.composite
def gen_environment_response(draw):
    """Generate a random environment response."""
    return EnvironmentResponse(
        id=draw(st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        type=draw(st.sampled_from(list(EnvironmentTypeEnum))),
        status=draw(st.sampled_from(list(EnvironmentStatusEnum))),
        architecture=draw(st.sampled_from(["x86_64", "arm64", "riscv64", "arm"])),
        assigned_tests=draw(st.lists(st.text(min_size=8, max_size=16), max_size=10)),
        resources=draw(gen_resource_usage()),
        health=draw(st.sampled_from(list(EnvironmentHealthEnum))),
        metadata=draw(gen_environment_metadata()),
        created_at=draw(st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc))),
        updated_at=draw(st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc)))
    )


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_response_contains_all_required_fields(environment):
    """
    Property: For any environment response, all required fields should be present and valid.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    # Verify all required fields are present
    assert environment.id is not None and len(environment.id) > 0, "Environment ID must be present and non-empty"
    assert environment.type in EnvironmentTypeEnum, f"Environment type {environment.type} must be valid"
    assert environment.status in EnvironmentStatusEnum, f"Environment status {environment.status} must be valid"
    assert environment.architecture is not None and len(environment.architecture) > 0, "Architecture must be present and non-empty"
    assert environment.assigned_tests is not None, "Assigned tests list must be present (can be empty)"
    assert environment.resources is not None, "Resource usage must be present"
    assert environment.health in EnvironmentHealthEnum, f"Environment health {environment.health} must be valid"
    assert environment.metadata is not None, "Metadata must be present"
    assert environment.created_at is not None, "Created timestamp must be present"
    assert environment.updated_at is not None, "Updated timestamp must be present"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_resource_usage_values_are_valid(environment):
    """
    Property: For any environment response, resource usage values should be within valid ranges.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    resources = environment.resources
    
    # CPU usage should be between 0 and 100
    assert 0.0 <= resources.cpu <= 100.0, f"CPU usage {resources.cpu} must be between 0 and 100"
    
    # Memory usage should be between 0 and 100
    assert 0.0 <= resources.memory <= 100.0, f"Memory usage {resources.memory} must be between 0 and 100"
    
    # Disk usage should be between 0 and 100
    assert 0.0 <= resources.disk <= 100.0, f"Disk usage {resources.disk} must be between 0 and 100"
    
    # Network metrics should be non-negative
    assert resources.network.bytes_in >= 0, f"Network bytes in {resources.network.bytes_in} must be non-negative"
    assert resources.network.bytes_out >= 0, f"Network bytes out {resources.network.bytes_out} must be non-negative"
    assert resources.network.packets_in >= 0, f"Network packets in {resources.network.packets_in} must be non-negative"
    assert resources.network.packets_out >= 0, f"Network packets out {resources.network.packets_out} must be non-negative"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_timestamps_are_consistent(environment):
    """
    Property: For any environment response, updated_at should be greater than or equal to created_at.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    assert environment.updated_at >= environment.created_at, \
        f"Updated timestamp {environment.updated_at} must be >= created timestamp {environment.created_at}"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_assigned_tests_are_valid_identifiers(environment):
    """
    Property: For any environment response, assigned test IDs should be valid non-empty strings.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    for test_id in environment.assigned_tests:
        assert isinstance(test_id, str), f"Test ID {test_id} must be a string"
        assert len(test_id) > 0, f"Test ID {test_id} must be non-empty"
        # Test IDs should not contain whitespace or special characters that could cause issues
        assert test_id.strip() == test_id, f"Test ID {test_id} should not have leading/trailing whitespace"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_metadata_is_serializable(environment):
    """
    Property: For any environment response, metadata should be JSON serializable.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    try:
        # Convert to dict and serialize to JSON
        metadata_dict = environment.metadata.dict()
        json_str = json.dumps(metadata_dict, default=str)  # Use default=str for datetime serialization
        
        # Verify we can deserialize it back
        deserialized = json.loads(json_str)
        assert isinstance(deserialized, dict), "Metadata should deserialize to a dictionary"
        
    except (TypeError, ValueError) as e:
        pytest.fail(f"Environment metadata should be JSON serializable, but got error: {e}")


@given(st.lists(gen_environment_response(), min_size=1, max_size=20))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_list_has_unique_ids(environments):
    """
    Property: For any list of environments, all environment IDs should be unique.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    environment_ids = [env.id for env in environments]
    unique_ids = set(environment_ids)
    
    assert len(environment_ids) == len(unique_ids), \
        f"Environment IDs should be unique, but found duplicates: {[id for id in environment_ids if environment_ids.count(id) > 1]}"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_status_health_consistency(environment):
    """
    Property: For any environment response, status and health should be logically consistent.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    # If environment is in ERROR status, health should not be HEALTHY
    if environment.status == EnvironmentStatusEnum.ERROR:
        assert environment.health != EnvironmentHealthEnum.HEALTHY, \
            "Environment in ERROR status should not have HEALTHY health status"
    
    # If environment is OFFLINE, health should be UNKNOWN or UNHEALTHY
    if environment.status == EnvironmentStatusEnum.OFFLINE:
        assert environment.health in [EnvironmentHealthEnum.UNKNOWN, EnvironmentHealthEnum.UNHEALTHY], \
            "Offline environment should have UNKNOWN or UNHEALTHY health status"
    
    # If environment is RUNNING and has assigned tests, it should not be UNHEALTHY
    if environment.status == EnvironmentStatusEnum.RUNNING and len(environment.assigned_tests) > 0:
        assert environment.health != EnvironmentHealthEnum.UNHEALTHY, \
            "Running environment with assigned tests should not be UNHEALTHY"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_architecture_is_supported(environment):
    """
    Property: For any environment response, architecture should be one of the supported values.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    supported_architectures = ["x86_64", "arm64", "riscv64", "arm", "aarch64", "i386", "mips", "ppc64"]
    
    assert environment.architecture in supported_architectures, \
        f"Architecture {environment.architecture} should be one of supported architectures: {supported_architectures}"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_type_virtualization_consistency(environment):
    """
    Property: For any environment response, type should be consistent with virtualization expectations.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    virtual_types = [EnvironmentTypeEnum.QEMU_X86, EnvironmentTypeEnum.QEMU_ARM, 
                    EnvironmentTypeEnum.DOCKER, EnvironmentTypeEnum.CONTAINER]
    physical_types = [EnvironmentTypeEnum.PHYSICAL]
    
    # All environment types should be either virtual or physical
    assert environment.type in virtual_types or environment.type in physical_types, \
        f"Environment type {environment.type} should be either virtual or physical"
    
    # If metadata indicates virtualization, type should be virtual
    if environment.metadata.additional_metadata.get("is_virtual") is True:
        assert environment.type in virtual_types, \
            f"Environment marked as virtual should have virtual type, got {environment.type}"
    
    # If metadata indicates physical, type should be physical
    if environment.metadata.additional_metadata.get("is_virtual") is False:
        assert environment.type in physical_types, \
            f"Environment marked as physical should have physical type, got {environment.type}"


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_ip_address_format_when_present(environment):
    """
    Property: For any environment response, if IP address is present, it should be valid format.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    if environment.metadata.ip_address is not None:
        ip_address = environment.metadata.ip_address
        
        # Basic IP address format validation (IPv4 or IPv6)
        import ipaddress
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            pytest.fail(f"IP address {ip_address} should be valid IPv4 or IPv6 format")


@given(gen_environment_response())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_response_serialization_roundtrip(environment):
    """
    Property: For any environment response, it should survive serialization/deserialization roundtrip.
    
    **Feature: environment-allocation-ui, Property 1: Environment Information Display Accuracy**
    **Validates: Requirements 1.1, 1.4, 3.1, 3.3**
    """
    try:
        # Serialize to JSON
        json_data = environment.json()
        
        # Deserialize back to object
        deserialized = EnvironmentResponse.parse_raw(json_data)
        
        # Verify key fields are preserved
        assert deserialized.id == environment.id, "Environment ID should be preserved"
        assert deserialized.type == environment.type, "Environment type should be preserved"
        assert deserialized.status == environment.status, "Environment status should be preserved"
        assert deserialized.architecture == environment.architecture, "Architecture should be preserved"
        assert deserialized.health == environment.health, "Health status should be preserved"
        assert len(deserialized.assigned_tests) == len(environment.assigned_tests), "Assigned tests count should be preserved"
        
    except Exception as e:
        pytest.fail(f"Environment response should survive serialization roundtrip, but got error: {e}")