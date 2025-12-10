#!/usr/bin/env python3
"""Example usage of the database layer."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from ai_generator.models import (
    TestCase, TestResult, Environment, CoverageData, 
    TestType, TestStatus, EnvironmentStatus, HardwareConfig,
    FailureInfo, ArtifactBundle
)

def demonstrate_data_models():
    """Demonstrate core data model usage."""
    print("🔧 Creating Hardware Configuration...")
    
    # Create hardware configuration
    hw_config = HardwareConfig(
        architecture="x86_64",
        cpu_model="Intel Core i7-9700K",
        memory_mb=16384,
        storage_type="nvme",
        is_virtual=True,
        emulator="qemu"
    )
    
    print(f"   Architecture: {hw_config.architecture}")
    print(f"   CPU: {hw_config.cpu_model}")
    print(f"   Memory: {hw_config.memory_mb} MB")
    print(f"   Virtual: {hw_config.is_virtual}")
    
    print("\n🧪 Creating Test Case...")
    
    # Create test case
    test_case = TestCase(
        id="kernel-mm-001",
        name="Memory Management Stress Test",
        description="Test kernel memory allocation under high load",
        test_type=TestType.PERFORMANCE,
        target_subsystem="memory_management",
        code_paths=[
            "mm/page_alloc.c",
            "mm/slab.c",
            "mm/vmalloc.c"
        ],
        execution_time_estimate=300,
        required_hardware=hw_config,
        test_script="""#!/bin/bash
# Memory stress test
echo "Starting memory allocation test..."
for i in {1..1000}; do
    dd if=/dev/zero of=/tmp/test_$i bs=1M count=10 2>/dev/null
done
echo "Memory test completed"
rm -f /tmp/test_*
"""
    )
    
    print(f"   ID: {test_case.id}")
    print(f"   Name: {test_case.name}")
    print(f"   Type: {test_case.test_type.value}")
    print(f"   Subsystem: {test_case.target_subsystem}")
    print(f"   Code Paths: {len(test_case.code_paths)} files")
    
    print("\n🖥️  Creating Test Environment...")
    
    # Create environment
    environment = Environment(
        id="env-qemu-001",
        config=hw_config,
        status=EnvironmentStatus.IDLE,
        kernel_version="6.5.0-rc1",
        ip_address="192.168.122.100"
    )
    
    print(f"   ID: {environment.id}")
    print(f"   Status: {environment.status.value}")
    print(f"   Kernel: {environment.kernel_version}")
    print(f"   IP: {environment.ip_address}")
    
    print("\n📊 Creating Coverage Data...")
    
    # Create coverage data
    coverage = CoverageData(
        line_coverage=0.87,
        branch_coverage=0.73,
        function_coverage=0.92,
        covered_lines=[
            "mm/page_alloc.c:1234",
            "mm/page_alloc.c:1245",
            "mm/slab.c:567"
        ],
        uncovered_lines=[
            "mm/page_alloc.c:1250",
            "mm/vmalloc.c:890"
        ]
    )
    
    print(f"   Line Coverage: {coverage.line_coverage:.1%}")
    print(f"   Branch Coverage: {coverage.branch_coverage:.1%}")
    print(f"   Function Coverage: {coverage.function_coverage:.1%}")
    print(f"   Covered Lines: {len(coverage.covered_lines)}")
    print(f"   Uncovered Lines: {len(coverage.uncovered_lines)}")
    
    print("\n📋 Creating Test Result...")
    
    # Create test result
    artifacts = ArtifactBundle(
        logs=["/var/log/kernel.log", "/var/log/test.log"],
        traces=["/tmp/perf.data"],
        metadata={"test_duration": 298.5, "peak_memory": "15.2GB"}
    )
    
    test_result = TestResult(
        test_id=test_case.id,
        status=TestStatus.PASSED,
        execution_time=298.5,
        environment=environment,
        artifacts=artifacts,
        coverage_data=coverage,
        timestamp=datetime.now()
    )
    
    print(f"   Test ID: {test_result.test_id}")
    print(f"   Status: {test_result.status.value}")
    print(f"   Execution Time: {test_result.execution_time:.1f}s")
    print(f"   Artifacts: {len(test_result.artifacts.logs)} logs, {len(test_result.artifacts.traces)} traces")
    
    return test_case, test_result, environment, coverage

def demonstrate_serialization():
    """Demonstrate serialization capabilities."""
    print("\n💾 Testing Serialization...")
    
    # Create a test case
    hw_config = HardwareConfig(
        architecture="arm64",
        cpu_model="ARM Cortex-A78",
        memory_mb=8192
    )
    
    test_case = TestCase(
        id="arm-boot-001",
        name="ARM Boot Test",
        description="Test ARM kernel boot sequence",
        test_type=TestType.INTEGRATION,
        target_subsystem="boot",
        required_hardware=hw_config
    )
    
    # Test JSON serialization
    json_str = test_case.to_json()
    print(f"   JSON Length: {len(json_str)} characters")
    
    # Test deserialization
    restored_test = TestCase.from_json(json_str)
    print(f"   Restored ID: {restored_test.id}")
    print(f"   Restored Name: {restored_test.name}")
    print(f"   Restored Type: {restored_test.test_type.value}")
    
    # Verify integrity
    assert restored_test.id == test_case.id
    assert restored_test.name == test_case.name
    assert restored_test.test_type == test_case.test_type
    assert restored_test.required_hardware.architecture == hw_config.architecture
    
    print("   ✅ Serialization integrity verified")

def demonstrate_failure_handling():
    """Demonstrate failure data handling."""
    print("\n❌ Creating Failure Scenario...")
    
    # Create failure info
    failure_info = FailureInfo(
        error_message="Kernel panic: Unable to handle kernel paging request",
        stack_trace="""Call Trace:
 [<ffffffff81234567>] page_fault_handler+0x123/0x456
 [<ffffffff81345678>] do_page_fault+0x234/0x567
 [<ffffffff81456789>] page_fault+0x345/0x678
 [<ffffffff81567890>] kmalloc+0x456/0x789
""",
        exit_code=-11,
        kernel_panic=True,
        metadata={"fault_address": "0xdeadbeef", "cpu": 2}
    )
    
    print(f"   Error: {failure_info.error_message}")
    print(f"   Exit Code: {failure_info.exit_code}")
    print(f"   Kernel Panic: {failure_info.kernel_panic}")
    print(f"   Stack Trace Lines: {len(failure_info.stack_trace.split())}")
    
    # Create failed test result
    hw_config = HardwareConfig(
        architecture="x86_64",
        cpu_model="Intel i5",
        memory_mb=4096
    )
    
    environment = Environment(
        id="env-debug-001",
        config=hw_config,
        status=EnvironmentStatus.ERROR,
        kernel_version="6.5.0-debug"
    )
    
    failed_result = TestResult(
        test_id="debug-test-001",
        status=TestStatus.FAILED,
        execution_time=45.2,
        environment=environment,
        failure_info=failure_info
    )
    
    print(f"   Failed Test: {failed_result.test_id}")
    print(f"   Status: {failed_result.status.value}")
    print(f"   Environment Status: {failed_result.environment.status.value}")

def main():
    """Main demonstration function."""
    print("🗄️  Database Layer Usage Examples")
    print("=" * 50)
    
    try:
        # Demonstrate core functionality
        test_case, test_result, environment, coverage = demonstrate_data_models()
        
        # Demonstrate serialization
        demonstrate_serialization()
        
        # Demonstrate failure handling
        demonstrate_failure_handling()
        
        print("\n✅ All examples completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Install SQLAlchemy: pip install sqlalchemy psycopg2-binary")
        print("   2. Configure database in .env file")
        print("   3. Run migrations: python -m database.cli migrate")
        print("   4. Use repositories to store/retrieve data")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())