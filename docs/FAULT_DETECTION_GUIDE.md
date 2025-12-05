# Fault Detection and Monitoring Guide

## Overview

The Fault Detection and Monitoring system is a critical component of the Agentic AI Testing System that automatically detects and reports various types of faults that occur during kernel and BSP testing. The system provides comprehensive detection capabilities for kernel crashes, system hangs, memory leaks, and data corruption.

## Architecture

The fault detection system consists of four specialized detectors coordinated by a unified detection system:

```
┌─────────────────────────────────────────────────────────────┐
│              FaultDetectionSystem                            │
│  (Unified coordinator for all fault detection)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        │              │               │              │
        ▼              ▼               ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐
│   Kernel     │ │   Hang   │ │   Memory     │ │    Data      │
│   Crash      │ │ Detector │ │    Leak      │ │ Corruption   │
│  Detector    │ │          │ │  Detector    │ │  Detector    │
└──────────────┘ └──────────┘ └──────────────┘ └──────────────┘
```

## Components

### 1. Kernel Crash Detector

Detects kernel crashes, panics, and fatal errors.

**Detected Patterns:**
- Kernel panic messages
- NULL pointer dereferences
- General protection faults
- Kernel Oops
- Segmentation faults
- Boot failures

**Features:**
- Stack trace extraction
- Crash type classification
- Severity assessment (all crashes are critical)
- Statistics tracking

**Example Usage:**
```python
from execution.fault_detection import KernelCrashDetector

detector = KernelCrashDetector()
log_content = """
[  123.456789] Kernel panic - not syncing: Fatal exception
[  123.456790] Call Trace:
[  123.456791]  dump_stack+0x5c/0x80
[  123.456792]  panic+0xe7/0x220
"""

faults = detector.detect(log_content)
for fault in faults:
    print(f"Detected: {fault.description}")
    print(f"Severity: {fault.severity}")
    print(f"Type: {fault.details['crash_type']}")
```

### 2. Hang Detector

Detects system hangs and timeouts through both active monitoring and log analysis.

**Detection Methods:**

1. **Active Monitoring:**
   - Start monitoring an operation
   - Check for timeout periodically
   - Detect when operation exceeds threshold

2. **Log-Based Detection:**
   - Blocked tasks
   - Soft lockups
   - Watchdog timeouts
   - RCU stalls

**Detected Patterns:**
- `task .* blocked for more than \d+ seconds`
- `task blocked for more than \d+ seconds` (without task name)
- `INFO: task .* blocked`
- `hung task`
- `watchdog: BUG: soft lockup`
- `NMI watchdog: BUG: soft lockup`
- `rcu_sched detected stalls`

**Example Usage:**
```python
from execution.fault_detection import HangDetector

# Active monitoring
detector = HangDetector(default_timeout=300)  # 5 minutes
detector.start_monitoring("test_operation_123")

# ... operation runs ...

fault = detector.check_timeout("test_operation_123")
if fault:
    print(f"Operation timed out: {fault.description}")

detector.stop_monitoring("test_operation_123")

# Log-based detection
log_content = "INFO: task systemd:1 blocked for more than 120 seconds"
faults = detector.detect_from_logs(log_content)
```

### 3. Memory Leak Detector

Integrates with KASAN (Kernel Address Sanitizer) to detect memory-related issues.

**Detected Issues:**
- Use-after-free
- Double-free
- Out-of-bounds access (heap, stack, global)
- Memory leaks
- Invalid free operations
- Use-after-scope

**Severity Classification:**
- **Critical:** Use-after-free, Double-free, Heap out-of-bounds
- **High:** Stack out-of-bounds, Invalid free
- **Medium:** Other memory issues

**Example Usage:**
```python
from execution.fault_detection import MemoryLeakDetector

detector = MemoryLeakDetector()
log_content = """
[  456.789012] BUG: KASAN: use-after-free in function_name+0x123/0x456
[  456.789013] Read of size 8 at addr ffff888012345678 by task test/1234
"""

faults = detector.detect(log_content)
for fault in faults:
    print(f"Memory issue: {fault.details['leak_type']}")
    print(f"Severity: {fault.severity}")
```

### 4. Data Corruption Detector

Detects data integrity issues and filesystem corruption.

**Detected Issues:**
- Checksum/CRC errors
- Filesystem corruption
- Metadata corruption
- Hardware errors (ECC, bit flips)
- Invalid magic numbers
- Inode corruption

**Features:**
- Pattern-based detection from logs
- Checksum verification for data integrity
- Corruption type classification
- Severity assessment

**Example Usage:**
```python
from execution.fault_detection import DataCorruptionDetector

detector = DataCorruptionDetector()

# Log-based detection
log_content = "EXT4-fs error: data corruption detected in inode 12345"
faults = detector.detect(log_content)

# Direct data verification
data = b"some test data"
expected_checksum = str(hash(data))
fault = detector.verify_data_integrity(data, expected_checksum)
if fault:
    print(f"Data corruption detected: {fault.description}")
```

### 5. Unified Fault Detection System

Coordinates all detectors and provides a single interface for comprehensive fault detection.

**Example Usage:**
```python
from execution.fault_detection import FaultDetectionSystem

system = FaultDetectionSystem(hang_timeout=300)

# Detect all fault types from logs
log_content = """
[  123.456] Kernel panic - not syncing: Fatal exception
[  234.567] INFO: task blocked for more than 120 seconds
[  345.678] BUG: KASAN: use-after-free in function_name
[  456.789] CRC error: checksum mismatch detected
"""

all_faults = system.detect_all_faults(log_content)

print(f"Total faults detected: {len(all_faults)}")
for fault in all_faults:
    print(f"- {fault.category.value}: {fault.description}")

# Get faults by category
crashes = system.get_faults_by_category(FaultCategory.KERNEL_CRASH)
hangs = system.get_faults_by_category(FaultCategory.HANG)

# Get comprehensive statistics
stats = system.get_all_statistics()
print(f"Statistics: {stats}")
```

## Data Models

### DetectedFault

Represents a detected fault with complete metadata.

```python
@dataclass
class DetectedFault:
    category: FaultCategory          # Type of fault
    timestamp: datetime              # When detected
    description: str                 # Human-readable description
    severity: str                    # low, medium, high, critical
    details: Dict[str, Any]         # Additional context
    stack_trace: Optional[str]      # Stack trace if available
```

### FaultCategory

Enumeration of fault types:
- `KERNEL_CRASH`: Kernel crashes and panics
- `HANG`: System hangs and timeouts
- `MEMORY_LEAK`: Memory-related issues
- `DATA_CORRUPTION`: Data integrity issues

## Integration with Test Execution

The fault detection system integrates seamlessly with the test execution pipeline:

```python
from execution.test_runner import TestRunner
from execution.fault_detection import FaultDetectionSystem

# Initialize components
test_runner = TestRunner()
fault_detector = FaultDetectionSystem()

# Execute test
result = test_runner.execute_test(test_case, environment)

# Analyze logs for faults
if result.artifacts and result.artifacts.logs:
    for log_file in result.artifacts.logs:
        with open(log_file, 'r') as f:
            log_content = f.read()
            faults = fault_detector.detect_all_faults(log_content)
            
            if faults:
                print(f"Detected {len(faults)} faults in {log_file}")
                for fault in faults:
                    print(f"  - {fault.category.value}: {fault.description}")
```

## Property-Based Testing

The fault detection system is validated using property-based testing with Hypothesis to ensure completeness and accuracy.

**Key Properties Tested:**

1. **Completeness:** All injected faults are detected
2. **Accuracy:** Detection count matches injection count
3. **No False Positives:** Clean logs don't trigger detections
4. **Category Correctness:** Detected faults have correct categories
5. **Metadata Completeness:** All faults have required metadata

**Running Property Tests:**
```bash
# Run all fault detection property tests
pytest tests/property/test_fault_detection_completeness.py -v

# Run with statistics
pytest tests/property/test_fault_detection_completeness.py --hypothesis-show-statistics

# Run with more iterations
pytest tests/property/test_fault_detection_completeness.py --hypothesis-iterations=200
```

## Best Practices

### 1. Regular Log Analysis
Analyze logs after every test execution to catch faults early:
```python
# Always check logs after test execution
faults = fault_detector.detect_all_faults(log_content)
if faults:
    # Handle detected faults
    for fault in faults:
        log_fault_to_database(fault)
        notify_developers(fault)
```

### 2. Active Hang Monitoring
Use active monitoring for long-running operations:
```python
hang_detector.start_monitoring("long_operation", timeout=600)
try:
    # Perform long operation
    result = perform_long_operation()
finally:
    hang_detector.stop_monitoring("long_operation")
```

### 3. Statistics Tracking
Regularly collect and analyze statistics:
```python
stats = system.get_all_statistics()
if stats['total_faults'] > threshold:
    alert_team("High fault rate detected")
```

### 4. Periodic Cleanup
Reset statistics periodically to avoid memory growth:
```python
# After processing a batch of tests
system.reset_all_statistics()
```

## Performance Considerations

### Log Size
- Large logs can slow down pattern matching
- Consider streaming analysis for very large logs
- Use log rotation to manage size

### Pattern Compilation
- Regex patterns are compiled once at initialization
- Reuse detector instances across multiple analyses
- Avoid creating new detectors for each log

### Memory Usage
- Detected faults are stored in memory
- Reset statistics periodically in long-running processes
- Consider persisting faults to database for large-scale testing

## Troubleshooting

### False Negatives (Missed Detections)

**Problem:** Known faults not being detected

**Solutions:**
1. Check if log pattern matches detector patterns
2. Add new patterns to detector if needed
3. Verify log format is as expected
4. Check for encoding issues in logs

### False Positives

**Problem:** Clean logs triggering detections

**Solutions:**
1. Review and refine regex patterns
2. Add negative lookahead patterns if needed
3. Increase pattern specificity
4. Test with property-based tests

### Performance Issues

**Problem:** Slow fault detection

**Solutions:**
1. Profile pattern matching performance
2. Optimize regex patterns
3. Consider parallel processing for multiple logs
4. Use streaming analysis for large logs

## API Reference

### KernelCrashDetector

```python
class KernelCrashDetector:
    def detect(self, log_content: str) -> List[DetectedFault]
    def get_statistics(self) -> Dict[str, Any]
```

### HangDetector

```python
class HangDetector:
    def __init__(self, default_timeout: int = 300)
    def start_monitoring(self, operation_id: str, timeout: Optional[int] = None)
    def check_timeout(self, operation_id: str, timeout: Optional[int] = None) -> Optional[DetectedFault]
    def stop_monitoring(self, operation_id: str)
    def detect_from_logs(self, log_content: str) -> List[DetectedFault]
    def get_statistics(self) -> Dict[str, Any]
```

### MemoryLeakDetector

```python
class MemoryLeakDetector:
    def detect(self, log_content: str) -> List[DetectedFault]
    def get_statistics(self) -> Dict[str, Any]
```

### DataCorruptionDetector

```python
class DataCorruptionDetector:
    def detect(self, log_content: str) -> List[DetectedFault]
    def verify_data_integrity(self, data: bytes, expected_checksum: Optional[str] = None) -> Optional[DetectedFault]
    def get_statistics(self) -> Dict[str, Any]
```

### FaultDetectionSystem

```python
class FaultDetectionSystem:
    def __init__(self, hang_timeout: int = 300)
    def detect_all_faults(self, log_content: str) -> List[DetectedFault]
    def get_faults_by_category(self, category: FaultCategory) -> List[DetectedFault]
    def get_all_statistics(self) -> Dict[str, Any]
    def reset_all_statistics(self)
```

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Test Execution Guide](../execution/README.md)
- [Requirements Document](../.kiro/specs/agentic-kernel-testing/requirements.md)
- [Design Document](../.kiro/specs/agentic-kernel-testing/design.md)

## Contributing

When adding new fault detection patterns:

1. Add pattern to appropriate detector class
2. Update property tests to cover new patterns
3. Run full test suite to ensure no regressions
4. Update this documentation with new patterns
5. Add examples demonstrating new detection capabilities

## Support

For issues or questions about fault detection:
- Check property tests for examples
- Review detector source code in `execution/fault_detection.py`
- Consult design document for requirements
- Open an issue with reproduction steps
