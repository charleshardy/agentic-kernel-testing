"""Property-based tests for fault injection diversity.

**Feature: agentic-kernel-testing, Property 11: Fault injection diversity**

This module tests that stress testing includes all specified fault types:
memory allocation failures, I/O errors, and timing variations.

**Validates: Requirements 3.1**
"""

import pytest
from hypothesis import given, strategies as st, settings
from execution.fault_injection import (
    FaultInjectionSystem,
    FaultInjectionConfig,
    FaultType,
    MemoryAllocationFailureInjector,
    IOErrorInjector,
    TimingVariationInjector
)


# Custom strategies for fault injection testing
@st.composite
def fault_type_lists(draw):
    """Generate lists of fault types with at least one type."""
    # Ensure we have at least one fault type
    fault_types = [
        FaultType.MEMORY_ALLOCATION_FAILURE,
        FaultType.IO_ERROR,
        FaultType.TIMING_VARIATION
    ]
    
    # Draw a subset of fault types (at least 1)
    num_types = draw(st.integers(min_value=1, max_value=3))
    selected = draw(st.lists(
        st.sampled_from(fault_types),
        min_size=num_types,
        max_size=num_types,
        unique=True
    ))
    
    return selected


@st.composite
def fault_injection_configs(draw):
    """Generate valid fault injection configurations."""
    enabled_types = draw(fault_type_lists())
    
    # Use small timing ranges to avoid long test times
    min_timing = draw(st.integers(min_value=0, max_value=2))
    max_timing = draw(st.integers(min_value=min_timing, max_value=min_timing + 3))
    
    config = FaultInjectionConfig(
        enabled_fault_types=enabled_types,
        memory_failure_rate=draw(st.floats(min_value=0.0, max_value=1.0)),
        io_error_rate=draw(st.floats(min_value=0.0, max_value=1.0)),
        timing_variation_range_ms=(min_timing, max_timing),
        seed=draw(st.integers(min_value=0, max_value=10000))
    )
    
    return config


class TestFaultInjectionDiversity:
    """Test suite for fault injection diversity property."""
    
    @given(config=fault_injection_configs())
    @settings(max_examples=100)
    def test_property_fault_injection_diversity(self, config):
        """
        **Feature: agentic-kernel-testing, Property 11: Fault injection diversity**
        
        Property: For any stress test execution, the injected faults should include
        all specified types: memory allocation failures, I/O errors, and timing variations.
        
        **Validates: Requirements 3.1**
        
        This test verifies that when a fault injection system is configured with
        specific fault types, all those types are available and can be injected.
        """
        # Create fault injection system with the configuration
        system = FaultInjectionSystem(config)
        
        # Get enabled fault types from the system
        enabled_types = system.get_enabled_fault_types()
        
        # Property: All configured fault types should be enabled
        assert set(enabled_types) == set(config.enabled_fault_types), \
            f"Enabled types {enabled_types} don't match configured types {config.enabled_fault_types}"
        
        # Property: Each enabled fault type should have a corresponding injector
        for fault_type in config.enabled_fault_types:
            if fault_type == FaultType.MEMORY_ALLOCATION_FAILURE:
                assert system.memory_injector is not None, \
                    "Memory injector should be initialized when memory faults are enabled"
                assert isinstance(system.memory_injector, MemoryAllocationFailureInjector)
            
            elif fault_type == FaultType.IO_ERROR:
                assert system.io_injector is not None, \
                    "I/O injector should be initialized when I/O faults are enabled"
                assert isinstance(system.io_injector, IOErrorInjector)
            
            elif fault_type == FaultType.TIMING_VARIATION:
                assert system.timing_injector is not None, \
                    "Timing injector should be initialized when timing faults are enabled"
                assert isinstance(system.timing_injector, TimingVariationInjector)
    
    @given(config=fault_injection_configs())
    @settings(max_examples=100)
    def test_all_fault_types_can_be_injected(self, config):
        """
        Test that all enabled fault types can actually be injected.
        
        This verifies that the injection methods work for all configured types.
        """
        system = FaultInjectionSystem(config)
        
        # Try to inject each enabled fault type
        for fault_type in config.enabled_fault_types:
            if fault_type == FaultType.MEMORY_ALLOCATION_FAILURE:
                # Memory injection should return None or MemoryError
                result = system.inject_memory_failure("test_location")
                assert result is None or isinstance(result, MemoryError)
            
            elif fault_type == FaultType.IO_ERROR:
                # I/O injection should return None or IOError
                result = system.inject_io_error("test_location", "read")
                assert result is None or isinstance(result, IOError)
            
            elif fault_type == FaultType.TIMING_VARIATION:
                # Timing injection should return a non-negative delay
                delay = system.inject_timing_variation("test_location")
                assert delay >= 0.0
    
    @given(
        memory_rate=st.floats(min_value=0.0, max_value=1.0),
        io_rate=st.floats(min_value=0.0, max_value=1.0),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=100)
    def test_complete_fault_type_coverage(self, memory_rate, io_rate, seed):
        """
        Test that when all three fault types are enabled, all three are available.
        
        This is the core diversity property: all fault types should be present.
        """
        # Configure with all three fault types
        config = FaultInjectionConfig(
            enabled_fault_types=[
                FaultType.MEMORY_ALLOCATION_FAILURE,
                FaultType.IO_ERROR,
                FaultType.TIMING_VARIATION
            ],
            memory_failure_rate=memory_rate,
            io_error_rate=io_rate,
            timing_variation_range_ms=(0, 100),
            seed=seed
        )
        
        system = FaultInjectionSystem(config)
        
        # Property: All three injectors should be initialized
        assert system.memory_injector is not None, \
            "Memory injector must be present for complete fault diversity"
        assert system.io_injector is not None, \
            "I/O injector must be present for complete fault diversity"
        assert system.timing_injector is not None, \
            "Timing injector must be present for complete fault diversity"
        
        # Property: All three fault types should be in enabled list
        enabled = system.get_enabled_fault_types()
        assert FaultType.MEMORY_ALLOCATION_FAILURE in enabled
        assert FaultType.IO_ERROR in enabled
        assert FaultType.TIMING_VARIATION in enabled
        assert len(enabled) == 3
    
    @given(config=fault_injection_configs())
    @settings(max_examples=100)
    def test_statistics_track_all_enabled_types(self, config):
        """
        Test that statistics are collected for all enabled fault types.
        """
        # Override timing range to be very small to avoid long test times
        if FaultType.TIMING_VARIATION in config.enabled_fault_types:
            config.timing_variation_range_ms = (0, 1)  # Max 1ms delay
        
        system = FaultInjectionSystem(config)
        
        # Perform some injections (reduced to 3 to speed up tests)
        for _ in range(3):
            system.inject_memory_failure("test")
            system.inject_io_error("test", "write")
            system.inject_timing_variation("test")
        
        # Get statistics
        stats = system.get_all_statistics()
        
        # Property: Statistics should include all enabled fault types
        assert "enabled_fault_types" in stats
        assert set(stats["enabled_fault_types"]) == set(
            ft.value for ft in config.enabled_fault_types
        )
        
        # Property: Each enabled type should have statistics
        for fault_type in config.enabled_fault_types:
            if fault_type == FaultType.MEMORY_ALLOCATION_FAILURE:
                assert "memory" in stats["injectors"]
                assert stats["injectors"]["memory"]["fault_type"] == FaultType.MEMORY_ALLOCATION_FAILURE.value
            
            elif fault_type == FaultType.IO_ERROR:
                assert "io" in stats["injectors"]
                assert stats["injectors"]["io"]["fault_type"] == FaultType.IO_ERROR.value
            
            elif fault_type == FaultType.TIMING_VARIATION:
                assert "timing" in stats["injectors"]
                assert stats["injectors"]["timing"]["fault_type"] == FaultType.TIMING_VARIATION.value
    
    def test_empty_configuration_has_no_injectors(self):
        """
        Test that a configuration with no enabled fault types has no injectors.
        """
        config = FaultInjectionConfig(enabled_fault_types=[])
        system = FaultInjectionSystem(config)
        
        assert system.memory_injector is None
        assert system.io_injector is None
        assert system.timing_injector is None
        assert len(system.get_enabled_fault_types()) == 0
    
    @given(
        min_delay=st.integers(min_value=0, max_value=2),
        max_delay=st.integers(min_value=2, max_value=5),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=100)
    def test_timing_variation_respects_range(self, min_delay, max_delay, seed):
        """
        Test that timing variations stay within configured range.
        """
        config = FaultInjectionConfig(
            enabled_fault_types=[FaultType.TIMING_VARIATION],
            timing_variation_range_ms=(min_delay, max_delay),
            seed=seed
        )
        
        system = FaultInjectionSystem(config)
        
        # Inject multiple timing variations (reduced to 5 to speed up tests)
        delays = []
        for _ in range(5):
            delay_seconds = system.inject_timing_variation("test")
            delay_ms = delay_seconds * 1000
            delays.append(delay_ms)
        
        # Property: All delays should be within the configured range
        for delay_ms in delays:
            assert min_delay <= delay_ms <= max_delay, \
                f"Delay {delay_ms}ms outside range [{min_delay}, {max_delay}]"
