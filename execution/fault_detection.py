"""Fault detection and monitoring system.

This module provides functionality for:
- Kernel crash detection
- Hang detection with timeout monitoring
- Memory leak detection (KASAN integration)
- Data corruption detection
"""

import re
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime


class FaultCategory(str, Enum):
    """Categories of faults that can be detected."""
    KERNEL_CRASH = "kernel_crash"
    HANG = "hang"
    MEMORY_LEAK = "memory_leak"
    DATA_CORRUPTION = "data_corruption"


@dataclass
class DetectedFault:
    """Record of a detected fault."""
    category: FaultCategory
    timestamp: datetime
    description: str
    severity: str  # low, medium, high, critical
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "severity": self.severity,
            "details": self.details,
            "stack_trace": self.stack_trace
        }


class KernelCrashDetector:
    """Detector for kernel crashes and panics."""
    
    # Common kernel panic patterns
    PANIC_PATTERNS = [
        r"Kernel panic",
        r"BUG: unable to handle",
        r"Oops:",
        r"general protection fault",
        r"segmentation fault",
        r"kernel NULL pointer dereference",
        r"Call Trace:",
        r"RIP:",
        r"unable to mount root fs",
        r"VFS: Cannot open root device"
    ]
    
    def __init__(self):
        """Initialize kernel crash detector."""
        self.detected_crashes: List[DetectedFault] = []
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.PANIC_PATTERNS]
    
    def detect(self, log_content: str) -> List[DetectedFault]:
        """Detect kernel crashes in log content.
        
        Args:
            log_content: Kernel log or dmesg output
            
        Returns:
            List of detected crash faults
        """
        faults = []
        lines = log_content.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    # Extract stack trace if present
                    stack_trace = self._extract_stack_trace(lines, i)
                    
                    # Determine crash type
                    crash_type = self._classify_crash(line, stack_trace)
                    
                    fault = DetectedFault(
                        category=FaultCategory.KERNEL_CRASH,
                        timestamp=datetime.now(),
                        description=f"Kernel crash detected: {crash_type}",
                        severity="critical",
                        details={
                            "crash_type": crash_type,
                            "trigger_line": line.strip(),
                            "line_number": i
                        },
                        stack_trace=stack_trace
                    )
                    faults.append(fault)
                    self.detected_crashes.append(fault)
                    break  # Only report once per line
        
        return faults
    
    def _extract_stack_trace(self, lines: List[str], start_idx: int) -> Optional[str]:
        """Extract stack trace from log lines.
        
        Args:
            lines: Log lines
            start_idx: Starting index
            
        Returns:
            Stack trace string or None
        """
        stack_lines = []
        # Look ahead for stack trace markers
        for i in range(start_idx, min(start_idx + 50, len(lines))):
            line = lines[i]
            if any(marker in line for marker in ["Call Trace:", "Stack:", "Backtrace:"]):
                # Collect stack trace lines
                for j in range(i, min(i + 30, len(lines))):
                    trace_line = lines[j]
                    if trace_line.strip():
                        stack_lines.append(trace_line)
                    else:
                        break
                break
        
        return '\n'.join(stack_lines) if stack_lines else None
    
    def _classify_crash(self, trigger_line: str, stack_trace: Optional[str]) -> str:
        """Classify the type of kernel crash.
        
        Args:
            trigger_line: Line that triggered detection
            stack_trace: Stack trace if available
            
        Returns:
            Crash type classification
        """
        trigger_lower = trigger_line.lower()
        
        if "null pointer" in trigger_lower:
            return "NULL pointer dereference"
        elif "general protection" in trigger_lower:
            return "General protection fault"
        elif "oops" in trigger_lower:
            return "Kernel Oops"
        elif "panic" in trigger_lower:
            return "Kernel panic"
        elif "segmentation fault" in trigger_lower:
            return "Segmentation fault"
        elif "unable to mount" in trigger_lower or "cannot open root" in trigger_lower:
            return "Boot failure"
        else:
            return "Unknown crash"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get crash detection statistics.
        
        Returns:
            Dictionary with statistics
        """
        crash_types = {}
        for fault in self.detected_crashes:
            crash_type = fault.details.get("crash_type", "unknown")
            crash_types[crash_type] = crash_types.get(crash_type, 0) + 1
        
        return {
            "total_crashes": len(self.detected_crashes),
            "crash_types": crash_types
        }


class HangDetector:
    """Detector for system hangs and timeouts."""
    
    def __init__(self, default_timeout: int = 300):
        """Initialize hang detector.
        
        Args:
            default_timeout: Default timeout in seconds
        """
        if default_timeout <= 0:
            raise ValueError("default_timeout must be positive")
        
        self.default_timeout = default_timeout
        self.detected_hangs: List[DetectedFault] = []
        self.monitored_operations: Dict[str, float] = {}
    
    def start_monitoring(self, operation_id: str, timeout: Optional[int] = None) -> None:
        """Start monitoring an operation for hangs.
        
        Args:
            operation_id: Unique identifier for the operation
            timeout: Timeout in seconds (uses default if None)
        """
        self.monitored_operations[operation_id] = time.time()
    
    def check_timeout(self, operation_id: str, timeout: Optional[int] = None) -> Optional[DetectedFault]:
        """Check if an operation has timed out.
        
        Args:
            operation_id: Operation identifier
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            DetectedFault if timeout occurred, None otherwise
        """
        if operation_id not in self.monitored_operations:
            return None
        
        start_time = self.monitored_operations[operation_id]
        elapsed = time.time() - start_time
        timeout_value = timeout if timeout is not None else self.default_timeout
        
        if elapsed > timeout_value:
            fault = DetectedFault(
                category=FaultCategory.HANG,
                timestamp=datetime.now(),
                description=f"Operation '{operation_id}' timed out after {elapsed:.2f} seconds",
                severity="high",
                details={
                    "operation_id": operation_id,
                    "elapsed_seconds": elapsed,
                    "timeout_seconds": timeout_value
                }
            )
            self.detected_hangs.append(fault)
            return fault
        
        return None
    
    def stop_monitoring(self, operation_id: str) -> None:
        """Stop monitoring an operation.
        
        Args:
            operation_id: Operation identifier
        """
        self.monitored_operations.pop(operation_id, None)
    
    def detect_from_logs(self, log_content: str) -> List[DetectedFault]:
        """Detect hangs from log patterns.
        
        Args:
            log_content: System logs
            
        Returns:
            List of detected hang faults
        """
        faults = []
        hang_patterns = [
            r"task .* blocked for more than \d+ seconds",
            r"task blocked for more than \d+ seconds",  # Handle case without task name
            r"INFO: task .* blocked",
            r"hung task",
            r"watchdog: BUG: soft lockup",
            r"NMI watchdog: BUG: soft lockup",
            r"rcu_sched detected stalls"
        ]
        
        for pattern in hang_patterns:
            matches = re.finditer(pattern, log_content, re.IGNORECASE)
            for match in matches:
                fault = DetectedFault(
                    category=FaultCategory.HANG,
                    timestamp=datetime.now(),
                    description=f"System hang detected: {match.group()}",
                    severity="high",
                    details={
                        "pattern": pattern,
                        "matched_text": match.group()
                    }
                )
                faults.append(fault)
                self.detected_hangs.append(fault)
        
        return faults
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get hang detection statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_hangs": len(self.detected_hangs),
            "currently_monitored": len(self.monitored_operations)
        }


class MemoryLeakDetector:
    """Detector for memory leaks using KASAN integration."""
    
    # KASAN error patterns
    KASAN_PATTERNS = [
        r"BUG: KASAN:",
        r"use-after-free",
        r"out-of-bounds",
        r"slab-out-of-bounds",
        r"heap-out-of-bounds",
        r"stack-out-of-bounds",
        r"global-out-of-bounds",
        r"use-after-scope",
        r"double-free",
        r"invalid-free",
        r"Memory leak detected"
    ]
    
    def __init__(self):
        """Initialize memory leak detector."""
        self.detected_leaks: List[DetectedFault] = []
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.KASAN_PATTERNS]
    
    def detect(self, log_content: str) -> List[DetectedFault]:
        """Detect memory leaks and KASAN errors in logs.
        
        Args:
            log_content: Kernel log or KASAN output
            
        Returns:
            List of detected memory leak faults
        """
        faults = []
        lines = log_content.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    # Extract additional context
                    context = self._extract_context(lines, i)
                    leak_type = self._classify_leak(line)
                    
                    fault = DetectedFault(
                        category=FaultCategory.MEMORY_LEAK,
                        timestamp=datetime.now(),
                        description=f"Memory issue detected: {leak_type}",
                        severity=self._determine_severity(leak_type),
                        details={
                            "leak_type": leak_type,
                            "trigger_line": line.strip(),
                            "line_number": i,
                            "context": context
                        }
                    )
                    faults.append(fault)
                    self.detected_leaks.append(fault)
                    break
        
        return faults
    
    def _extract_context(self, lines: List[str], start_idx: int, context_lines: int = 10) -> str:
        """Extract context around a detection.
        
        Args:
            lines: Log lines
            start_idx: Starting index
            context_lines: Number of lines to extract
            
        Returns:
            Context string
        """
        start = max(0, start_idx - context_lines // 2)
        end = min(len(lines), start_idx + context_lines // 2)
        return '\n'.join(lines[start:end])
    
    def _classify_leak(self, trigger_line: str) -> str:
        """Classify the type of memory issue.
        
        Args:
            trigger_line: Line that triggered detection
            
        Returns:
            Memory issue classification
        """
        trigger_lower = trigger_line.lower()
        
        if "use-after-free" in trigger_lower:
            return "Use-after-free"
        elif "double-free" in trigger_lower:
            return "Double-free"
        elif "out-of-bounds" in trigger_lower:
            if "heap" in trigger_lower:
                return "Heap out-of-bounds"
            elif "stack" in trigger_lower:
                return "Stack out-of-bounds"
            elif "global" in trigger_lower:
                return "Global out-of-bounds"
            else:
                return "Out-of-bounds access"
        elif "memory leak" in trigger_lower:
            return "Memory leak"
        elif "invalid-free" in trigger_lower:
            return "Invalid free"
        elif "use-after-scope" in trigger_lower:
            return "Use-after-scope"
        else:
            return "Unknown memory issue"
    
    def _determine_severity(self, leak_type: str) -> str:
        """Determine severity of memory issue.
        
        Args:
            leak_type: Type of memory issue
            
        Returns:
            Severity level
        """
        critical_types = ["Use-after-free", "Double-free", "Heap out-of-bounds"]
        high_types = ["Stack out-of-bounds", "Invalid free"]
        
        if leak_type in critical_types:
            return "critical"
        elif leak_type in high_types:
            return "high"
        else:
            return "medium"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory leak detection statistics.
        
        Returns:
            Dictionary with statistics
        """
        leak_types = {}
        for fault in self.detected_leaks:
            leak_type = fault.details.get("leak_type", "unknown")
            leak_types[leak_type] = leak_types.get(leak_type, 0) + 1
        
        return {
            "total_leaks": len(self.detected_leaks),
            "leak_types": leak_types
        }


class DataCorruptionDetector:
    """Detector for data corruption issues."""
    
    # Data corruption patterns
    CORRUPTION_PATTERNS = [
        r"data corruption",
        r"checksum mismatch",
        r"CRC error",
        r"bad magic number",
        r"filesystem corruption",
        r"metadata corruption",
        r"ECC error",
        r"bit flip detected",
        r"invalid data structure",
        r"corrupted inode"
    ]
    
    def __init__(self):
        """Initialize data corruption detector."""
        self.detected_corruptions: List[DetectedFault] = []
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.CORRUPTION_PATTERNS]
    
    def detect(self, log_content: str) -> List[DetectedFault]:
        """Detect data corruption in logs.
        
        Args:
            log_content: System logs
            
        Returns:
            List of detected corruption faults
        """
        faults = []
        lines = log_content.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    corruption_type = self._classify_corruption(line)
                    
                    fault = DetectedFault(
                        category=FaultCategory.DATA_CORRUPTION,
                        timestamp=datetime.now(),
                        description=f"Data corruption detected: {corruption_type}",
                        severity=self._determine_severity(corruption_type),
                        details={
                            "corruption_type": corruption_type,
                            "trigger_line": line.strip(),
                            "line_number": i
                        }
                    )
                    faults.append(fault)
                    self.detected_corruptions.append(fault)
                    break
        
        return faults
    
    def verify_data_integrity(
        self, 
        data: bytes, 
        expected_checksum: Optional[str] = None
    ) -> Optional[DetectedFault]:
        """Verify data integrity using checksums.
        
        Args:
            data: Data to verify
            expected_checksum: Expected checksum value
            
        Returns:
            DetectedFault if corruption detected, None otherwise
        """
        if expected_checksum is None:
            return None
        
        # Simple checksum calculation (in real implementation, use proper algorithms)
        calculated_checksum = str(hash(data))
        
        if calculated_checksum != expected_checksum:
            fault = DetectedFault(
                category=FaultCategory.DATA_CORRUPTION,
                timestamp=datetime.now(),
                description="Data integrity check failed: checksum mismatch",
                severity="high",
                details={
                    "corruption_type": "Checksum mismatch",
                    "expected_checksum": expected_checksum,
                    "calculated_checksum": calculated_checksum,
                    "data_size": len(data)
                }
            )
            self.detected_corruptions.append(fault)
            return fault
        
        return None
    
    def _classify_corruption(self, trigger_line: str) -> str:
        """Classify the type of data corruption.
        
        Args:
            trigger_line: Line that triggered detection
            
        Returns:
            Corruption type classification
        """
        trigger_lower = trigger_line.lower()
        
        if "checksum" in trigger_lower or "crc" in trigger_lower:
            return "Checksum/CRC error"
        elif "filesystem" in trigger_lower:
            return "Filesystem corruption"
        elif "metadata" in trigger_lower:
            return "Metadata corruption"
        elif "ecc" in trigger_lower or "bit flip" in trigger_lower:
            return "Hardware error (ECC/bit flip)"
        elif "magic number" in trigger_lower:
            return "Invalid magic number"
        elif "inode" in trigger_lower:
            return "Inode corruption"
        else:
            return "Unknown corruption"
    
    def _determine_severity(self, corruption_type: str) -> str:
        """Determine severity of corruption.
        
        Args:
            corruption_type: Type of corruption
            
        Returns:
            Severity level
        """
        critical_types = ["Filesystem corruption", "Metadata corruption"]
        high_types = ["Checksum/CRC error", "Inode corruption"]
        
        if corruption_type in critical_types:
            return "critical"
        elif corruption_type in high_types:
            return "high"
        else:
            return "medium"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get data corruption detection statistics.
        
        Returns:
            Dictionary with statistics
        """
        corruption_types = {}
        for fault in self.detected_corruptions:
            corruption_type = fault.details.get("corruption_type", "unknown")
            corruption_types[corruption_type] = corruption_types.get(corruption_type, 0) + 1
        
        return {
            "total_corruptions": len(self.detected_corruptions),
            "corruption_types": corruption_types
        }


class FaultDetectionSystem:
    """Unified fault detection system."""
    
    def __init__(self, hang_timeout: int = 300):
        """Initialize fault detection system.
        
        Args:
            hang_timeout: Default timeout for hang detection in seconds
        """
        self.crash_detector = KernelCrashDetector()
        self.hang_detector = HangDetector(default_timeout=hang_timeout)
        self.memory_leak_detector = MemoryLeakDetector()
        self.corruption_detector = DataCorruptionDetector()
    
    def detect_all_faults(self, log_content: str) -> List[DetectedFault]:
        """Run all fault detectors on log content.
        
        Args:
            log_content: System/kernel logs
            
        Returns:
            List of all detected faults
        """
        all_faults = []
        
        # Run all detectors
        all_faults.extend(self.crash_detector.detect(log_content))
        all_faults.extend(self.hang_detector.detect_from_logs(log_content))
        all_faults.extend(self.memory_leak_detector.detect(log_content))
        all_faults.extend(self.corruption_detector.detect(log_content))
        
        return all_faults
    
    def get_faults_by_category(self, category: FaultCategory) -> List[DetectedFault]:
        """Get all detected faults of a specific category.
        
        Args:
            category: Fault category to filter by
            
        Returns:
            List of faults in the specified category
        """
        all_faults = []
        
        if category == FaultCategory.KERNEL_CRASH:
            all_faults = self.crash_detector.detected_crashes
        elif category == FaultCategory.HANG:
            all_faults = self.hang_detector.detected_hangs
        elif category == FaultCategory.MEMORY_LEAK:
            all_faults = self.memory_leak_detector.detected_leaks
        elif category == FaultCategory.DATA_CORRUPTION:
            all_faults = self.corruption_detector.detected_corruptions
        
        return all_faults
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics from all detectors.
        
        Returns:
            Dictionary with statistics from all detectors
        """
        return {
            "crash_detection": self.crash_detector.get_statistics(),
            "hang_detection": self.hang_detector.get_statistics(),
            "memory_leak_detection": self.memory_leak_detector.get_statistics(),
            "corruption_detection": self.corruption_detector.get_statistics(),
            "total_faults": (
                len(self.crash_detector.detected_crashes) +
                len(self.hang_detector.detected_hangs) +
                len(self.memory_leak_detector.detected_leaks) +
                len(self.corruption_detector.detected_corruptions)
            )
        }
    
    def reset_all_statistics(self):
        """Reset statistics for all detectors."""
        self.crash_detector.detected_crashes.clear()
        self.hang_detector.detected_hangs.clear()
        self.hang_detector.monitored_operations.clear()
        self.memory_leak_detector.detected_leaks.clear()
        self.corruption_detector.detected_corruptions.clear()
