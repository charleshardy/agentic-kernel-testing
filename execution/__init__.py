"""Test execution and environment management module."""

from execution.hardware_config import (
    HardwareConfigParser,
    TestMatrixGenerator,
    HardwareCapabilityDetector,
    HardwareClassifier,
    TestMatrix,
    HardwareCapability
)

from execution.concurrency_testing import (
    ThreadScheduler,
    ThreadScheduleConfig,
    SchedulingStrategy,
    ConcurrencyTimingInjector,
    ConcurrencyTestRunner,
    ConcurrencyTestResult,
    ConcurrencyTestRun
)

__version__ = "0.1.0"

__all__ = [
    'HardwareConfigParser',
    'TestMatrixGenerator',
    'HardwareCapabilityDetector',
    'HardwareClassifier',
    'TestMatrix',
    'HardwareCapability',
    'ThreadScheduler',
    'ThreadScheduleConfig',
    'SchedulingStrategy',
    'ConcurrencyTimingInjector',
    'ConcurrencyTestRunner',
    'ConcurrencyTestResult',
    'ConcurrencyTestRun'
]
