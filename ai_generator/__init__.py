"""AI-powered test generation and analysis module."""

__version__ = "0.1.0"

from .models import (
    TestCase, TestResult, CodeAnalysis, FailureAnalysis,
    HardwareConfig, Environment, TestType, TestStatus,
    RiskLevel, EnvironmentStatus, Peripheral, ExpectedOutcome,
    ArtifactBundle, CoverageData, FailureInfo, Credentials,
    Function, Commit, FixSuggestion
)

from .interfaces import (
    ITestGenerator, ITestOrchestrator, IEnvironmentManager,
    ICoverageAnalyzer, IRootCauseAnalyzer, ISecurityScanner,
    IPerformanceMonitor
)

__all__ = [
    # Models
    "TestCase", "TestResult", "CodeAnalysis", "FailureAnalysis",
    "HardwareConfig", "Environment", "TestType", "TestStatus",
    "RiskLevel", "EnvironmentStatus", "Peripheral", "ExpectedOutcome",
    "ArtifactBundle", "CoverageData", "FailureInfo", "Credentials",
    "Function", "Commit", "FixSuggestion",
    # Interfaces
    "ITestGenerator", "ITestOrchestrator", "IEnvironmentManager",
    "ICoverageAnalyzer", "IRootCauseAnalyzer", "ISecurityScanner",
    "IPerformanceMonitor"
]
