"""Fault injection system for stress testing.

This module provides functionality for:
- Memory allocation failure injection
- I/O error injection
- Timing variation injection
- Fault injection configuration and control
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum


class FaultType(str, Enum):
    """Types of faults that can be injected."""
    MEMORY_ALLOCATION_FAILURE = "memory_allocation_failure"
    IO_ERROR = "io_error"
    TIMING_VARIATION = "timing_variation"


@dataclass
class FaultInjectionConfig:
    """Configuration for fault injection."""
    enabled_fault_types: List[FaultType] = field(default_factory=list)
    memory_failure_rate: float = 0.1  # 10% failure rate
    io_error_rate: float = 0.05  # 5% error rate
    timing_variation_range_ms: tuple = (0, 100)  # 0-100ms delay
    seed: Optional[int] = None  # For reproducibility
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.memory_failure_rate <= 1.0:
            raise ValueError("memory_failure_rate must be between 0.0 and 1.0")
        if not 0.0 <= self.io_error_rate <= 1.0:
            raise ValueError("io_error_rate must be between 0.0 and 1.0")
        if len(self.timing_variation_range_ms) != 2:
            raise ValueError("timing_variation_range_ms must be a tuple of (min, max)")
        if self.timing_variation_range_ms[0] < 0:
            raise ValueError("timing_variation_range_ms min must be non-negative")
        if self.timing_variation_range_ms[1] < self.timing_variation_range_ms[0]:
            raise ValueError("timing_variation_range_ms max must be >= min")


@dataclass
class FaultInjectionEvent:
    """Record of a fault injection event."""
    fault_type: FaultType
    timestamp: float
    location: str  # Where the fault was injected
    parameters: Dict[str, Any] = field(default_factory=dict)
    success: bool = True  # Whether injection succeeded


class MemoryAllocationFailureInjector:
    """Injector for memory allocation failures."""
    
    def __init__(self, failure_rate: float = 0.1, seed: Optional[int] = None):
        """Initialize memory allocation failure injector.
        
        Args:
            failure_rate: Probability of injection (0.0 to 1.0)
            seed: Random seed for reproducibility
        """
        if not 0.0 <= failure_rate <= 1.0:
            raise ValueError("failure_rate must be between 0.0 and 1.0")
        
        self.failure_rate = failure_rate
        self.rng = random.Random(seed)
        self.injection_count = 0
        self.events: List[FaultInjectionEvent] = []
    
    def should_inject(self) -> bool:
        """Determine if a fault should be injected.
        
        Returns:
            True if fault should be injected
        """
        return self.rng.random() < self.failure_rate
    
    def inject(self, location: str = "unknown") -> Optional[Exception]:
        """Inject a memory allocation failure.
        
        Args:
            location: Location identifier for the injection
            
        Returns:
            MemoryError exception if injection occurs, None otherwise
        """
        if self.should_inject():
            self.injection_count += 1
            event = FaultInjectionEvent(
                fault_type=FaultType.MEMORY_ALLOCATION_FAILURE,
                timestamp=time.time(),
                location=location,
                parameters={"injection_count": self.injection_count}
            )
            self.events.append(event)
            return MemoryError(f"Injected memory allocation failure at {location}")
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get injection statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "fault_type": FaultType.MEMORY_ALLOCATION_FAILURE.value,
            "injection_count": self.injection_count,
            "failure_rate": self.failure_rate,
            "total_events": len(self.events)
        }


class IOErrorInjector:
    """Injector for I/O errors."""
    
    def __init__(self, error_rate: float = 0.05, seed: Optional[int] = None):
        """Initialize I/O error injector.
        
        Args:
            error_rate: Probability of injection (0.0 to 1.0)
            seed: Random seed for reproducibility
        """
        if not 0.0 <= error_rate <= 1.0:
            raise ValueError("error_rate must be between 0.0 and 1.0")
        
        self.error_rate = error_rate
        self.rng = random.Random(seed)
        self.injection_count = 0
        self.events: List[FaultInjectionEvent] = []
    
    def should_inject(self) -> bool:
        """Determine if a fault should be injected.
        
        Returns:
            True if fault should be injected
        """
        return self.rng.random() < self.error_rate
    
    def inject(self, location: str = "unknown", operation: str = "read") -> Optional[Exception]:
        """Inject an I/O error.
        
        Args:
            location: Location identifier for the injection
            operation: Type of I/O operation (read, write, open, close)
            
        Returns:
            IOError exception if injection occurs, None otherwise
        """
        if self.should_inject():
            self.injection_count += 1
            event = FaultInjectionEvent(
                fault_type=FaultType.IO_ERROR,
                timestamp=time.time(),
                location=location,
                parameters={
                    "injection_count": self.injection_count,
                    "operation": operation
                }
            )
            self.events.append(event)
            return IOError(f"Injected I/O error during {operation} at {location}")
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get injection statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "fault_type": FaultType.IO_ERROR.value,
            "injection_count": self.injection_count,
            "error_rate": self.error_rate,
            "total_events": len(self.events)
        }


class TimingVariationInjector:
    """Injector for timing variations."""
    
    def __init__(
        self, 
        variation_range_ms: tuple = (0, 100), 
        seed: Optional[int] = None
    ):
        """Initialize timing variation injector.
        
        Args:
            variation_range_ms: Tuple of (min_ms, max_ms) for delay range
            seed: Random seed for reproducibility
        """
        if len(variation_range_ms) != 2:
            raise ValueError("variation_range_ms must be a tuple of (min, max)")
        if variation_range_ms[0] < 0:
            raise ValueError("variation_range_ms min must be non-negative")
        if variation_range_ms[1] < variation_range_ms[0]:
            raise ValueError("variation_range_ms max must be >= min")
        
        self.variation_range_ms = variation_range_ms
        self.rng = random.Random(seed)
        self.injection_count = 0
        self.events: List[FaultInjectionEvent] = []
    
    def inject(self, location: str = "unknown") -> float:
        """Inject a timing variation (delay).
        
        Args:
            location: Location identifier for the injection
            
        Returns:
            Delay in seconds that was injected
        """
        delay_ms = self.rng.uniform(
            self.variation_range_ms[0],
            self.variation_range_ms[1]
        )
        delay_seconds = delay_ms / 1000.0
        
        self.injection_count += 1
        event = FaultInjectionEvent(
            fault_type=FaultType.TIMING_VARIATION,
            timestamp=time.time(),
            location=location,
            parameters={
                "injection_count": self.injection_count,
                "delay_ms": delay_ms,
                "delay_seconds": delay_seconds
            }
        )
        self.events.append(event)
        
        # Actually inject the delay
        time.sleep(delay_seconds)
        
        return delay_seconds
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get injection statistics.
        
        Returns:
            Dictionary with statistics
        """
        delays = [e.parameters.get("delay_ms", 0) for e in self.events]
        avg_delay = sum(delays) / len(delays) if delays else 0.0
        
        return {
            "fault_type": FaultType.TIMING_VARIATION.value,
            "injection_count": self.injection_count,
            "variation_range_ms": self.variation_range_ms,
            "average_delay_ms": avg_delay,
            "total_events": len(self.events)
        }


class FaultInjectionSystem:
    """Unified fault injection system."""
    
    def __init__(self, config: Optional[FaultInjectionConfig] = None):
        """Initialize fault injection system.
        
        Args:
            config: Fault injection configuration
        """
        self.config = config or FaultInjectionConfig()
        
        # Initialize injectors based on configuration
        self.memory_injector: Optional[MemoryAllocationFailureInjector] = None
        self.io_injector: Optional[IOErrorInjector] = None
        self.timing_injector: Optional[TimingVariationInjector] = None
        
        if FaultType.MEMORY_ALLOCATION_FAILURE in self.config.enabled_fault_types:
            self.memory_injector = MemoryAllocationFailureInjector(
                failure_rate=self.config.memory_failure_rate,
                seed=self.config.seed
            )
        
        if FaultType.IO_ERROR in self.config.enabled_fault_types:
            self.io_injector = IOErrorInjector(
                error_rate=self.config.io_error_rate,
                seed=self.config.seed
            )
        
        if FaultType.TIMING_VARIATION in self.config.enabled_fault_types:
            self.timing_injector = TimingVariationInjector(
                variation_range_ms=self.config.timing_variation_range_ms,
                seed=self.config.seed
            )
    
    def inject_memory_failure(self, location: str = "unknown") -> Optional[Exception]:
        """Inject a memory allocation failure.
        
        Args:
            location: Location identifier
            
        Returns:
            Exception if injected, None otherwise
        """
        if self.memory_injector:
            return self.memory_injector.inject(location)
        return None
    
    def inject_io_error(
        self, 
        location: str = "unknown", 
        operation: str = "read"
    ) -> Optional[Exception]:
        """Inject an I/O error.
        
        Args:
            location: Location identifier
            operation: I/O operation type
            
        Returns:
            Exception if injected, None otherwise
        """
        if self.io_injector:
            return self.io_injector.inject(location, operation)
        return None
    
    def inject_timing_variation(self, location: str = "unknown") -> float:
        """Inject a timing variation.
        
        Args:
            location: Location identifier
            
        Returns:
            Delay in seconds (0.0 if not injected)
        """
        if self.timing_injector:
            return self.timing_injector.inject(location)
        return 0.0
    
    def get_enabled_fault_types(self) -> List[FaultType]:
        """Get list of enabled fault types.
        
        Returns:
            List of enabled fault types
        """
        return self.config.enabled_fault_types.copy()
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics from all injectors.
        
        Returns:
            Dictionary with statistics from all injectors
        """
        stats = {
            "enabled_fault_types": [ft.value for ft in self.config.enabled_fault_types],
            "injectors": {}
        }
        
        if self.memory_injector:
            stats["injectors"]["memory"] = self.memory_injector.get_statistics()
        
        if self.io_injector:
            stats["injectors"]["io"] = self.io_injector.get_statistics()
        
        if self.timing_injector:
            stats["injectors"]["timing"] = self.timing_injector.get_statistics()
        
        return stats
    
    def reset_statistics(self):
        """Reset all injection statistics."""
        if self.memory_injector:
            self.memory_injector.injection_count = 0
            self.memory_injector.events.clear()
        
        if self.io_injector:
            self.io_injector.injection_count = 0
            self.io_injector.events.clear()
        
        if self.timing_injector:
            self.timing_injector.injection_count = 0
            self.timing_injector.events.clear()
