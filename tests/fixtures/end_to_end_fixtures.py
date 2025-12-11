"""Comprehensive test fixtures for end-to-end integration testing."""

import pytest
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, TestType, RiskLevel, CodeAnalysis, Function,
    ArtifactBundle, CoverageData, FailureInfo, Peripheral, Credentials,
    ExpectedOutcome, Commit, FixSuggestion, FailureAnalysis
)
from orchestrator.scheduler import Priority


@pytest.fixture
def comprehensive_test_environments():
    """Provide comprehensive set of test environments for end-to-end testing."""
    return [
        # Virtual x86_64 environments
        Environment(
            id="env-x86-qemu-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon E5-2686 v4",
                memory_mb=4096,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu",
                peripherals=[
                    Peripheral(name="eth0", type="network", model="e1000e"),
                    Peripheral(name="sda", type="storage", model="QEMU HARDDISK")
                ]
            ),
            status=EnvironmentStatus.IDLE,
            kernel_version="6.1.0-rc1",
            ip_address="192.168.122.10",
            ssh_credentials=Credentials(
                username="root",
                private_key_path="/tmp/test_key"
            ),
            metadata={
                "env_dir": "/tmp/env-x86-qemu-1",
                "boot_time": 15,
                "max_memory": 4096
            }
        ),
        
        Environment(
            id="env-x86-kvm-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Core i7-9700K",
                memory_mb=8192,
                storage_type="nvme",
                is_virtual=True,
                emulator="kvm",
                peripherals=[
                    Peripheral(name="ens3", type="network", model="virtio-net"),
                    Peripheral(name="vda", type="storage", model="virtio-blk")
                ]
            ),
            status=EnvironmentStatus.IDLE,
            kernel_version="6.1.0-rc1",
            ip_address="192.168.122.11",
            ssh_credentials=Credentials(
                username="root",
                private_key_path="/tmp/test_key"
            ),
            metadata={
                "env_dir": "/tmp/env-x86-kvm-1",
                "boot_time": 8,
                "max_memory": 8192,
                "kvm_acceleration": True
            }
        ),
        
        # ARM64 virtual environment
        Environment(
            id="env-arm64-qemu-1",
            config=HardwareConfig(
                architecture="arm64",
                cpu_model="ARM Cortex-A72",
                memory_mb=2048,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu",
                peripherals=[
                    Peripheral(name="eth0", type="network", model="virtio-net"),
                    Peripheral(name="sda", type="storage", model="QEMU HARDDISK")
                ]
            ),
            status=EnvironmentStatus.IDLE,
            kernel_version="6.1.0-rc1",
            ip_address="192.168.122.20",
            ssh_credentials=Credentials(
                username="root",
                private_key_path="/tmp/test_key"
            ),
            metadata={
                "env_dir": "/tmp/env-arm64-qemu-1",
                "boot_time": 20,
                "max_memory": 2048,
                "cross_compile": True
            }
        ),
        
        # RISC-V virtual environment
        Environment(
            id="env-riscv64-qemu-1",
            config=HardwareConfig(
                architecture="riscv64",
                cpu_model="SiFive U74",
                memory_mb=1024,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu",
                peripherals=[
                    Peripheral(name="eth0", type="network", model="virtio-net"),
                    Peripheral(name="sda", type="storage", model="QEMU HARDDISK")
                ]
            ),
            status=EnvironmentStatus.IDLE,
            kernel_version="6.1.0-rc1",
            ip_address="192.168.122.30",
            ssh_credentials=Credentials(
                username="root",
                private_key_path="/tmp/test_key"
            ),
            metadata={
                "env_dir": "/tmp/env-riscv64-qemu-1",
                "boot_time": 25,
                "max_memory": 1024,
                "experimental": True
            }
        ),
        
        # Physical hardware environments
        Environment(
            id="env-physical-x86-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon Gold 6248",
                memory_mb=16384,
                storage_type="nvme",
                is_virtual=False,
                peripherals=[
                    Peripheral(name="eno1", type="network", model="Intel I350"),
                    Peripheral(name="nvme0n1", type="storage", model="Samsung PM983"),
                    Peripheral(name="gpu0", type="gpu", model="NVIDIA Tesla V100")
                ]
            ),
            status=EnvironmentStatus.IDLE,
            kernel_version="6.1.0-rc1",
            ip_address="192.168.1.100",
            ssh_credentials=Credentials(
                username="testuser",
                private_key_path="/tmp/physical_key"
            ),
            metadata={
                "env_dir": "/home/testuser/testing",
                "power_control": "ipmi://192.168.1.101",
                "serial_console": "telnet://192.168.1.102:2001",
                "bootloader": "grub2",
                "max_memory": 16384
            }
        ),
        
        Environment(
            id="env-physical-arm64-1",
            config=HardwareConfig(
                architecture="arm64",
                cpu_model="ARM Cortex-A78",
                memory_mb=4096,
                storage_type="emmc",
                is_virtual=False,
                peripherals=[
                    Peripheral(name="eth0", type="network", model="Realtek RTL8111"),
                    Peripheral(name="mmcblk0", type="storage", model="Samsung eMMC"),
                    Peripheral(name="uart0", type="serial", model="ARM PL011")
                ]
            ),
            status=EnvironmentStatus.IDLE,
            kernel_version="6.1.0-rc1",
            ip_address="192.168.1.110",
            ssh_credentials=Credentials(
                username="pi",
                private_key_path="/tmp/arm_key"
            ),
            metadata={
                "env_dir": "/home/pi/testing",
                "power_control": "gpio://pin18",
                "serial_console": "telnet://192.168.1.112:2002",
                "bootloader": "u-boot",
                "max_memory": 4096,
                "board_type": "raspberry_pi_4"
            }
        )
    ]


@pytest.fixture
def comprehensive_test_cases():
    """Provide comprehensive set of test cases for different scenarios."""
    return [
        # Unit tests
        TestCase(
            id="unit-scheduler-001",
            name="Scheduler Core Unit Test",
            description="Test core scheduler functionality",
            test_type=TestType.UNIT,
            target_subsystem="scheduler",
            code_paths=["kernel/sched/core.c::schedule", "kernel/sched/fair.c::pick_next_task_fair"],
            execution_time_estimate=60,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            ),
            test_script="""#!/bin/bash
set -e
echo "Testing scheduler core functionality..."

# Test 1: Basic scheduling
echo "Test 1: Basic scheduling operations"
cat > /tmp/sched_test.c << 'EOF'
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main() {
    pid_t pid = fork();
    if (pid == 0) {
        printf("Child process running\\n");
        sleep(1);
        return 0;
    } else {
        printf("Parent process waiting\\n");
        wait(NULL);
        printf("Child completed\\n");
    }
    return 0;
}
EOF

gcc -o /tmp/sched_test /tmp/sched_test.c
/tmp/sched_test

# Test 2: Priority scheduling
echo "Test 2: Priority scheduling"
nice -n 10 sleep 0.1 &
nice -n -10 sleep 0.1 &
wait

echo "Scheduler unit test completed successfully"
""",
            expected_outcome=ExpectedOutcome(
                should_pass=True,
                expected_return_code=0,
                should_not_crash=True,
                max_execution_time=60
            ),
            metadata={
                "test_category": "unit",
                "subsystem": "scheduler",
                "complexity": "medium"
            }
        ),
        
        TestCase(
            id="unit-memory-001",
            name="Memory Management Unit Test",
            description="Test memory allocation and deallocation",
            test_type=TestType.UNIT,
            target_subsystem="memory_management",
            code_paths=["mm/page_alloc.c::alloc_pages", "mm/slab.c::kmalloc"],
            execution_time_estimate=90,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=4096,
                is_virtual=True
            ),
            test_script="""#!/bin/bash
set -e
echo "Testing memory management..."

# Test 1: Basic allocation
echo "Test 1: Basic memory allocation"
cat > /tmp/mem_test.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    // Test malloc/free
    void *ptr = malloc(1024 * 1024);  // 1MB
    if (!ptr) {
        printf("malloc failed\\n");
        return 1;
    }
    memset(ptr, 0xAA, 1024 * 1024);
    free(ptr);
    
    // Test multiple allocations
    void *ptrs[100];
    for (int i = 0; i < 100; i++) {
        ptrs[i] = malloc(1024);
        if (!ptrs[i]) {
            printf("malloc %d failed\\n", i);
            return 1;
        }
    }
    
    for (int i = 0; i < 100; i++) {
        free(ptrs[i]);
    }
    
    printf("Memory test completed successfully\\n");
    return 0;
}
EOF

gcc -o /tmp/mem_test /tmp/mem_test.c
/tmp/mem_test

# Test 2: Memory pressure
echo "Test 2: Memory pressure handling"
free -h
echo "Memory unit test completed successfully"
""",
            expected_outcome=ExpectedOutcome(
                should_pass=True,
                expected_return_code=0,
                should_not_crash=True,
                max_execution_time=90
            ),
            metadata={
                "test_category": "unit",
                "subsystem": "memory_management",
                "complexity": "medium"
            }
        ),
        
        # Integration tests
        TestCase(
            id="integration-network-001",
            name="Network Stack Integration Test",
            description="Test network stack integration with drivers",
            test_type=TestType.INTEGRATION,
            target_subsystem="networking",
            code_paths=["net/core/", "drivers/net/"],
            execution_time_estimate=180,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True,
                peripherals=[
                    Peripheral(name="eth0", type="network", model="e1000e")
                ]
            ),
            test_script="""#!/bin/bash
set -e
echo "Testing network stack integration..."

# Test 1: Interface configuration
echo "Test 1: Network interface configuration"
ip link show
ip addr show

# Test 2: Basic connectivity
echo "Test 2: Basic network connectivity"
ping -c 3 127.0.0.1
ping -c 1 8.8.8.8 || echo "External ping failed (expected in isolated env)"

# Test 3: Socket operations
echo "Test 3: Socket operations"
cat > /tmp/socket_test.c << 'EOF'
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        printf("Socket creation failed\\n");
        return 1;
    }
    
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(12345);
    addr.sin_addr.s_addr = INADDR_ANY;
    
    if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        printf("Bind failed\\n");
        close(sock);
        return 1;
    }
    
    close(sock);
    printf("Socket test completed successfully\\n");
    return 0;
}
EOF

gcc -o /tmp/socket_test /tmp/socket_test.c
/tmp/socket_test

echo "Network integration test completed successfully"
""",
            expected_outcome=ExpectedOutcome(
                should_pass=True,
                expected_return_code=0,
                should_not_crash=True,
                max_execution_time=180
            ),
            metadata={
                "test_category": "integration",
                "subsystem": "networking",
                "complexity": "high",
                "requires_network": True
            }
        ),
        
        # Performance tests
        TestCase(
            id="performance-scheduler-001",
            name="Scheduler Performance Benchmark",
            description="Measure scheduler performance metrics",
            test_type=TestType.PERFORMANCE,
            target_subsystem="scheduler",
            code_paths=["kernel/sched/"],
            execution_time_estimate=300,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=4096,
                is_virtual=True
            ),
            test_script="""#!/bin/bash
set -e
echo "Starting scheduler performance benchmark..."

# Test 1: Context switch latency
echo "Test 1: Context switch latency measurement"
cat > /tmp/context_switch_bench.c << 'EOF'
#include <stdio.h>
#include <unistd.h>
#include <sys/time.h>
#include <sys/wait.h>

int main() {
    int pipefd[2];
    pipe(pipefd);
    
    struct timeval start, end;
    gettimeofday(&start, NULL);
    
    pid_t pid = fork();
    if (pid == 0) {
        // Child
        char c;
        for (int i = 0; i < 1000; i++) {
            read(pipefd[0], &c, 1);
            write(pipefd[1], &c, 1);
        }
        return 0;
    } else {
        // Parent
        char c = 'x';
        for (int i = 0; i < 1000; i++) {
            write(pipefd[1], &c, 1);
            read(pipefd[0], &c, 1);
        }
        wait(NULL);
    }
    
    gettimeofday(&end, NULL);
    double elapsed = (end.tv_sec - start.tv_sec) * 1000000.0 + (end.tv_usec - start.tv_usec);
    double per_switch = elapsed / 2000.0;  // 2000 context switches
    
    printf("Context switch latency: %.2f microseconds\\n", per_switch);
    
    // Write results for collection
    FILE *f = fopen("/tmp/perf_results.txt", "w");
    fprintf(f, "context_switch_latency_us: %.2f\\n", per_switch);
    fclose(f);
    
    return 0;
}
EOF

gcc -o /tmp/context_switch_bench /tmp/context_switch_bench.c
/tmp/context_switch_bench

# Test 2: Scheduling latency
echo "Test 2: Scheduling latency measurement"
cyclictest -t 1 -p 80 -n -i 1000 -l 1000 -q || echo "cyclictest not available, skipping"

echo "Scheduler performance benchmark completed"
""",
            expected_outcome=ExpectedOutcome(
                should_pass=True,
                expected_return_code=0,
                should_not_crash=True,
                max_execution_time=300
            ),
            metadata={
                "test_category": "performance",
                "subsystem": "scheduler",
                "complexity": "high",
                "metrics": ["context_switch_latency_us", "scheduling_latency_us"]
            }
        ),
        
        # Security tests
        TestCase(
            id="security-syscall-001",
            name="System Call Security Test",
            description="Test system call security and fuzzing",
            test_type=TestType.SECURITY,
            target_subsystem="syscalls",
            code_paths=["arch/x86/entry/", "kernel/sys.c"],
            execution_time_estimate=240,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            ),
            test_script="""#!/bin/bash
set -e
echo "Starting system call security test..."

# Test 1: Invalid parameter fuzzing
echo "Test 1: Invalid parameter fuzzing"
cat > /tmp/syscall_fuzz.c << 'EOF'
#include <stdio.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <errno.h>

int main() {
    // Test invalid pointers
    int result;
    
    // Test 1: Invalid read pointer
    result = syscall(SYS_read, 0, (void*)0x1, 1);
    if (result != -1 || errno != EFAULT) {
        printf("Invalid read pointer not handled correctly\\n");
    }
    
    // Test 2: Invalid write pointer  
    result = syscall(SYS_write, 1, (void*)0x1, 1);
    if (result != -1 || errno != EFAULT) {
        printf("Invalid write pointer not handled correctly\\n");
    }
    
    // Test 3: Large buffer sizes
    result = syscall(SYS_read, 0, NULL, 0x7FFFFFFF);
    if (result != -1) {
        printf("Large buffer size not handled correctly\\n");
    }
    
    printf("System call fuzzing completed\\n");
    return 0;
}
EOF

gcc -o /tmp/syscall_fuzz /tmp/syscall_fuzz.c
/tmp/syscall_fuzz

# Test 2: Privilege escalation attempts
echo "Test 2: Privilege escalation detection"
# Test setuid with invalid parameters
setuid 99999 2>/dev/null && echo "SECURITY ISSUE: setuid succeeded with invalid uid" || echo "setuid properly rejected invalid uid"

echo "System call security test completed"
""",
            expected_outcome=ExpectedOutcome(
                should_pass=True,
                expected_return_code=0,
                should_not_crash=True,
                max_execution_time=240
            ),
            metadata={
                "test_category": "security",
                "subsystem": "syscalls",
                "complexity": "high",
                "security_focus": ["input_validation", "privilege_escalation"]
            }
        ),
        
        # Fuzz tests
        TestCase(
            id="fuzz-filesystem-001",
            name="Filesystem Fuzzing Test",
            description="Fuzz filesystem operations for robustness",
            test_type=TestType.FUZZ,
            target_subsystem="filesystem",
            code_paths=["fs/", "include/linux/fs.h"],
            execution_time_estimate=360,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            ),
            test_script="""#!/bin/bash
set -e
echo "Starting filesystem fuzzing test..."

# Create test directory
mkdir -p /tmp/fuzz_test
cd /tmp/fuzz_test

# Test 1: Filename fuzzing
echo "Test 1: Filename fuzzing"
for i in {1..50}; do
    # Generate random filename
    filename=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c $((RANDOM % 100 + 1)))
    
    # Try to create file
    touch "$filename" 2>/dev/null || true
    
    # Try various operations
    ls "$filename" 2>/dev/null || true
    rm "$filename" 2>/dev/null || true
done

# Test 2: Path traversal attempts
echo "Test 2: Path traversal fuzzing"
dangerous_paths=(
    "../../../etc/passwd"
    "../../../../root/.ssh/id_rsa"
    "/proc/self/mem"
    "/dev/kmem"
)

for path in "${dangerous_paths[@]}"; do
    cat "$path" 2>/dev/null && echo "SECURITY ISSUE: Accessed $path" || echo "Access to $path properly blocked"
done

# Test 3: Large file operations
echo "Test 3: Large file operations"
dd if=/dev/zero of=large_file bs=1M count=10 2>/dev/null || echo "Large file creation failed (expected)"
rm -f large_file

echo "Filesystem fuzzing test completed"
""",
            expected_outcome=ExpectedOutcome(
                should_pass=True,
                expected_return_code=0,
                should_not_crash=True,
                max_execution_time=360
            ),
            metadata={
                "test_category": "fuzz",
                "subsystem": "filesystem",
                "complexity": "high",
                "fuzzing_targets": ["filenames", "paths", "file_operations"]
            }
        )
    ]


@pytest.fixture
def sample_test_results(comprehensive_test_environments, comprehensive_test_cases):
    """Provide sample test results for analysis testing."""
    results = []
    
    for i, (env, test_case) in enumerate(zip(comprehensive_test_environments, comprehensive_test_cases)):
        # Create varied results
        if i % 4 == 0:
            # Failed result with failure info
            result = TestResult(
                test_id=test_case.id,
                status=TestStatus.FAILED,
                execution_time=test_case.execution_time_estimate * 0.8,
                environment=env,
                artifacts=ArtifactBundle(
                    logs=[f"/tmp/logs/{test_case.id}.log"],
                    core_dumps=[f"/tmp/cores/{test_case.id}.core"] if i % 8 == 0 else [],
                    traces=[f"/tmp/traces/{test_case.id}.trace"]
                ),
                coverage_data=CoverageData(
                    line_coverage=0.65,
                    branch_coverage=0.58,
                    function_coverage=0.72,
                    covered_lines=[f"file.c:{j}" for j in range(100, 200, 3)],
                    uncovered_lines=[f"file.c:{j}" for j in range(200, 250, 2)]
                ),
                failure_info=FailureInfo(
                    error_message="Assertion failed in scheduler path",
                    stack_trace="kernel_panic+0x123\nschedule+0x456\n",
                    exit_code=1,
                    kernel_panic=i % 8 == 0,
                    timeout_occurred=False
                ),
                timestamp=datetime.now() - timedelta(hours=i)
            )
        elif i % 4 == 1:
            # Timeout result
            result = TestResult(
                test_id=test_case.id,
                status=TestStatus.TIMEOUT,
                execution_time=test_case.execution_time_estimate * 1.5,
                environment=env,
                artifacts=ArtifactBundle(
                    logs=[f"/tmp/logs/{test_case.id}.log"]
                ),
                failure_info=FailureInfo(
                    error_message=f"Test timed out after {test_case.execution_time_estimate} seconds",
                    timeout_occurred=True
                ),
                timestamp=datetime.now() - timedelta(hours=i)
            )
        elif i % 4 == 2:
            # Error result
            result = TestResult(
                test_id=test_case.id,
                status=TestStatus.ERROR,
                execution_time=test_case.execution_time_estimate * 0.3,
                environment=env,
                artifacts=ArtifactBundle(
                    logs=[f"/tmp/logs/{test_case.id}.log"]
                ),
                failure_info=FailureInfo(
                    error_message="Environment setup failed",
                    exit_code=2
                ),
                timestamp=datetime.now() - timedelta(hours=i)
            )
        else:
            # Passed result
            result = TestResult(
                test_id=test_case.id,
                status=TestStatus.PASSED,
                execution_time=test_case.execution_time_estimate * 0.9,
                environment=env,
                artifacts=ArtifactBundle(
                    logs=[f"/tmp/logs/{test_case.id}.log"]
                ),
                coverage_data=CoverageData(
                    line_coverage=0.85,
                    branch_coverage=0.78,
                    function_coverage=0.92,
                    covered_lines=[f"file.c:{j}" for j in range(100, 300, 2)],
                    uncovered_lines=[f"file.c:{j}" for j in range(300, 320)]
                ),
                timestamp=datetime.now() - timedelta(hours=i)
            )
        
        results.append(result)
    
    return results


@pytest.fixture
def sample_code_analyses():
    """Provide sample code analyses for testing."""
    return [
        CodeAnalysis(
            changed_files=["kernel/sched/core.c", "kernel/sched/fair.c"],
            changed_functions=[
                Function(
                    name="schedule",
                    file_path="kernel/sched/core.c",
                    line_number=100,
                    signature="void schedule(void)",
                    subsystem="scheduler"
                ),
                Function(
                    name="pick_next_task_fair",
                    file_path="kernel/sched/fair.c",
                    line_number=200,
                    signature="struct task_struct *pick_next_task_fair(struct rq *rq)",
                    subsystem="scheduler"
                )
            ],
            affected_subsystems=["scheduler"],
            impact_score=0.8,
            risk_level=RiskLevel.HIGH,
            suggested_test_types=[TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE],
            related_tests=["unit-scheduler-001", "performance-scheduler-001"]
        ),
        
        CodeAnalysis(
            changed_files=["mm/page_alloc.c", "mm/slab.c"],
            changed_functions=[
                Function(
                    name="alloc_pages",
                    file_path="mm/page_alloc.c",
                    line_number=300,
                    signature="struct page *alloc_pages(gfp_t gfp_mask, unsigned int order)",
                    subsystem="memory_management"
                ),
                Function(
                    name="kmalloc",
                    file_path="mm/slab.c",
                    line_number=150,
                    signature="void *kmalloc(size_t size, gfp_t flags)",
                    subsystem="memory_management"
                )
            ],
            affected_subsystems=["memory_management"],
            impact_score=0.9,
            risk_level=RiskLevel.CRITICAL,
            suggested_test_types=[TestType.UNIT, TestType.SECURITY, TestType.FUZZ],
            related_tests=["unit-memory-001", "security-syscall-001"]
        ),
        
        CodeAnalysis(
            changed_files=["net/core/dev.c", "drivers/net/ethernet/intel/e1000e/netdev.c"],
            changed_functions=[
                Function(
                    name="netif_receive_skb",
                    file_path="net/core/dev.c",
                    line_number=500,
                    signature="int netif_receive_skb(struct sk_buff *skb)",
                    subsystem="networking"
                )
            ],
            affected_subsystems=["networking"],
            impact_score=0.6,
            risk_level=RiskLevel.MEDIUM,
            suggested_test_types=[TestType.INTEGRATION, TestType.PERFORMANCE],
            related_tests=["integration-network-001"]
        )
    ]


@pytest.fixture
def sample_failure_analyses():
    """Provide sample failure analyses for testing."""
    return [
        FailureAnalysis(
            failure_id="unit-scheduler-001",
            root_cause="Race condition in scheduler task selection",
            confidence=0.85,
            suspicious_commits=[
                Commit(
                    sha="abc123def456",
                    message="Optimize scheduler task selection",
                    author="developer@example.com",
                    timestamp=datetime.now() - timedelta(days=2),
                    files_changed=["kernel/sched/core.c", "kernel/sched/fair.c"]
                )
            ],
            error_pattern="BUG: scheduling while atomic",
            stack_trace="schedule+0x123\npick_next_task+0x456\n",
            suggested_fixes=[
                FixSuggestion(
                    description="Add proper locking around task selection",
                    code_patch="spin_lock(&rq->lock);\n// task selection code\nspin_unlock(&rq->lock);",
                    confidence=0.9,
                    rationale="The race condition occurs when multiple CPUs access task queues simultaneously"
                )
            ],
            related_failures=["performance-scheduler-001"],
            reproducibility=0.7
        ),
        
        FailureAnalysis(
            failure_id="unit-memory-001",
            root_cause="Memory leak in page allocation error path",
            confidence=0.92,
            suspicious_commits=[
                Commit(
                    sha="def456ghi789",
                    message="Add error handling to page allocator",
                    author="maintainer@example.com",
                    timestamp=datetime.now() - timedelta(days=1),
                    files_changed=["mm/page_alloc.c"]
                )
            ],
            error_pattern="KASAN: use-after-free",
            stack_trace="kfree+0x123\nalloc_pages+0x456\n",
            suggested_fixes=[
                FixSuggestion(
                    description="Fix memory leak in error path",
                    code_patch="if (error) {\n    free_pages(page, order);\n    return NULL;\n}",
                    confidence=0.95,
                    rationale="Error path is not properly freeing allocated pages"
                )
            ],
            related_failures=[],
            reproducibility=0.95
        )
    ]


@pytest.fixture
def mock_vcs_events():
    """Provide mock VCS events for CI/CD testing."""
    return [
        {
            'event_type': 'push',
            'repository': 'torvalds/linux',
            'branch': 'master',
            'commit_sha': 'abc123def456789',
            'author': 'torvalds@linux-foundation.org',
            'message': 'scheduler: fix race condition in task selection',
            'changed_files': ['kernel/sched/core.c', 'kernel/sched/fair.c'],
            'timestamp': datetime.now().isoformat(),
            'diff': """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -100,6 +100,10 @@ void schedule(void)
     struct task_struct *prev, *next;
     
     prev = current;
+    
+    /* Fix race condition */
+    if (need_resched())
+        return;
     
     next = pick_next_task(rq);
"""
        },
        
        {
            'event_type': 'pull_request',
            'repository': 'torvalds/linux',
            'branch': 'feature/memory-optimization',
            'base_branch': 'master',
            'pr_number': 12345,
            'commit_sha': 'def456ghi789abc',
            'author': 'contributor@example.com',
            'message': 'mm: optimize page allocation for large orders',
            'changed_files': ['mm/page_alloc.c', 'mm/compaction.c'],
            'timestamp': datetime.now().isoformat(),
            'diff': """
diff --git a/mm/page_alloc.c b/mm/page_alloc.c
index 7890abc..def1234 100644
--- a/mm/page_alloc.c
+++ b/mm/page_alloc.c
@@ -200,6 +200,15 @@ struct page *alloc_pages(gfp_t gfp_mask, unsigned int order)
     struct page *page;
     
+    /* Optimize for large orders */
+    if (order > PAGE_ALLOC_COSTLY_ORDER) {
+        page = alloc_pages_direct_compact(gfp_mask, order);
+        if (page)
+            return page;
+    }
+    
     page = __alloc_pages(gfp_mask, order, preferred_zone);
     return page;
"""
        }
    ]


@pytest.fixture
def performance_baselines():
    """Provide performance baseline data for regression testing."""
    return {
        'scheduler': {
            'context_switch_latency_us': 1.5,
            'scheduling_latency_us': 2.1,
            'throughput_tasks_per_sec': 10000,
            'cpu_utilization_percent': 85.0
        },
        'memory_management': {
            'allocation_latency_us': 0.8,
            'deallocation_latency_us': 0.6,
            'fragmentation_percent': 15.0,
            'memory_utilization_percent': 78.0
        },
        'networking': {
            'packet_processing_latency_us': 5.2,
            'throughput_packets_per_sec': 50000,
            'bandwidth_mbps': 950.0,
            'cpu_overhead_percent': 12.0
        },
        'filesystem': {
            'read_latency_us': 100.0,
            'write_latency_us': 150.0,
            'iops': 8000,
            'cache_hit_rate_percent': 92.0
        }
    }


@pytest.fixture
def security_vulnerability_patterns():
    """Provide security vulnerability patterns for testing."""
    return [
        {
            'pattern_id': 'buffer_overflow_001',
            'name': 'Stack Buffer Overflow',
            'description': 'Potential stack buffer overflow in string handling',
            'severity': 'high',
            'cwe_id': 'CWE-121',
            'pattern_regex': r'strcpy\s*\(\s*[^,]+\s*,\s*[^)]+\)',
            'example_code': 'strcpy(buffer, user_input);',
            'fix_suggestion': 'Use strncpy or strlcpy with proper bounds checking'
        },
        
        {
            'pattern_id': 'use_after_free_001',
            'name': 'Use After Free',
            'description': 'Potential use-after-free vulnerability',
            'severity': 'critical',
            'cwe_id': 'CWE-416',
            'pattern_regex': r'kfree\s*\([^)]+\).*\*[^=]*=',
            'example_code': 'kfree(ptr); ptr->field = value;',
            'fix_suggestion': 'Set pointer to NULL after freeing and add null checks'
        },
        
        {
            'pattern_id': 'integer_overflow_001',
            'name': 'Integer Overflow',
            'description': 'Potential integer overflow in arithmetic operations',
            'severity': 'medium',
            'cwe_id': 'CWE-190',
            'pattern_regex': r'[a-zA-Z_][a-zA-Z0-9_]*\s*\+\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\*',
            'example_code': 'size = count + len * sizeof(struct item);',
            'fix_suggestion': 'Use overflow-safe arithmetic functions or add bounds checking'
        }
    ]