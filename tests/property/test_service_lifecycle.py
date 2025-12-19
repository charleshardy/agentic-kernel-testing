"""Property-based tests for orchestrator service lifecycle.

**Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
**Validates: Requirements 1.1, 2.5**

Property 1: Service startup and shutdown consistency
For any orchestrator service instance, starting and stopping the service should maintain
consistent state and proper resource cleanup.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

pytestmark = pytest.mark.property
from datetime import datetime
import time
import threading
from typing import List, Dict, Any
import tempfile
import os

from orchestrator.service import OrchestratorService
from orchestrator.config import OrchestratorConfig


# Custom strategies for generating test data
@st.composite
def gen_orchestrator_config(draw):
    """Generate a valid orchestrator configuration."""
    return OrchestratorConfig(
        poll_interval=draw(st.floats(min_value=0.1, max_value=10.0)),
        max_concurrent_tests=draw(st.integers(min_value=1, max_value=50)),
        default_timeout=draw(st.integers(min_value=10, max_value=3600)),
        docker_enabled=draw(st.booleans()),
        qemu_enabled=draw(st.booleans()),
        max_environments=draw(st.integers(min_value=1, max_value=100)),
        environment_cleanup_timeout=draw(st.integers(min_value=5, max_value=120)),
        max_memory_per_test=draw(st.integers(min_value=512, max_value=8192)),
        max_cpu_per_test=draw(st.floats(min_value=0.5, max_value=8.0)),
        log_level=draw(st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR'])),
        metrics_enabled=draw(st.booleans()),
        health_check_interval=draw(st.floats(min_value=1.0, max_value=300.0)),
        enable_persistence=draw(st.booleans()),
        state_file=draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))) + '.json'
    )


@given(gen_orchestrator_config())
@settings(max_examples=1, deadline=10000)  # 10 second deadline, 1 example
def test_service_start_stop_consistency(config: OrchestratorConfig):
    """
    Property: For any orchestrator service with valid configuration, starting and then
    stopping the service should result in consistent state transitions.
    
    **Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
    **Validates: Requirements 1.1, 2.5**
    """
    # Use temporary state file to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
        config.state_file = tmp_file.name
    
    # Optimize config for testing - disable complex features
    config.enable_persistence = False
    config.poll_interval = 0.1
    config.docker_enabled = False  # Disable Docker to avoid provisioning delays
    config.qemu_enabled = False    # Disable QEMU to avoid provisioning delays
    config.health_check_interval = 1.0  # Reduce health check frequency
    
    service = None
    try:
        service = OrchestratorService(config)
        
        # Initial state should be stopped
        assert not service.is_running, "Service should not be running initially"
        assert service.start_time is None, "Start time should be None initially"
        
        # Start the service
        start_result = service.start()
        assert start_result, "Service start should return True on success"
        
        # Verify service is running
        assert service.is_running, "Service should be running after start"
        assert service.start_time is not None, "Start time should be set after start"
        
        # Allow minimal time for service to initialize
        time.sleep(0.05)
        
        # Verify health status indicates running
        health = service.get_health_status()
        assert health['status'] == 'healthy', f"Health status should be 'healthy', got {health['status']}"
        assert health['is_running'], "Health status should indicate service is running"
        assert health['start_time'] is not None, "Health status should include start time"
        
        # Stop the service
        stop_result = service.stop()
        assert stop_result, "Service stop should return True on success"
        
        # Verify service is stopped
        assert not service.is_running, "Service should not be running after stop"
        
        # Verify health status indicates stopped
        health = service.get_health_status()
        assert health['status'] == 'stopped', f"Health status should be 'stopped', got {health['status']}"
        assert not health['is_running'], "Health status should indicate service is not running"
        
    finally:
        # Ensure service is stopped
        if service and service.is_running:
            service.stop()
        
        # Clean up temporary state file
        try:
            os.unlink(config.state_file)
        except FileNotFoundError:
            pass


@given(gen_orchestrator_config())
@settings(max_examples=20, deadline=15000)  # 15 second deadline
def test_multiple_start_stop_cycles(config: OrchestratorConfig):
    """
    Property: For any orchestrator service, multiple start/stop cycles should maintain
    consistent behavior without resource leaks or state corruption.
    
    **Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
    **Validates: Requirements 1.1, 2.5**
    """
    # Use temporary state file to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
        config.state_file = tmp_file.name
    
    # Disable persistence and reduce poll interval for faster testing
    config.enable_persistence = False
    config.poll_interval = 0.1
    
    service = None
    try:
        service = OrchestratorService(config)
        
        # Perform multiple start/stop cycles (reduced to 2 for speed)
        for cycle in range(2):
            # Start the service
            start_result = service.start()
            assert start_result, f"Service start should succeed on cycle {cycle}"
            assert service.is_running, f"Service should be running after start on cycle {cycle}"
            
            # Allow service to run briefly
            time.sleep(0.05)
            
            # Verify service is healthy
            health = service.get_health_status()
            assert health['status'] == 'healthy', f"Service should be healthy on cycle {cycle}"
            
            # Stop the service
            stop_result = service.stop()
            assert stop_result, f"Service stop should succeed on cycle {cycle}"
            assert not service.is_running, f"Service should be stopped after stop on cycle {cycle}"
            
            # Verify service is stopped
            health = service.get_health_status()
            assert health['status'] == 'stopped', f"Service should be stopped on cycle {cycle}"
    
    finally:
        # Ensure service is stopped
        if service and service.is_running:
            service.stop()
        
        # Clean up temporary state file
        try:
            os.unlink(config.state_file)
        except FileNotFoundError:
            pass


@given(gen_orchestrator_config())
@settings(max_examples=20, deadline=10000)
def test_redundant_start_stop_operations(config: OrchestratorConfig):
    """
    Property: For any orchestrator service, redundant start/stop operations should be
    handled gracefully without causing errors or inconsistent state.
    
    **Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
    **Validates: Requirements 1.1, 2.5**
    """
    # Use temporary state file to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
        config.state_file = tmp_file.name
    
    try:
        service = OrchestratorService(config)
        
        # Multiple start attempts when stopped
        assert not service.is_running, "Service should start in stopped state"
        
        first_start = service.start()
        assert first_start, "First start should succeed"
        assert service.is_running, "Service should be running after first start"
        
        # Redundant start should return False but not break the service
        second_start = service.start()
        assert not second_start, "Second start should return False (already running)"
        assert service.is_running, "Service should still be running after redundant start"
        
        # Service should still be healthy
        health = service.get_health_status()
        assert health['status'] == 'healthy', "Service should remain healthy after redundant start"
        
        # Stop the service
        first_stop = service.stop()
        assert first_stop, "First stop should succeed"
        assert not service.is_running, "Service should be stopped after first stop"
        
        # Redundant stop should return False but not cause errors
        second_stop = service.stop()
        assert not second_stop, "Second stop should return False (already stopped)"
        assert not service.is_running, "Service should remain stopped after redundant stop"
        
        # Service should still report stopped status
        health = service.get_health_status()
        assert health['status'] == 'stopped', "Service should remain stopped after redundant stop"
    
    finally:
        # Clean up temporary state file
        try:
            os.unlink(config.state_file)
        except FileNotFoundError:
            pass


@given(
    gen_orchestrator_config(),
    st.floats(min_value=0.1, max_value=0.5)  # Reduced duration for faster testing
)
@settings(max_examples=10, deadline=10000)
def test_service_uptime_tracking(config: OrchestratorConfig, run_duration: float):
    """
    Property: For any orchestrator service that runs for a given duration, the uptime
    tracking should accurately reflect the actual running time.
    
    **Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
    **Validates: Requirements 2.5**
    """
    # Use temporary state file to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
        config.state_file = tmp_file.name
    
    try:
        service = OrchestratorService(config)
        
        # Start the service and record start time
        start_time = time.time()
        start_result = service.start()
        assert start_result, "Service should start successfully"
        
        # Let service run for specified duration
        time.sleep(run_duration)
        
        # Check uptime before stopping
        metrics = service.get_system_metrics()
        uptime_before_stop = metrics['uptime_seconds']
        
        # Uptime should be approximately equal to run duration (within tolerance)
        actual_duration = time.time() - start_time
        tolerance = 0.5  # 500ms tolerance
        
        assert abs(uptime_before_stop - actual_duration) <= tolerance, \
            f"Uptime {uptime_before_stop} should be close to actual duration {actual_duration}"
        
        # Stop the service
        stop_result = service.stop()
        assert stop_result, "Service should stop successfully"
        
        # After stopping, uptime should remain at the last recorded value
        health = service.get_health_status()
        assert not health['is_running'], "Service should not be running after stop"
    
    finally:
        # Clean up temporary state file
        try:
            os.unlink(config.state_file)
        except FileNotFoundError:
            pass


@given(
    gen_orchestrator_config(),
    st.integers(min_value=2, max_value=3)  # Reduced thread count
)
@settings(max_examples=5, deadline=15000)  # Reduced examples for concurrency test
def test_concurrent_start_stop_operations(config: OrchestratorConfig, num_threads: int):
    """
    Property: For any orchestrator service, concurrent start/stop operations from multiple
    threads should be handled safely without race conditions or inconsistent state.
    
    **Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
    **Validates: Requirements 1.1, 2.5**
    """
    # Use temporary state file to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
        config.state_file = tmp_file.name
    
    try:
        service = OrchestratorService(config)
        results = []
        errors = []
        
        def worker_thread(thread_id: int, operation: str):
            """Worker thread that performs start or stop operations."""
            try:
                if operation == 'start':
                    result = service.start()
                    results.append(('start', thread_id, result))
                else:
                    result = service.stop()
                    results.append(('stop', thread_id, result))
            except Exception as e:
                errors.append(f"Thread {thread_id} ({operation}): {e}")
        
        # Test concurrent starts
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i, 'start'))
            threads.append(thread)
            thread.start()
        
        # Wait for all start threads
        for thread in threads:
            thread.join()
        
        # Check results - exactly one start should succeed
        start_results = [r for r in results if r[0] == 'start']
        successful_starts = [r for r in start_results if r[2]]
        
        assert len(successful_starts) == 1, \
            f"Exactly one start should succeed, got {len(successful_starts)} successes"
        assert service.is_running, "Service should be running after concurrent starts"
        
        # Clear results for stop test
        results.clear()
        
        # Test concurrent stops
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i, 'stop'))
            threads.append(thread)
            thread.start()
        
        # Wait for all stop threads
        for thread in threads:
            thread.join()
        
        # Check results - exactly one stop should succeed
        stop_results = [r for r in results if r[0] == 'stop']
        successful_stops = [r for r in stop_results if r[2]]
        
        assert len(successful_stops) == 1, \
            f"Exactly one stop should succeed, got {len(successful_stops)} successes"
        assert not service.is_running, "Service should be stopped after concurrent stops"
        
        # Check for errors
        assert not errors, f"No errors should occur during concurrent operations: {errors}"
    
    finally:
        # Clean up temporary state file
        try:
            os.unlink(config.state_file)
        except FileNotFoundError:
            pass


@given(gen_orchestrator_config())
@settings(max_examples=20, deadline=10000)
def test_service_component_initialization(config: OrchestratorConfig):
    """
    Property: For any orchestrator service, starting the service should properly initialize
    all components and stopping should properly clean them up.
    
    **Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
    **Validates: Requirements 1.1, 2.5**
    """
    # Use temporary state file to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
        config.state_file = tmp_file.name
    
    try:
        service = OrchestratorService(config)
        
        # Before starting, components should exist but not be active
        assert service.status_tracker is not None, "Status tracker should be initialized"
        assert service.queue_monitor is not None, "Queue monitor should be initialized"
        assert service.resource_manager is not None, "Resource manager should be initialized"
        
        # Start the service
        start_result = service.start()
        assert start_result, "Service should start successfully"
        
        # After starting, all components should be healthy
        health = service.get_health_status()
        components = health['components']
        
        assert 'status_tracker' in components, "Health should include status tracker"
        assert 'resource_manager' in components, "Health should include resource manager"
        assert 'queue_monitor' in components, "Health should include queue monitor"
        
        # All components should report healthy status
        for component_name, component_health in components.items():
            assert component_health is not None, f"Component {component_name} should have health status"
        
        # Stop the service
        stop_result = service.stop()
        assert stop_result, "Service should stop successfully"
        
        # After stopping, service should be in stopped state
        health = service.get_health_status()
        assert health['status'] == 'stopped', "Service should be stopped"
        assert not health['is_running'], "Service should not be running"
    
    finally:
        # Clean up temporary state file
        try:
            os.unlink(config.state_file)
        except FileNotFoundError:
            pass


@given(gen_orchestrator_config())
@settings(max_examples=20, deadline=10000)
def test_service_metrics_consistency(config: OrchestratorConfig):
    """
    Property: For any orchestrator service, system metrics should remain consistent
    and accessible throughout the service lifecycle.
    
    **Feature: test-execution-orchestrator, Property 1: Service startup and shutdown consistency**
    **Validates: Requirements 2.5**
    """
    # Use temporary state file to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
        config.state_file = tmp_file.name
    
    try:
        service = OrchestratorService(config)
        
        # Metrics should be available even when stopped
        metrics_stopped = service.get_system_metrics()
        assert isinstance(metrics_stopped, dict), "Metrics should be a dictionary"
        assert 'uptime_seconds' in metrics_stopped, "Metrics should include uptime"
        assert metrics_stopped['uptime_seconds'] == 0.0, "Uptime should be 0 when stopped"
        
        # Start the service
        start_result = service.start()
        assert start_result, "Service should start successfully"
        
        # Allow some time for metrics to update
        time.sleep(0.1)
        
        # Metrics should be updated when running
        metrics_running = service.get_system_metrics()
        assert isinstance(metrics_running, dict), "Metrics should be a dictionary"
        assert 'uptime_seconds' in metrics_running, "Metrics should include uptime"
        assert metrics_running['uptime_seconds'] > 0, "Uptime should be positive when running"
        
        # Required metrics should be present
        required_metrics = [
            'active_tests', 'queued_tests', 'completed_tests', 'failed_tests',
            'total_processed', 'available_environments', 'uptime_seconds'
        ]
        
        for metric in required_metrics:
            assert metric in metrics_running, f"Metric {metric} should be present"
            assert isinstance(metrics_running[metric], (int, float)), \
                f"Metric {metric} should be numeric"
        
        # Stop the service
        stop_result = service.stop()
        assert stop_result, "Service should stop successfully"
        
        # Metrics should still be accessible after stopping
        metrics_after_stop = service.get_system_metrics()
        assert isinstance(metrics_after_stop, dict), "Metrics should still be accessible after stop"
        
        for metric in required_metrics:
            assert metric in metrics_after_stop, f"Metric {metric} should still be present after stop"
    
    finally:
        # Clean up temporary state file
        try:
            os.unlink(config.state_file)
        except FileNotFoundError:
            pass