"""Interface contracts for major components."""

from abc import ABC, abstractmethod
from typing import List, Optional
from .models import (
    TestCase, TestResult, CodeAnalysis, FailureAnalysis,
    HardwareConfig, Environment, CoverageData, Function,
    ArtifactBundle, Commit
)


class ITestGenerator(ABC):
    """Interface for AI test generation component."""
    
    @abstractmethod
    def analyze_code_changes(self, diff: str) -> CodeAnalysis:
        """Analyze code changes and identify affected areas.
        
        Args:
            diff: Git diff string showing code changes
            
        Returns:
            CodeAnalysis object with affected subsystems and impact
        """
        pass
    
    @abstractmethod
    def generate_test_cases(self, analysis: CodeAnalysis) -> List[TestCase]:
        """Generate test cases based on code analysis.
        
        Args:
            analysis: CodeAnalysis from analyze_code_changes
            
        Returns:
            List of generated TestCase objects
        """
        pass
    
    @abstractmethod
    def generate_property_tests(self, functions: List[Function]) -> List[TestCase]:
        """Generate property-based tests for functions.
        
        Args:
            functions: List of Function objects to test
            
        Returns:
            List of property-based TestCase objects
        """
        pass


class ITestOrchestrator(ABC):
    """Interface for test orchestration and scheduling."""
    
    @abstractmethod
    def schedule_tests(self, tests: List[TestCase], priority: int = 0) -> str:
        """Schedule tests for execution.
        
        Args:
            tests: List of TestCase objects to schedule
            priority: Priority level (higher = more urgent)
            
        Returns:
            Execution plan ID
        """
        pass
    
    @abstractmethod
    def execute_plan(self, plan_id: str) -> str:
        """Execute a test plan.
        
        Args:
            plan_id: ID of the test plan to execute
            
        Returns:
            Execution handle for monitoring
        """
        pass
    
    @abstractmethod
    def monitor_execution(self, handle: str) -> dict:
        """Monitor test execution status.
        
        Args:
            handle: Execution handle from execute_plan
            
        Returns:
            Dictionary with execution status and progress
        """
        pass
    
    @abstractmethod
    def cancel_execution(self, handle: str) -> None:
        """Cancel a running test execution.
        
        Args:
            handle: Execution handle to cancel
        """
        pass


class IEnvironmentManager(ABC):
    """Interface for test environment management."""
    
    @abstractmethod
    def provision_environment(self, config: HardwareConfig) -> Environment:
        """Provision a test environment with specified configuration.
        
        Args:
            config: HardwareConfig specifying environment requirements
            
        Returns:
            Provisioned Environment object
        """
        pass
    
    @abstractmethod
    def deploy_kernel(self, env: Environment, kernel_image: str) -> None:
        """Deploy a kernel image to an environment.
        
        Args:
            env: Target Environment
            kernel_image: Path to kernel image file
        """
        pass
    
    @abstractmethod
    def execute_test(self, env: Environment, test: TestCase) -> TestResult:
        """Execute a test in an environment.
        
        Args:
            env: Environment to run test in
            test: TestCase to execute
            
        Returns:
            TestResult with execution outcome
        """
        pass
    
    @abstractmethod
    def cleanup_environment(self, env: Environment) -> None:
        """Clean up and release an environment.
        
        Args:
            env: Environment to clean up
        """
        pass
    
    @abstractmethod
    def capture_artifacts(self, env: Environment) -> ArtifactBundle:
        """Capture artifacts from an environment.
        
        Args:
            env: Environment to capture from
            
        Returns:
            ArtifactBundle with logs, dumps, traces
        """
        pass


class ICoverageAnalyzer(ABC):
    """Interface for coverage analysis."""
    
    @abstractmethod
    def collect_coverage(self, test_result: TestResult) -> CoverageData:
        """Collect coverage data from a test result.
        
        Args:
            test_result: TestResult to extract coverage from
            
        Returns:
            CoverageData object
        """
        pass
    
    @abstractmethod
    def merge_coverage(self, data_list: List[CoverageData]) -> CoverageData:
        """Merge multiple coverage data sets.
        
        Args:
            data_list: List of CoverageData to merge
            
        Returns:
            Merged CoverageData
        """
        pass
    
    @abstractmethod
    def identify_gaps(self, coverage: CoverageData) -> List[str]:
        """Identify untested code paths.
        
        Args:
            coverage: CoverageData to analyze
            
        Returns:
            List of code path identifiers that are untested
        """
        pass
    
    @abstractmethod
    def generate_report(self, coverage: CoverageData) -> str:
        """Generate a coverage report.
        
        Args:
            coverage: CoverageData to report on
            
        Returns:
            Report string (HTML, JSON, or text)
        """
        pass


class IRootCauseAnalyzer(ABC):
    """Interface for root cause analysis."""
    
    @abstractmethod
    def analyze_failure(self, failure: TestResult) -> FailureAnalysis:
        """Analyze a test failure to determine root cause.
        
        Args:
            failure: TestResult with failure information
            
        Returns:
            FailureAnalysis with root cause and suggestions
        """
        pass
    
    @abstractmethod
    def correlate_with_changes(self, failure: TestResult, commits: List[Commit]) -> List[Commit]:
        """Correlate failure with recent code changes.
        
        Args:
            failure: TestResult with failure information
            commits: List of recent Commit objects
            
        Returns:
            List of suspicious Commit objects
        """
        pass
    
    @abstractmethod
    def group_failures(self, failures: List[TestResult]) -> dict:
        """Group related failures by root cause.
        
        Args:
            failures: List of TestResult objects with failures
            
        Returns:
            Dictionary mapping root cause to list of failures
        """
        pass


class ISecurityScanner(ABC):
    """Interface for security scanning."""
    
    @abstractmethod
    def static_analysis(self, code_path: str) -> List[dict]:
        """Perform static analysis on code.
        
        Args:
            code_path: Path to code to analyze
            
        Returns:
            List of security issues found
        """
        pass
    
    @abstractmethod
    def fuzz_interface(self, interface: str, duration: int) -> List[TestResult]:
        """Fuzz a kernel interface.
        
        Args:
            interface: Interface identifier to fuzz
            duration: Fuzzing duration in seconds
            
        Returns:
            List of TestResult objects from fuzzing
        """
        pass


class IPerformanceMonitor(ABC):
    """Interface for performance monitoring."""
    
    @abstractmethod
    def run_benchmarks(self, kernel_image: str, suite: str) -> dict:
        """Run performance benchmarks.
        
        Args:
            kernel_image: Path to kernel image
            suite: Benchmark suite name
            
        Returns:
            Dictionary of benchmark results
        """
        pass
    
    @abstractmethod
    def compare_with_baseline(self, results: dict, baseline: dict) -> dict:
        """Compare results with baseline.
        
        Args:
            results: Current benchmark results
            baseline: Baseline benchmark results
            
        Returns:
            Dictionary of differences
        """
        pass
    
    @abstractmethod
    def detect_regressions(self, diff: dict, threshold: float) -> List[str]:
        """Detect performance regressions.
        
        Args:
            diff: Performance difference from compare_with_baseline
            threshold: Regression threshold (e.g., 0.1 for 10%)
            
        Returns:
            List of regressed metrics
        """
        pass
