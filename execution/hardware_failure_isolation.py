"""Hardware failure isolation diagnostics system.

This module provides functionality for:
- Hardware-specific diagnostic collector
- Failure-to-hardware correlator
- Diagnostic report generator
"""

import re
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from datetime import datetime

from ai_generator.models import (
    HardwareConfig, TestResult, TestStatus, FailureInfo, Environment
)
from execution.fault_detection import DetectedFault, FaultCategory


class HardwareFailureType(str, Enum):
    """Types of hardware-specific failures."""
    MEMORY_ERROR = "memory_error"
    CPU_ERROR = "cpu_error"
    STORAGE_ERROR = "storage_error"
    NETWORK_ERROR = "network_error"
    PERIPHERAL_ERROR = "peripheral_error"
    POWER_ERROR = "power_error"
    THERMAL_ERROR = "thermal_error"
    UNKNOWN = "unknown"


@dataclass
class HardwareSpecificDiagnostic:
    """Hardware-specific diagnostic information."""
    hardware_id: str
    hardware_config: HardwareConfig
    failure_type: HardwareFailureType
    diagnostic_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hardware_id": self.hardware_id,
            "hardware_config": self.hardware_config.to_dict(),
            "failure_type": self.failure_type.value,
            "diagnostic_data": self.diagnostic_data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class HardwareFailureCorrelation:
    """Correlation between failure and hardware configuration."""
    failure_id: str
    hardware_id: str
    hardware_config: HardwareConfig
    correlation_score: float  # 0.0 to 1.0
    correlation_factors: List[str] = field(default_factory=list)
    diagnostic_evidence: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate correlation data."""
        if not 0.0 <= self.correlation_score <= 1.0:
            raise ValueError("correlation_score must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "failure_id": self.failure_id,
            "hardware_id": self.hardware_id,
            "hardware_config": self.hardware_config.to_dict(),
            "correlation_score": self.correlation_score,
            "correlation_factors": self.correlation_factors,
            "diagnostic_evidence": self.diagnostic_evidence
        }


@dataclass
class HardwareFailureReport:
    """Comprehensive hardware failure isolation report."""
    report_id: str
    failure_id: str
    hardware_id: str
    hardware_config: HardwareConfig
    failure_type: HardwareFailureType
    isolation_confidence: float  # 0.0 to 1.0
    diagnostics: List[HardwareSpecificDiagnostic] = field(default_factory=list)
    correlations: List[HardwareFailureCorrelation] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate report data."""
        if not 0.0 <= self.isolation_confidence <= 1.0:
            raise ValueError("isolation_confidence must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "failure_id": self.failure_id,
            "hardware_id": self.hardware_id,
            "hardware_config": self.hardware_config.to_dict(),
            "failure_type": self.failure_type.value,
            "isolation_confidence": self.isolation_confidence,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "correlations": [c.to_dict() for c in self.correlations],
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }


class HardwareSpecificDiagnosticCollector:
    """Collector for hardware-specific diagnostic information."""
    
    # Hardware-specific error patterns
    HARDWARE_ERROR_PATTERNS = {
        HardwareFailureType.MEMORY_ERROR: [
            r"Machine Check Exception",
            r"MCE: CPU \d+ BANK \d+",
            r"EDAC.*error",
            r"memory error",
            r"ECC.*error",
            r"DIMM.*error",
            r"Bad RAM",
            r"memory corruption"
        ],
        HardwareFailureType.CPU_ERROR: [
            r"CPU.*error",
            r"processor.*error",
            r"thermal throttling",
            r"CPU overheating",
            r"instruction cache error",
            r"CPU microcode",
            r"CPU.*exception"
        ],
        HardwareFailureType.STORAGE_ERROR: [
            r"I/O error.*dev",
            r"disk.*error",
            r"SATA.*error",
            r"NVMe.*error",
            r"block device.*error",
            r"filesystem.*error",
            r"bad sector",
            r"read.*error.*sector"
        ],
        HardwareFailureType.NETWORK_ERROR: [
            r"network.*error",
            r"ethernet.*error",
            r"link.*down",
            r"network interface.*error",
            r"PHY.*error",
            r"MAC.*error"
        ],
        HardwareFailureType.PERIPHERAL_ERROR: [
            r"USB.*error",
            r"PCI.*error",
            r"GPIO.*error",
            r"I2C.*error",
            r"SPI.*error",
            r"peripheral.*error"
        ],
        HardwareFailureType.POWER_ERROR: [
            r"power.*error",
            r"voltage.*error",
            r"power supply.*error",
            r"battery.*error",
            r"undervoltage",
            r"overvoltage"
        ],
        HardwareFailureType.THERMAL_ERROR: [
            r"thermal.*error",
            r"temperature.*critical",
            r"overheating",
            r"thermal shutdown",
            r"cooling.*error"
        ]
    }
    
    def __init__(self):
        """Initialize diagnostic collector."""
        self.collected_diagnostics: List[HardwareSpecificDiagnostic] = []
        self.compiled_patterns = {}
        
        # Compile regex patterns for efficiency
        for failure_type, patterns in self.HARDWARE_ERROR_PATTERNS.items():
            self.compiled_patterns[failure_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def collect_diagnostics(
        self,
        hardware_id: str,
        hardware_config: HardwareConfig,
        test_result: TestResult
    ) -> List[HardwareSpecificDiagnostic]:
        """Collect hardware-specific diagnostics from test result.
        
        Args:
            hardware_id: ID of the hardware
            hardware_config: Hardware configuration
            test_result: Test result to analyze
            
        Returns:
            List of hardware-specific diagnostics
        """
        diagnostics = []
        
        # Only analyze failed tests
        if test_result.status != TestStatus.FAILED:
            return diagnostics
        
        # Analyze logs for hardware-specific errors
        all_logs = "\n".join(test_result.artifacts.logs)
        
        for failure_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(all_logs)
                for match in matches:
                    diagnostic_data = self._extract_diagnostic_data(
                        failure_type, match, all_logs, hardware_config
                    )
                    
                    diagnostic = HardwareSpecificDiagnostic(
                        hardware_id=hardware_id,
                        hardware_config=hardware_config,
                        failure_type=failure_type,
                        diagnostic_data=diagnostic_data
                    )
                    
                    diagnostics.append(diagnostic)
                    self.collected_diagnostics.append(diagnostic)
        
        # If no specific hardware errors found but test failed, create generic diagnostic
        if not diagnostics and test_result.failure_info:
            diagnostic = self._create_generic_diagnostic(
                hardware_id, hardware_config, test_result.failure_info
            )
            diagnostics.append(diagnostic)
            self.collected_diagnostics.append(diagnostic)
        
        return diagnostics
    
    def _extract_diagnostic_data(
        self,
        failure_type: HardwareFailureType,
        match: re.Match,
        full_log: str,
        hardware_config: HardwareConfig
    ) -> Dict[str, Any]:
        """Extract detailed diagnostic data from log match.
        
        Args:
            failure_type: Type of hardware failure
            match: Regex match object
            full_log: Full log content
            hardware_config: Hardware configuration
            
        Returns:
            Dictionary with diagnostic data
        """
        diagnostic_data = {
            "matched_pattern": match.group(),
            "match_position": match.start(),
            "failure_type": failure_type.value,
            "hardware_architecture": hardware_config.architecture,
            "hardware_memory_mb": hardware_config.memory_mb,
            "is_virtual": hardware_config.is_virtual
        }
        
        # Extract context around the match
        lines = full_log.split('\n')
        match_line_idx = full_log[:match.start()].count('\n')
        
        # Get surrounding context
        start_idx = max(0, match_line_idx - 5)
        end_idx = min(len(lines), match_line_idx + 5)
        context = lines[start_idx:end_idx]
        diagnostic_data["context"] = context
        
        # Extract failure-type specific information
        if failure_type == HardwareFailureType.MEMORY_ERROR:
            diagnostic_data.update(self._extract_memory_error_details(match.group(), context))
        elif failure_type == HardwareFailureType.CPU_ERROR:
            diagnostic_data.update(self._extract_cpu_error_details(match.group(), context))
        elif failure_type == HardwareFailureType.STORAGE_ERROR:
            diagnostic_data.update(self._extract_storage_error_details(match.group(), context))
        elif failure_type == HardwareFailureType.NETWORK_ERROR:
            diagnostic_data.update(self._extract_network_error_details(match.group(), context))
        
        return diagnostic_data
    
    def _extract_memory_error_details(self, matched_text: str, context: List[str]) -> Dict[str, Any]:
        """Extract memory error specific details."""
        details = {}
        
        # Look for memory addresses, bank numbers, etc.
        for line in context:
            if "BANK" in line:
                bank_match = re.search(r"BANK (\d+)", line)
                if bank_match:
                    details["memory_bank"] = int(bank_match.group(1))
            
            if "DIMM" in line:
                dimm_match = re.search(r"DIMM (\d+)", line)
                if dimm_match:
                    details["dimm_slot"] = int(dimm_match.group(1))
            
            if "address" in line.lower():
                addr_match = re.search(r"0x[0-9a-fA-F]+", line)
                if addr_match:
                    details["memory_address"] = addr_match.group()
        
        return details
    
    def _extract_cpu_error_details(self, matched_text: str, context: List[str]) -> Dict[str, Any]:
        """Extract CPU error specific details."""
        details = {}
        
        for line in context:
            if "CPU" in line:
                cpu_match = re.search(r"CPU (\d+)", line)
                if cpu_match:
                    details["cpu_number"] = int(cpu_match.group(1))
            
            if "temperature" in line.lower():
                temp_match = re.search(r"(\d+)°?C", line)
                if temp_match:
                    details["temperature_celsius"] = int(temp_match.group(1))
        
        return details
    
    def _extract_storage_error_details(self, matched_text: str, context: List[str]) -> Dict[str, Any]:
        """Extract storage error specific details."""
        details = {}
        
        for line in context:
            if "sector" in line.lower():
                sector_match = re.search(r"sector (\d+)", line)
                if sector_match:
                    details["bad_sector"] = int(sector_match.group(1))
            
            if "dev" in line:
                dev_match = re.search(r"dev ([a-zA-Z0-9/]+)", line)
                if dev_match:
                    details["device"] = dev_match.group(1)
        
        return details
    
    def _extract_network_error_details(self, matched_text: str, context: List[str]) -> Dict[str, Any]:
        """Extract network error specific details."""
        details = {}
        
        for line in context:
            if "eth" in line or "wlan" in line:
                iface_match = re.search(r"(eth\d+|wlan\d+)", line)
                if iface_match:
                    details["network_interface"] = iface_match.group(1)
        
        return details
    
    def _create_generic_diagnostic(
        self,
        hardware_id: str,
        hardware_config: HardwareConfig,
        failure_info: FailureInfo
    ) -> HardwareSpecificDiagnostic:
        """Create generic diagnostic for non-hardware-specific failures."""
        diagnostic_data = {
            "error_message": failure_info.error_message,
            "exit_code": failure_info.exit_code,
            "kernel_panic": failure_info.kernel_panic,
            "timeout_occurred": failure_info.timeout_occurred,
            "hardware_architecture": hardware_config.architecture,
            "hardware_memory_mb": hardware_config.memory_mb,
            "is_virtual": hardware_config.is_virtual
        }
        
        return HardwareSpecificDiagnostic(
            hardware_id=hardware_id,
            hardware_config=hardware_config,
            failure_type=HardwareFailureType.UNKNOWN,
            diagnostic_data=diagnostic_data
        )
    
    def get_diagnostics_by_hardware(self, hardware_id: str) -> List[HardwareSpecificDiagnostic]:
        """Get all diagnostics for a specific hardware."""
        return [d for d in self.collected_diagnostics if d.hardware_id == hardware_id]
    
    def get_diagnostics_by_type(self, failure_type: HardwareFailureType) -> List[HardwareSpecificDiagnostic]:
        """Get all diagnostics of a specific failure type."""
        return [d for d in self.collected_diagnostics if d.failure_type == failure_type]


class FailureToHardwareCorrelator:
    """Correlates failures with specific hardware configurations."""
    
    def __init__(self):
        """Initialize correlator."""
        self.correlations: List[HardwareFailureCorrelation] = []
    
    def correlate_failure_to_hardware(
        self,
        failure_id: str,
        test_results: List[TestResult],
        hardware_configs: Dict[str, HardwareConfig]
    ) -> List[HardwareFailureCorrelation]:
        """Correlate a failure with hardware configurations.
        
        Args:
            failure_id: ID of the failure to correlate
            test_results: List of test results across different hardware
            hardware_configs: Mapping of hardware ID to configuration
            
        Returns:
            List of correlations between failure and hardware
        """
        correlations = []
        
        # Group test results by hardware
        results_by_hardware = {}
        for result in test_results:
            hw_id = result.environment.id
            if hw_id not in results_by_hardware:
                results_by_hardware[hw_id] = []
            results_by_hardware[hw_id].append(result)
        
        # Analyze failure patterns across hardware
        for hw_id, hw_results in results_by_hardware.items():
            if hw_id not in hardware_configs:
                continue
            
            hw_config = hardware_configs[hw_id]
            
            # Calculate correlation score
            correlation_score, factors, evidence = self._calculate_correlation_score(
                failure_id, hw_results, hw_config
            )
            
            if correlation_score > 0.0:
                correlation = HardwareFailureCorrelation(
                    failure_id=failure_id,
                    hardware_id=hw_id,
                    hardware_config=hw_config,
                    correlation_score=correlation_score,
                    correlation_factors=factors,
                    diagnostic_evidence=evidence
                )
                
                correlations.append(correlation)
                self.correlations.append(correlation)
        
        return correlations
    
    def _calculate_correlation_score(
        self,
        failure_id: str,
        hw_results: List[TestResult],
        hw_config: HardwareConfig
    ) -> Tuple[float, List[str], Dict[str, Any]]:
        """Calculate correlation score between failure and hardware.
        
        Args:
            failure_id: Failure ID
            hw_results: Test results for this hardware
            hw_config: Hardware configuration
            
        Returns:
            Tuple of (correlation_score, factors, evidence)
        """
        score = 0.0
        factors = []
        evidence = {}
        
        # Count failed vs passed tests
        failed_count = sum(1 for r in hw_results if r.status == TestStatus.FAILED)
        total_count = len(hw_results)
        
        if total_count == 0:
            return 0.0, [], {}
        
        failure_rate = failed_count / total_count
        evidence["failure_rate"] = failure_rate
        evidence["failed_count"] = failed_count
        evidence["total_count"] = total_count
        
        # Base score on failure rate
        score += failure_rate * 0.4
        
        # Check for hardware-specific error patterns
        hardware_error_count = 0
        for result in hw_results:
            if result.status == TestStatus.FAILED:
                logs = "\n".join(result.artifacts.logs)
                if self._contains_hardware_errors(logs):
                    hardware_error_count += 1
        
        if failed_count > 0:
            hardware_error_rate = hardware_error_count / failed_count
            score += hardware_error_rate * 0.3
            evidence["hardware_error_rate"] = hardware_error_rate
            factors.append(f"Hardware-specific errors in {hardware_error_count}/{failed_count} failures")
        
        # Architecture-specific factors
        if hw_config.architecture in ["arm", "arm64"] and failure_rate > 0.5:
            score += 0.1
            factors.append("High failure rate on ARM architecture")
        
        # Memory-related factors
        if hw_config.memory_mb < 1024 and failure_rate > 0.3:
            score += 0.1
            factors.append("Failures on low-memory configuration")
        
        # Virtual vs physical factors
        if not hw_config.is_virtual and failure_rate > 0.4:
            score += 0.1
            factors.append("Failures on physical hardware")
        
        # Ensure score is within bounds
        score = min(1.0, max(0.0, score))
        
        return score, factors, evidence
    
    def _contains_hardware_errors(self, log_content: str) -> bool:
        """Check if log content contains hardware-specific errors."""
        hardware_patterns = [
            r"Machine Check Exception",
            r"EDAC.*error",
            r"I/O error.*dev",
            r"thermal.*error",
            r"power.*error",
            r"CPU.*error"
        ]
        
        for pattern in hardware_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                return True
        
        return False
    
    def get_correlations_by_hardware(self, hardware_id: str) -> List[HardwareFailureCorrelation]:
        """Get all correlations for a specific hardware."""
        return [c for c in self.correlations if c.hardware_id == hardware_id]
    
    def get_high_correlation_failures(self, threshold: float = 0.7) -> List[HardwareFailureCorrelation]:
        """Get failures with high correlation to hardware."""
        return [c for c in self.correlations if c.correlation_score >= threshold]


class HardwareFailureReportGenerator:
    """Generator for comprehensive hardware failure isolation reports."""
    
    def __init__(self):
        """Initialize report generator."""
        self.generated_reports: List[HardwareFailureReport] = []
    
    def generate_report(
        self,
        failure_id: str,
        hardware_id: str,
        hardware_config: HardwareConfig,
        diagnostics: List[HardwareSpecificDiagnostic],
        correlations: List[HardwareFailureCorrelation]
    ) -> HardwareFailureReport:
        """Generate comprehensive hardware failure isolation report.
        
        Args:
            failure_id: ID of the failure
            hardware_id: ID of the hardware
            hardware_config: Hardware configuration
            diagnostics: Hardware-specific diagnostics
            correlations: Failure-to-hardware correlations
            
        Returns:
            Comprehensive hardware failure report
        """
        import uuid
        
        report_id = str(uuid.uuid4())
        
        # Determine primary failure type
        failure_type = self._determine_primary_failure_type(diagnostics)
        
        # Calculate isolation confidence
        isolation_confidence = self._calculate_isolation_confidence(
            diagnostics, correlations
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            failure_type, hardware_config, diagnostics, correlations
        )
        
        report = HardwareFailureReport(
            report_id=report_id,
            failure_id=failure_id,
            hardware_id=hardware_id,
            hardware_config=hardware_config,
            failure_type=failure_type,
            isolation_confidence=isolation_confidence,
            diagnostics=diagnostics,
            correlations=correlations,
            recommendations=recommendations
        )
        
        self.generated_reports.append(report)
        return report
    
    def _determine_primary_failure_type(
        self,
        diagnostics: List[HardwareSpecificDiagnostic]
    ) -> HardwareFailureType:
        """Determine the primary failure type from diagnostics."""
        if not diagnostics:
            return HardwareFailureType.UNKNOWN
        
        # Count failure types
        type_counts = {}
        for diagnostic in diagnostics:
            failure_type = diagnostic.failure_type
            type_counts[failure_type] = type_counts.get(failure_type, 0) + 1
        
        # Return most common type
        if type_counts:
            return max(type_counts.keys(), key=lambda k: type_counts[k])
        
        return HardwareFailureType.UNKNOWN
    
    def _calculate_isolation_confidence(
        self,
        diagnostics: List[HardwareSpecificDiagnostic],
        correlations: List[HardwareFailureCorrelation]
    ) -> float:
        """Calculate confidence in hardware failure isolation."""
        confidence = 0.0
        
        # Base confidence on number of diagnostics
        if diagnostics:
            confidence += min(0.4, len(diagnostics) * 0.1)
        
        # Add confidence from correlations
        if correlations:
            max_correlation = max(c.correlation_score for c in correlations)
            confidence += max_correlation * 0.6
        
        return min(1.0, confidence)
    
    def _generate_recommendations(
        self,
        failure_type: HardwareFailureType,
        hardware_config: HardwareConfig,
        diagnostics: List[HardwareSpecificDiagnostic],
        correlations: List[HardwareFailureCorrelation]
    ) -> List[str]:
        """Generate recommendations based on failure analysis."""
        recommendations = []
        
        # Type-specific recommendations
        if failure_type == HardwareFailureType.MEMORY_ERROR:
            recommendations.extend([
                "Check memory modules for physical damage",
                "Run memory diagnostic tests (memtest86+)",
                "Verify memory timing and voltage settings",
                "Consider replacing suspect memory modules"
            ])
        elif failure_type == HardwareFailureType.CPU_ERROR:
            recommendations.extend([
                "Check CPU temperature and cooling",
                "Verify CPU power supply stability",
                "Update CPU microcode if available",
                "Consider CPU stress testing"
            ])
        elif failure_type == HardwareFailureType.STORAGE_ERROR:
            recommendations.extend([
                "Check storage device health (SMART data)",
                "Verify storage connections and cables",
                "Run filesystem check and repair",
                "Consider storage device replacement"
            ])
        elif failure_type == HardwareFailureType.NETWORK_ERROR:
            recommendations.extend([
                "Check network cable connections",
                "Verify network interface configuration",
                "Update network driver if available",
                "Test with different network interface"
            ])
        
        # Architecture-specific recommendations
        if hardware_config.architecture in ["arm", "arm64"]:
            recommendations.append("Verify ARM-specific kernel configuration")
        
        # Virtual vs physical recommendations
        if hardware_config.is_virtual:
            recommendations.extend([
                "Check hypervisor configuration",
                "Verify virtual hardware resource allocation",
                "Consider testing on physical hardware"
            ])
        else:
            recommendations.extend([
                "Perform physical hardware inspection",
                "Check hardware compatibility with kernel version",
                "Verify firmware/BIOS settings"
            ])
        
        # Correlation-based recommendations
        high_correlations = [c for c in correlations if c.correlation_score > 0.7]
        if high_correlations:
            recommendations.append(
                f"High correlation with hardware detected (score: "
                f"{max(c.correlation_score for c in high_correlations):.2f}) - "
                f"prioritize hardware-specific investigation"
            )
        
        return recommendations
    
    def get_reports_by_hardware(self, hardware_id: str) -> List[HardwareFailureReport]:
        """Get all reports for a specific hardware."""
        return [r for r in self.generated_reports if r.hardware_id == hardware_id]
    
    def get_reports_by_failure_type(self, failure_type: HardwareFailureType) -> List[HardwareFailureReport]:
        """Get all reports of a specific failure type."""
        return [r for r in self.generated_reports if r.failure_type == failure_type]


class HardwareFailureIsolationSystem:
    """Unified hardware failure isolation system."""
    
    def __init__(self):
        """Initialize hardware failure isolation system."""
        self.diagnostic_collector = HardwareSpecificDiagnosticCollector()
        self.correlator = FailureToHardwareCorrelator()
        self.report_generator = HardwareFailureReportGenerator()
    
    def isolate_hardware_failure(
        self,
        failure_id: str,
        test_results: List[TestResult],
        hardware_configs: Dict[str, HardwareConfig]
    ) -> List[HardwareFailureReport]:
        """Perform complete hardware failure isolation analysis.
        
        Args:
            failure_id: ID of the failure to isolate
            test_results: Test results across different hardware
            hardware_configs: Mapping of hardware ID to configuration
            
        Returns:
            List of hardware failure isolation reports
        """
        reports = []
        
        # Collect diagnostics for each hardware
        all_diagnostics = {}
        for result in test_results:
            hw_id = result.environment.id
            if hw_id in hardware_configs:
                hw_config = hardware_configs[hw_id]
                diagnostics = self.diagnostic_collector.collect_diagnostics(
                    hw_id, hw_config, result
                )
                if hw_id not in all_diagnostics:
                    all_diagnostics[hw_id] = []
                all_diagnostics[hw_id].extend(diagnostics)
        
        # Correlate failures with hardware
        correlations = self.correlator.correlate_failure_to_hardware(
            failure_id, test_results, hardware_configs
        )
        
        # Generate reports for each hardware with diagnostics
        for hw_id, diagnostics in all_diagnostics.items():
            if diagnostics:  # Only generate report if there are diagnostics
                hw_config = hardware_configs[hw_id]
                hw_correlations = [c for c in correlations if c.hardware_id == hw_id]
                
                report = self.report_generator.generate_report(
                    failure_id, hw_id, hw_config, diagnostics, hw_correlations
                )
                reports.append(report)
        
        return reports
    
    def get_hardware_failure_statistics(self) -> Dict[str, Any]:
        """Get statistics about hardware failures."""
        diagnostics = self.diagnostic_collector.collected_diagnostics
        correlations = self.correlator.correlations
        reports = self.report_generator.generated_reports
        
        # Count by failure type
        failure_type_counts = {}
        for diagnostic in diagnostics:
            failure_type = diagnostic.failure_type
            failure_type_counts[failure_type.value] = failure_type_counts.get(failure_type.value, 0) + 1
        
        # Count by architecture
        arch_counts = {}
        for diagnostic in diagnostics:
            arch = diagnostic.hardware_config.architecture
            arch_counts[arch] = arch_counts.get(arch, 0) + 1
        
        # High correlation failures
        high_correlation_count = len([c for c in correlations if c.correlation_score > 0.7])
        
        return {
            "total_diagnostics": len(diagnostics),
            "total_correlations": len(correlations),
            "total_reports": len(reports),
            "failure_type_distribution": failure_type_counts,
            "architecture_distribution": arch_counts,
            "high_correlation_failures": high_correlation_count,
            "average_correlation_score": (
                sum(c.correlation_score for c in correlations) / len(correlations)
                if correlations else 0.0
            )
        }