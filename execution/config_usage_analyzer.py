"""Configuration usage analysis system.

This module provides functionality for:
- Tracking configuration option usage across test runs
- Identifying rarely-used or untested configuration options
- Collecting usage statistics and trends
- Generating usage reports and recommendations
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from execution.kernel_config_testing import KernelConfig, ConfigTestResult, ConfigType


logger = logging.getLogger(__name__)


class UsageFrequency(Enum):
    """Frequency categories for configuration option usage."""
    NEVER_USED = "never_used"
    RARELY_USED = "rarely_used"
    OCCASIONALLY_USED = "occasionally_used"
    FREQUENTLY_USED = "frequently_used"
    ALWAYS_USED = "always_used"


@dataclass
class ConfigOptionUsage:
    """Usage statistics for a single configuration option."""
    option_name: str
    total_tests: int = 0
    enabled_count: int = 0
    disabled_count: int = 0
    module_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    usage_frequency: UsageFrequency = UsageFrequency.NEVER_USED
    architectures_used: Set[str] = field(default_factory=set)
    config_types_used: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'option_name': self.option_name,
            'total_tests': self.total_tests,
            'enabled_count': self.enabled_count,
            'disabled_count': self.disabled_count,
            'module_count': self.module_count,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'usage_frequency': self.usage_frequency.value,
            'architectures_used': list(self.architectures_used),
            'config_types_used': list(self.config_types_used)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigOptionUsage':
        """Create from dictionary."""
        return cls(
            option_name=data['option_name'],
            total_tests=data.get('total_tests', 0),
            enabled_count=data.get('enabled_count', 0),
            disabled_count=data.get('disabled_count', 0),
            module_count=data.get('module_count', 0),
            first_seen=datetime.fromisoformat(data['first_seen']) if data.get('first_seen') else None,
            last_seen=datetime.fromisoformat(data['last_seen']) if data.get('last_seen') else None,
            usage_frequency=UsageFrequency(data.get('usage_frequency', 'never_used')),
            architectures_used=set(data.get('architectures_used', [])),
            config_types_used=set(data.get('config_types_used', []))
        )
    
    @property
    def usage_rate(self) -> float:
        """Calculate usage rate (enabled + module) / total."""
        if self.total_tests == 0:
            return 0.0
        return (self.enabled_count + self.module_count) / self.total_tests
    
    @property
    def enabled_rate(self) -> float:
        """Calculate enabled rate."""
        if self.total_tests == 0:
            return 0.0
        return self.enabled_count / self.total_tests


@dataclass
class UsageStatistics:
    """Overall usage statistics for configuration testing."""
    total_configurations_tested: int = 0
    total_unique_options: int = 0
    never_used_options: int = 0
    rarely_used_options: int = 0
    frequently_used_options: int = 0
    architecture_coverage: Dict[str, int] = field(default_factory=dict)
    config_type_coverage: Dict[str, int] = field(default_factory=dict)
    analysis_date: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_configurations_tested': self.total_configurations_tested,
            'total_unique_options': self.total_unique_options,
            'never_used_options': self.never_used_options,
            'rarely_used_options': self.rarely_used_options,
            'frequently_used_options': self.frequently_used_options,
            'architecture_coverage': self.architecture_coverage,
            'config_type_coverage': self.config_type_coverage,
            'analysis_date': self.analysis_date.isoformat()
        }


@dataclass
class UsageReport:
    """Comprehensive usage analysis report."""
    statistics: UsageStatistics
    option_usage: Dict[str, ConfigOptionUsage] = field(default_factory=dict)
    untested_options: List[str] = field(default_factory=list)
    rarely_used_options: List[str] = field(default_factory=list)
    architecture_specific_options: Dict[str, List[str]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'statistics': self.statistics.to_dict(),
            'option_usage': {k: v.to_dict() for k, v in self.option_usage.items()},
            'untested_options': self.untested_options,
            'rarely_used_options': self.rarely_used_options,
            'architecture_specific_options': self.architecture_specific_options,
            'recommendations': self.recommendations
        }


class ConfigUsageTracker:
    """Tracks configuration option usage across test runs."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize usage tracker.
        
        Args:
            storage_path: Path to store usage data (uses temp if None)
        """
        self.storage_path = storage_path or Path("config_usage_data.json")
        self.usage_data: Dict[str, ConfigOptionUsage] = {}
        self.load_usage_data()
    
    def track_configuration(self, config: KernelConfig, test_result: ConfigTestResult):
        """Track usage of a configuration in a test.
        
        Args:
            config: Kernel configuration that was tested
            test_result: Result of testing the configuration
        """
        logger.debug(f"Tracking usage for configuration: {config.name}")
        
        current_time = datetime.now()
        
        # Track each option in the configuration
        for option_name, option_value in config.options.items():
            if option_name not in self.usage_data:
                self.usage_data[option_name] = ConfigOptionUsage(
                    option_name=option_name,
                    first_seen=current_time
                )
            
            usage = self.usage_data[option_name]
            usage.total_tests += 1
            usage.last_seen = current_time
            
            # Count usage by value
            if option_value == 'y':
                usage.enabled_count += 1
            elif option_value == 'n':
                usage.disabled_count += 1
            elif option_value == 'm':
                usage.module_count += 1
            
            # Track architecture and config type usage
            usage.architectures_used.add(config.architecture)
            usage.config_types_used.add(config.config_type.value)
            
            # Update usage frequency
            usage.usage_frequency = self._calculate_usage_frequency(usage)
        
        # Save updated data
        self.save_usage_data()
    
    def _calculate_usage_frequency(self, usage: ConfigOptionUsage) -> UsageFrequency:
        """Calculate usage frequency category for an option.
        
        Args:
            usage: Option usage data
            
        Returns:
            Usage frequency category
        """
        if usage.total_tests == 0:
            return UsageFrequency.NEVER_USED
        
        usage_rate = usage.usage_rate
        
        if usage_rate == 0.0:
            return UsageFrequency.NEVER_USED
        elif usage_rate < 0.1:  # Less than 10%
            return UsageFrequency.RARELY_USED
        elif usage_rate < 0.5:  # Less than 50%
            return UsageFrequency.OCCASIONALLY_USED
        elif usage_rate < 0.9:  # Less than 90%
            return UsageFrequency.FREQUENTLY_USED
        else:  # 90% or more
            return UsageFrequency.ALWAYS_USED
    
    def get_usage_statistics(self) -> UsageStatistics:
        """Get overall usage statistics.
        
        Returns:
            Usage statistics summary
        """
        total_configs = max(usage.total_tests for usage in self.usage_data.values()) if self.usage_data else 0
        
        # Count options by frequency
        frequency_counts = Counter(usage.usage_frequency for usage in self.usage_data.values())
        
        # Count architecture coverage
        arch_coverage = defaultdict(int)
        for usage in self.usage_data.values():
            for arch in usage.architectures_used:
                arch_coverage[arch] += 1
        
        # Count config type coverage
        type_coverage = defaultdict(int)
        for usage in self.usage_data.values():
            for config_type in usage.config_types_used:
                type_coverage[config_type] += 1
        
        return UsageStatistics(
            total_configurations_tested=total_configs,
            total_unique_options=len(self.usage_data),
            never_used_options=frequency_counts[UsageFrequency.NEVER_USED],
            rarely_used_options=frequency_counts[UsageFrequency.RARELY_USED],
            frequently_used_options=frequency_counts[UsageFrequency.FREQUENTLY_USED],
            architecture_coverage=dict(arch_coverage),
            config_type_coverage=dict(type_coverage)
        )
    
    def load_usage_data(self):
        """Load usage data from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.usage_data = {
                        name: ConfigOptionUsage.from_dict(usage_dict)
                        for name, usage_dict in data.items()
                    }
                logger.info(f"Loaded usage data for {len(self.usage_data)} options")
            except Exception as e:
                logger.error(f"Failed to load usage data: {e}")
                self.usage_data = {}
        else:
            logger.info("No existing usage data found, starting fresh")
            self.usage_data = {}
    
    def save_usage_data(self):
        """Save usage data to storage."""
        try:
            data = {
                name: usage.to_dict()
                for name, usage in self.usage_data.items()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved usage data for {len(self.usage_data)} options")
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")


class RarelyUsedOptionIdentifier:
    """Identifies rarely-used configuration options."""
    
    def __init__(self, rarely_used_threshold: float = 0.1):
        """Initialize identifier.
        
        Args:
            rarely_used_threshold: Usage rate threshold for "rarely used" (default 10%)
        """
        self.rarely_used_threshold = rarely_used_threshold
    
    def identify_rarely_used_options(
        self,
        usage_data: Dict[str, ConfigOptionUsage],
        min_tests: int = 5
    ) -> List[str]:
        """Identify rarely-used configuration options.
        
        Args:
            usage_data: Usage data for all options
            min_tests: Minimum number of tests to consider an option
            
        Returns:
            List of rarely-used option names
        """
        rarely_used = []
        
        for option_name, usage in usage_data.items():
            # Skip options that haven't been tested enough
            if usage.total_tests < min_tests:
                continue
            
            # Check if usage rate is below threshold
            if usage.usage_rate < self.rarely_used_threshold:
                rarely_used.append(option_name)
        
        return sorted(rarely_used)
    
    def identify_untested_options(
        self,
        usage_data: Dict[str, ConfigOptionUsage],
        known_options: Optional[Set[str]] = None
    ) -> List[str]:
        """Identify completely untested configuration options.
        
        Args:
            usage_data: Usage data for all options
            known_options: Set of all known options (if available)
            
        Returns:
            List of untested option names
        """
        untested = []
        
        # Find options that have never been enabled or used as modules
        for option_name, usage in usage_data.items():
            if usage.enabled_count == 0 and usage.module_count == 0:
                untested.append(option_name)
        
        # If we have a list of known options, find ones not in usage data
        if known_options:
            for option in known_options:
                if option not in usage_data:
                    untested.append(option)
        
        return sorted(untested)
    
    def identify_architecture_specific_options(
        self,
        usage_data: Dict[str, ConfigOptionUsage]
    ) -> Dict[str, List[str]]:
        """Identify options that are specific to certain architectures.
        
        Args:
            usage_data: Usage data for all options
            
        Returns:
            Dictionary mapping architectures to their specific options
        """
        arch_specific = defaultdict(list)
        
        # Get all architectures seen
        all_architectures = set()
        for usage in usage_data.values():
            all_architectures.update(usage.architectures_used)
        
        # Find options used only on specific architectures
        for option_name, usage in usage_data.items():
            if len(usage.architectures_used) == 1:
                # Option used on only one architecture
                arch = list(usage.architectures_used)[0]
                arch_specific[arch].append(option_name)
            elif len(usage.architectures_used) > 1 and len(usage.architectures_used) < len(all_architectures):
                # Option used on some but not all architectures
                for arch in usage.architectures_used:
                    arch_specific[f"{arch}_partial"].append(option_name)
        
        return dict(arch_specific)


class UsageReportGenerator:
    """Generates comprehensive usage reports."""
    
    def __init__(self):
        """Initialize report generator."""
        self.identifier = RarelyUsedOptionIdentifier()
    
    def generate_usage_report(
        self,
        usage_data: Dict[str, ConfigOptionUsage],
        known_options: Optional[Set[str]] = None
    ) -> UsageReport:
        """Generate comprehensive usage report.
        
        Args:
            usage_data: Usage data for all options
            known_options: Set of all known options (if available)
            
        Returns:
            Comprehensive usage report
        """
        logger.info("Generating configuration usage report")
        
        # Calculate statistics
        statistics = self._calculate_statistics(usage_data)
        
        # Identify problematic options
        untested_options = self.identifier.identify_untested_options(usage_data, known_options)
        rarely_used_options = self.identifier.identify_rarely_used_options(usage_data)
        arch_specific_options = self.identifier.identify_architecture_specific_options(usage_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            statistics, untested_options, rarely_used_options, arch_specific_options
        )
        
        return UsageReport(
            statistics=statistics,
            option_usage=usage_data.copy(),
            untested_options=untested_options,
            rarely_used_options=rarely_used_options,
            architecture_specific_options=arch_specific_options,
            recommendations=recommendations
        )
    
    def _calculate_statistics(self, usage_data: Dict[str, ConfigOptionUsage]) -> UsageStatistics:
        """Calculate usage statistics from usage data."""
        if not usage_data:
            return UsageStatistics()
        
        total_configs = max(usage.total_tests for usage in usage_data.values())
        
        # Count by frequency
        frequency_counts = Counter(usage.usage_frequency for usage in usage_data.values())
        
        # Architecture coverage
        arch_coverage = defaultdict(int)
        for usage in usage_data.values():
            for arch in usage.architectures_used:
                arch_coverage[arch] += 1
        
        # Config type coverage
        type_coverage = defaultdict(int)
        for usage in usage_data.values():
            for config_type in usage.config_types_used:
                type_coverage[config_type] += 1
        
        return UsageStatistics(
            total_configurations_tested=total_configs,
            total_unique_options=len(usage_data),
            never_used_options=frequency_counts[UsageFrequency.NEVER_USED],
            rarely_used_options=frequency_counts[UsageFrequency.RARELY_USED],
            frequently_used_options=frequency_counts[UsageFrequency.FREQUENTLY_USED],
            architecture_coverage=dict(arch_coverage),
            config_type_coverage=dict(type_coverage)
        )
    
    def _generate_recommendations(
        self,
        statistics: UsageStatistics,
        untested_options: List[str],
        rarely_used_options: List[str],
        arch_specific_options: Dict[str, List[str]]
    ) -> List[str]:
        """Generate recommendations based on usage analysis."""
        recommendations = []
        
        # Recommendations for untested options
        if untested_options:
            recommendations.append(
                f"Consider testing {len(untested_options)} untested configuration options "
                f"to improve coverage"
            )
            if len(untested_options) > 10:
                recommendations.append(
                    "Focus on the most critical untested options first, such as "
                    "security, networking, and filesystem options"
                )
        
        # Recommendations for rarely used options
        if rarely_used_options:
            recommendations.append(
                f"Review {len(rarely_used_options)} rarely-used options to determine "
                f"if they should be deprecated or tested more thoroughly"
            )
        
        # Architecture coverage recommendations
        if len(statistics.architecture_coverage) < 3:
            recommendations.append(
                "Consider expanding testing to more architectures (arm64, riscv64) "
                "to improve cross-platform compatibility"
            )
        
        # Config type recommendations
        if statistics.config_type_coverage.get('minimal', 0) < statistics.total_configurations_tested / 3:
            recommendations.append(
                "Increase testing of minimal configurations to ensure embedded "
                "and resource-constrained deployments work correctly"
            )
        
        # Overall coverage recommendations
        coverage_rate = (statistics.total_unique_options - statistics.never_used_options) / statistics.total_unique_options if statistics.total_unique_options > 0 else 0
        if coverage_rate < 0.8:
            recommendations.append(
                f"Configuration option coverage is {coverage_rate:.1%}. "
                f"Consider adding more diverse test configurations to improve coverage"
            )
        
        return recommendations
    
    def export_report_json(self, report: UsageReport, output_path: Path):
        """Export usage report to JSON file.
        
        Args:
            report: Usage report to export
            output_path: Path to output JSON file
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            logger.info(f"Exported usage report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
    
    def export_report_text(self, report: UsageReport, output_path: Path):
        """Export usage report to human-readable text file.
        
        Args:
            report: Usage report to export
            output_path: Path to output text file
        """
        try:
            with open(output_path, 'w') as f:
                self._write_text_report(report, f)
            logger.info(f"Exported text report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export text report: {e}")
    
    def _write_text_report(self, report: UsageReport, file):
        """Write human-readable text report."""
        stats = report.statistics
        
        file.write("Configuration Usage Analysis Report\n")
        file.write("=" * 40 + "\n\n")
        
        # Summary statistics
        file.write("Summary Statistics:\n")
        file.write(f"  Total configurations tested: {stats.total_configurations_tested}\n")
        file.write(f"  Total unique options: {stats.total_unique_options}\n")
        file.write(f"  Never used options: {stats.never_used_options}\n")
        file.write(f"  Rarely used options: {stats.rarely_used_options}\n")
        file.write(f"  Frequently used options: {stats.frequently_used_options}\n\n")
        
        # Architecture coverage
        file.write("Architecture Coverage:\n")
        for arch, count in stats.architecture_coverage.items():
            file.write(f"  {arch}: {count} options\n")
        file.write("\n")
        
        # Config type coverage
        file.write("Configuration Type Coverage:\n")
        for config_type, count in stats.config_type_coverage.items():
            file.write(f"  {config_type}: {count} options\n")
        file.write("\n")
        
        # Untested options
        if report.untested_options:
            file.write(f"Untested Options ({len(report.untested_options)}):\n")
            for option in report.untested_options[:20]:  # Show first 20
                file.write(f"  {option}\n")
            if len(report.untested_options) > 20:
                file.write(f"  ... and {len(report.untested_options) - 20} more\n")
            file.write("\n")
        
        # Rarely used options
        if report.rarely_used_options:
            file.write(f"Rarely Used Options ({len(report.rarely_used_options)}):\n")
            for option in report.rarely_used_options[:20]:  # Show first 20
                usage = report.option_usage.get(option)
                if usage:
                    file.write(f"  {option} (usage: {usage.usage_rate:.1%})\n")
            if len(report.rarely_used_options) > 20:
                file.write(f"  ... and {len(report.rarely_used_options) - 20} more\n")
            file.write("\n")
        
        # Recommendations
        if report.recommendations:
            file.write("Recommendations:\n")
            for i, rec in enumerate(report.recommendations, 1):
                file.write(f"  {i}. {rec}\n")
            file.write("\n")


class ConfigUsageAnalyzer:
    """Main configuration usage analysis system."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize usage analyzer.
        
        Args:
            storage_path: Path to store usage data
        """
        self.tracker = ConfigUsageTracker(storage_path)
        self.report_generator = UsageReportGenerator()
    
    def analyze_configuration_usage(
        self,
        test_results: List[ConfigTestResult],
        known_options: Optional[Set[str]] = None
    ) -> UsageReport:
        """Analyze configuration usage from test results.
        
        Args:
            test_results: List of configuration test results
            known_options: Set of all known configuration options
            
        Returns:
            Comprehensive usage analysis report
        """
        logger.info(f"Analyzing usage for {len(test_results)} configuration test results")
        
        # Track usage for each test result
        for test_result in test_results:
            self.tracker.track_configuration(test_result.config, test_result)
        
        # Generate comprehensive report
        report = self.report_generator.generate_usage_report(
            self.tracker.usage_data, known_options
        )
        
        logger.info("Configuration usage analysis completed")
        return report
    
    def get_usage_statistics(self) -> UsageStatistics:
        """Get current usage statistics.
        
        Returns:
            Current usage statistics
        """
        return self.tracker.get_usage_statistics()
    
    def export_report(self, report: UsageReport, output_dir: Path):
        """Export usage report in multiple formats.
        
        Args:
            report: Usage report to export
            output_dir: Directory to save reports
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export JSON report
        json_path = output_dir / "config_usage_report.json"
        self.report_generator.export_report_json(report, json_path)
        
        # Export text report
        text_path = output_dir / "config_usage_report.txt"
        self.report_generator.export_report_text(report, text_path)
        
        logger.info(f"Exported usage reports to {output_dir}")