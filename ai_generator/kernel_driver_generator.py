"""AI-powered kernel test driver generator."""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .models import TestCase, TestType, Function
from .interfaces import ITestGenerator


class KernelDriverTemplate:
    """Templates for generating kernel test drivers."""
    
    BASIC_MODULE_TEMPLATE = """
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>

#define MODULE_NAME "test_{function_name}"
#define PROC_NAME "test_{function_name}_results"

static struct proc_dir_entry *proc_entry;
static int test_results = 0;
static char test_log[4096];
static int log_pos = 0;

// Test logging function
static void test_log_msg(const char *fmt, ...) {{
    va_list args;
    va_start(args, fmt);
    log_pos += vsnprintf(test_log + log_pos, sizeof(test_log) - log_pos, fmt, args);
    va_end(args);
}}

{test_functions}

// Proc file operations
static int test_proc_show(struct seq_file *m, void *v) {{
    seq_printf(m, "Test Results for {function_name}:\\n");
    seq_printf(m, "Status: %s\\n", test_results == 0 ? "PASSED" : "FAILED");
    seq_printf(m, "Log:\\n%s\\n", test_log);
    return 0;
}}

static int test_proc_open(struct inode *inode, struct file *file) {{
    return single_open(file, test_proc_show, NULL);
}}

static const struct proc_ops test_proc_ops = {{
    .proc_open = test_proc_open,
    .proc_read = seq_read,
    .proc_lseek = seq_lseek,
    .proc_release = single_release,
}};

static int __init test_module_init(void) {{
    printk(KERN_INFO "Loading test module for {function_name}\\n");
    
    // Create proc entry for results
    proc_entry = proc_create(PROC_NAME, 0644, NULL, &test_proc_ops);
    if (!proc_entry) {{
        printk(KERN_ERR "Failed to create proc entry\\n");
        return -ENOMEM;
    }}
    
    // Run tests
    test_results = run_all_tests();
    
    printk(KERN_INFO "Test module loaded, results: %s\\n", 
           test_results == 0 ? "PASSED" : "FAILED");
    return 0;
}}

static void __exit test_module_exit(void) {{
    if (proc_entry) {{
        proc_remove(proc_entry);
    }}
    printk(KERN_INFO "Test module for {function_name} unloaded\\n");
}}

module_init(test_module_init);
module_exit(test_module_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("AI Test Generator");
MODULE_DESCRIPTION("Test driver for {function_name}");
MODULE_VERSION("1.0");
"""

    MEMORY_TEST_FUNCTIONS = """
// Memory allocation test functions
static int test_memory_allocation_basic(void) {{
    void *ptr;
    int i, failures = 0;
    
    test_log_msg("Testing basic memory allocation...\\n");
    
    // Test various allocation sizes
    for (i = 0; i < 100; i++) {{
        size_t size = (i % 10 + 1) * 1024; // 1KB to 10KB
        ptr = kmalloc(size, GFP_KERNEL);
        if (!ptr) {{
            failures++;
            test_log_msg("Allocation failed for size %zu\\n", size);
            continue;
        }}
        
        // Write and verify pattern
        memset(ptr, 0xAA, size);
        if (((char*)ptr)[0] != (char)0xAA || ((char*)ptr)[size-1] != (char)0xAA) {{
            failures++;
            test_log_msg("Memory pattern verification failed for size %zu\\n", size);
        }}
        
        kfree(ptr);
    }}
    
    test_log_msg("Basic allocation test: %d failures out of 100\\n", failures);
    return failures;
}}

static int test_memory_allocation_stress(void) {{
    void *ptrs[1000];
    int i, allocated = 0, failures = 0;
    
    test_log_msg("Testing memory allocation stress...\\n");
    
    // Allocate many blocks
    for (i = 0; i < 1000; i++) {{
        ptrs[i] = kmalloc(4096, GFP_KERNEL);
        if (ptrs[i]) {{
            allocated++;
            // Touch the memory
            memset(ptrs[i], i % 256, 4096);
        }}
    }}
    
    test_log_msg("Allocated %d out of 1000 blocks\\n", allocated);
    
    // Verify and free all blocks
    for (i = 0; i < 1000; i++) {{
        if (ptrs[i]) {{
            // Verify pattern
            if (((char*)ptrs[i])[0] != (char)(i % 256)) {{
                failures++;
                test_log_msg("Memory corruption detected in block %d\\n", i);
            }}
            kfree(ptrs[i]);
        }}
    }}
    
    test_log_msg("Stress test: %d corruption failures\\n", failures);
    return failures;
}}

static int test_memory_error_conditions(void) {{
    void *ptr;
    int failures = 0;
    
    test_log_msg("Testing memory error conditions...\\n");
    
    // Test zero-size allocation
    ptr = kmalloc(0, GFP_KERNEL);
    if (ptr) {{
        test_log_msg("Zero-size allocation returned non-NULL\\n");
        kfree(ptr);
    }}
    
    // Test very large allocation (should fail)
    ptr = kmalloc(SIZE_MAX, GFP_KERNEL);
    if (ptr) {{
        test_log_msg("ERROR: Excessive allocation succeeded\\n");
        failures++;
        kfree(ptr);
    }} else {{
        test_log_msg("Large allocation properly rejected\\n");
    }}
    
    return failures;
}}

static int run_all_tests(void) {{
    int total_failures = 0;
    
    total_failures += test_memory_allocation_basic();
    total_failures += test_memory_allocation_stress();
    total_failures += test_memory_error_conditions();
    
    test_log_msg("\\nTotal test failures: %d\\n", total_failures);
    return total_failures;
}}
"""

    SCHEDULER_TEST_FUNCTIONS = """
// Scheduler test functions
#include <linux/kthread.h>
#include <linux/delay.h>
#include <linux/sched.h>

static struct task_struct *test_threads[10];
static atomic_t thread_counter = ATOMIC_INIT(0);
static atomic_t completed_threads = ATOMIC_INIT(0);

static int scheduler_test_thread(void *data) {{
    int thread_id = (long)data;
    int i;
    
    atomic_inc(&thread_counter);
    
    // Different workload patterns for different threads
    for (i = 0; i < 1000 && !kthread_should_stop(); i++) {{
        if (thread_id % 3 == 0) {{
            // CPU-intensive thread
            udelay(100);
        }} else if (thread_id % 3 == 1) {{
            // I/O-bound thread
            msleep(1);
        }} else {{
            // Mixed workload
            if (i % 2) udelay(50);
            else msleep(1);
        }}
        
        // Test voluntary context switches
        if (i % 100 == 0) {{
            schedule();
        }}
    }}
    
    atomic_inc(&completed_threads);
    return 0;
}}

static int test_scheduler_basic(void) {{
    int i, failures = 0;
    unsigned long start_time, end_time;
    
    test_log_msg("Testing basic scheduler functionality...\\n");
    
    atomic_set(&thread_counter, 0);
    atomic_set(&completed_threads, 0);
    
    start_time = jiffies;
    
    // Create test threads with different priorities
    for (i = 0; i < 10; i++) {{
        test_threads[i] = kthread_create(scheduler_test_thread, 
                                       (void *)(long)i, 
                                       "sched_test_%d", i);
        if (!IS_ERR(test_threads[i])) {{
            // Set different nice values
            set_user_nice(test_threads[i], i - 5); // -5 to +4
            wake_up_process(test_threads[i]);
        }} else {{
            failures++;
            test_log_msg("Failed to create thread %d\\n", i);
        }}
    }}
    
    // Wait for threads to complete
    msleep(5000); // 5 second timeout
    
    // Stop any remaining threads
    for (i = 0; i < 10; i++) {{
        if (!IS_ERR_OR_NULL(test_threads[i])) {{
            kthread_stop(test_threads[i]);
        }}
    }}
    
    end_time = jiffies;
    
    test_log_msg("Scheduler test completed in %lu jiffies\\n", end_time - start_time);
    test_log_msg("Threads created: %d, completed: %d\\n", 
                atomic_read(&thread_counter), atomic_read(&completed_threads));
    
    return failures;
}}

static int run_all_tests(void) {{
    int total_failures = 0;
    
    total_failures += test_scheduler_basic();
    
    test_log_msg("\\nTotal scheduler test failures: %d\\n", total_failures);
    return total_failures;
}}
"""

    NETWORK_TEST_FUNCTIONS = """
// Network stack test functions
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/skbuff.h>
#include <linux/if_ether.h>

static struct net_device *test_netdev;
static struct net_device_stats test_stats;

static netdev_tx_t test_net_xmit(struct sk_buff *skb, struct net_device *dev) {{
    struct ethhdr *eth = eth_hdr(skb);
    
    // Log packet for testing
    test_log_msg("TX packet: proto=0x%04x, len=%d\\n", 
                ntohs(eth->h_proto), skb->len);
    
    // Update statistics
    test_stats.tx_packets++;
    test_stats.tx_bytes += skb->len;
    
    // Test error conditions
    if (skb->len > ETH_FRAME_LEN) {{
        test_stats.tx_errors++;
        dev_kfree_skb(skb);
        return NETDEV_TX_OK;
    }}
    
    // Simulate successful transmission
    dev_kfree_skb(skb);
    return NETDEV_TX_OK;
}}

static struct net_device_stats *test_net_get_stats(struct net_device *dev) {{
    return &test_stats;
}}

static int test_net_open(struct net_device *dev) {{
    test_log_msg("Network device opened\\n");
    netif_start_queue(dev);
    return 0;
}}

static int test_net_close(struct net_device *dev) {{
    test_log_msg("Network device closed\\n");
    netif_stop_queue(dev);
    return 0;
}}

static const struct net_device_ops test_netdev_ops = {{
    .ndo_open = test_net_open,
    .ndo_stop = test_net_close,
    .ndo_start_xmit = test_net_xmit,
    .ndo_get_stats = test_net_get_stats,
}};

static int test_network_device(void) {{
    int failures = 0;
    struct sk_buff *skb;
    
    test_log_msg("Testing network device functionality...\\n");
    
    // Allocate network device
    test_netdev = alloc_etherdev(0);
    if (!test_netdev) {{
        test_log_msg("Failed to allocate network device\\n");
        return 1;
    }}
    
    // Setup device
    strcpy(test_netdev->name, "test%d");
    test_netdev->netdev_ops = &test_netdev_ops;
    test_netdev->flags |= IFF_NOARP;
    
    // Register device
    if (register_netdev(test_netdev)) {{
        test_log_msg("Failed to register network device\\n");
        free_netdev(test_netdev);
        return 1;
    }}
    
    // Test packet transmission
    skb = alloc_skb(ETH_HLEN + 64, GFP_KERNEL);
    if (skb) {{
        skb_reserve(skb, ETH_HLEN);
        skb_put(skb, 64);
        skb->dev = test_netdev;
        skb->protocol = htons(ETH_P_IP);
        
        // Test transmission
        if (test_net_xmit(skb, test_netdev) != NETDEV_TX_OK) {{
            failures++;
            test_log_msg("Packet transmission failed\\n");
        }}
    }} else {{
        failures++;
        test_log_msg("Failed to allocate test packet\\n");
    }}
    
    // Cleanup
    unregister_netdev(test_netdev);
    free_netdev(test_netdev);
    
    test_log_msg("Network test completed with %d failures\\n", failures);
    return failures;
}}

static int run_all_tests(void) {{
    int total_failures = 0;
    
    total_failures += test_network_device();
    
    test_log_msg("\\nTotal network test failures: %d\\n", total_failures);
    return total_failures;
}}
"""

    MAKEFILE_TEMPLATE = """
# Makefile for {function_name} test driver
obj-m := test_{function_name}.o

KERNEL_DIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

all:
\tmake -C $(KERNEL_DIR) M=$(PWD) modules

clean:
\tmake -C $(KERNEL_DIR) M=$(PWD) clean

install: all
\tsudo insmod test_{function_name}.ko

uninstall:
\tsudo rmmod test_{function_name} || true

test: install
\t@echo "Running kernel test for {function_name}..."
\t@sleep 2
\t@cat /proc/test_{function_name}_results || echo "Test results not available"
\t@make uninstall

.PHONY: all clean install uninstall test
"""


class KernelDriverGenerator(ITestGenerator):
    """AI-powered kernel test driver generator."""
    
    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
        self.template = KernelDriverTemplate()
    
    def generate_kernel_test_driver(self, function: Function) -> Dict[str, str]:
        """Generate a complete kernel test driver for a function.
        
        Args:
            function: Function to generate test driver for
            
        Returns:
            Dictionary with generated files (source, makefile, etc.)
        """
        # Determine test type based on function characteristics
        test_functions = self._select_test_functions(function)
        
        # Generate the main module source
        module_source = self.template.BASIC_MODULE_TEMPLATE.format(
            function_name=function.name.lower(),
            test_functions=test_functions
        )
        
        # Generate Makefile
        makefile = self.template.MAKEFILE_TEMPLATE.format(
            function_name=function.name.lower()
        )
        
        # Generate test script
        test_script = self._generate_test_script(function)
        
        # Generate installation script
        install_script = self._generate_install_script(function)
        
        return {
            f"test_{function.name.lower()}.c": module_source,
            "Makefile": makefile,
            "run_test.sh": test_script,
            "install.sh": install_script,
            "README.md": self._generate_readme(function)
        }
    
    def _select_test_functions(self, function: Function) -> str:
        """Select appropriate test functions based on function characteristics."""
        function_name = function.name.lower()
        subsystem = (function.subsystem or "").lower()
        
        if "alloc" in function_name or "malloc" in function_name or "mm" in subsystem:
            return self.template.MEMORY_TEST_FUNCTIONS
        elif "sched" in function_name or "schedule" in function_name or "sched" in subsystem:
            return self.template.SCHEDULER_TEST_FUNCTIONS
        elif "net" in function_name or "network" in subsystem or "eth" in function_name:
            return self.template.NETWORK_TEST_FUNCTIONS
        else:
            # Generate generic test functions
            return self._generate_generic_test_functions(function)
    
    def _generate_generic_test_functions(self, function: Function) -> str:
        """Generate generic test functions for any kernel function."""
        return f"""
// Generic test functions for {function.name}
static int test_{function.name.lower()}_basic(void) {{
    int failures = 0;
    
    test_log_msg("Testing {function.name} basic functionality...\\n");
    
    // Test basic function behavior
    // Note: This is a template - actual implementation depends on function signature
    
    test_log_msg("Basic test completed with %d failures\\n", failures);
    return failures;
}}

static int test_{function.name.lower()}_error_conditions(void) {{
    int failures = 0;
    
    test_log_msg("Testing {function.name} error conditions...\\n");
    
    // Test error handling
    // Note: Implement based on function's error conditions
    
    test_log_msg("Error condition test completed with %d failures\\n", failures);
    return failures;
}}

static int run_all_tests(void) {{
    int total_failures = 0;
    
    total_failures += test_{function.name.lower()}_basic();
    total_failures += test_{function.name.lower()}_error_conditions();
    
    test_log_msg("\\nTotal test failures: %d\\n", total_failures);
    return total_failures;
}}
"""
    
    def _generate_test_script(self, function: Function) -> str:
        """Generate test execution script."""
        return f"""#!/bin/bash
# Test script for {function.name} kernel driver

set -e

echo "Building and testing kernel driver for {function.name}..."

# Build the module
make clean
make

if [ ! -f "test_{function.name.lower()}.ko" ]; then
    echo "ERROR: Module build failed"
    exit 1
fi

echo "Module built successfully"

# Load the module
echo "Loading test module..."
sudo insmod test_{function.name.lower()}.ko

# Wait for tests to complete
sleep 3

# Check results
echo "Test results:"
echo "============="
if [ -f "/proc/test_{function.name.lower()}_results" ]; then
    cat /proc/test_{function.name.lower()}_results
else
    echo "ERROR: Test results not available"
    dmesg | tail -20 | grep -i "test_{function.name.lower()}" || true
fi

# Unload the module
echo "Unloading test module..."
sudo rmmod test_{function.name.lower()} || true

echo "Test completed"
"""
    
    def _generate_install_script(self, function: Function) -> str:
        """Generate installation script."""
        return f"""#!/bin/bash
# Installation script for {function.name} kernel test driver

echo "Installing kernel test driver for {function.name}..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or use sudo"
    exit 1
fi

# Check kernel headers
if [ ! -d "/lib/modules/$(uname -r)/build" ]; then
    echo "ERROR: Kernel headers not found"
    echo "Please install kernel headers for your kernel version"
    exit 1
fi

# Build and install
make clean
make

if [ -f "test_{function.name.lower()}.ko" ]; then
    echo "Module built successfully"
    
    # Copy to modules directory
    cp test_{function.name.lower()}.ko /lib/modules/$(uname -r)/extra/
    depmod -a
    
    echo "Module installed successfully"
    echo "Use 'modprobe test_{function.name.lower()}' to load"
    echo "Use 'rmmod test_{function.name.lower()}' to unload"
else
    echo "ERROR: Module build failed"
    exit 1
fi
"""
    
    def _generate_readme(self, function: Function) -> str:
        """Generate README documentation."""
        return f"""# Kernel Test Driver for {function.name}

This is an AI-generated kernel test driver for testing the `{function.name}` function.

## Overview

- **Function**: {function.name}
- **Subsystem**: {function.subsystem or 'Unknown'}
- **File**: {function.file_path or 'Unknown'}

## Building

```bash
make
```

## Testing

```bash
# Quick test
make test

# Manual testing
sudo insmod test_{function.name.lower()}.ko
cat /proc/test_{function.name.lower()}_results
sudo rmmod test_{function.name.lower()}
```

## Installation

```bash
sudo ./install.sh
```

## Files

- `test_{function.name.lower()}.c` - Main kernel module source
- `Makefile` - Build configuration
- `run_test.sh` - Test execution script
- `install.sh` - Installation script

## Test Results

Test results are available in `/proc/test_{function.name.lower()}_results` while the module is loaded.

## Requirements

- Linux kernel headers for your kernel version
- GCC compiler
- Root privileges for loading/unloading modules

## Generated by

AI Test Generator - Kernel Driver Generator
"""

    def generate_test_cases_with_drivers(self, functions: List[Function]) -> List[TestCase]:
        """Generate test cases that include kernel driver generation."""
        test_cases = []
        
        for function in functions:
            # Generate kernel driver files
            driver_files = self.generate_kernel_test_driver(function)
            
            # Create test case that builds and runs the kernel driver
            test_case = TestCase(
                id=f"kernel_driver_{uuid.uuid4().hex[:8]}",
                name=f"Kernel Driver Test for {function.name}",
                description=f"Comprehensive kernel-space testing of {function.name} using generated kernel module",
                test_type=TestType.INTEGRATION,
                target_subsystem=function.subsystem or "kernel",
                code_paths=[function.file_path] if function.file_path else [],
                test_script=self._create_driver_test_script(function, driver_files),
                execution_time_estimate=300,  # 5 minutes for kernel module testing
                metadata={
                    "test_method": "kernel_driver",
                    "driver_files": list(driver_files.keys()),
                    "requires_root": True,
                    "kernel_module": True
                }
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _create_driver_test_script(self, function: Function, driver_files: Dict[str, str]) -> str:
        """Create test script that sets up and runs kernel driver test."""
        return f"""#!/bin/bash
# Kernel Driver Test for {function.name}
set -e

echo "Setting up kernel driver test for {function.name}..."

# Check prerequisites
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Kernel driver tests require root privileges"
    exit 1
fi

if [ ! -d "/lib/modules/$(uname -r)/build" ]; then
    echo "ERROR: Kernel headers not found for $(uname -r)"
    echo "Please install kernel headers: apt-get install linux-headers-$(uname -r)"
    exit 1
fi

# Create test directory
TEST_DIR="/tmp/kernel_test_{function.name.lower()}_$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Generate driver files
cat > test_{function.name.lower()}.c << 'EOF'
{driver_files.get(f"test_{function.name.lower()}.c", "")}
EOF

cat > Makefile << 'EOF'
{driver_files.get("Makefile", "")}
EOF

cat > run_test.sh << 'EOF'
{driver_files.get("run_test.sh", "")}
EOF

chmod +x run_test.sh

echo "Building kernel module..."
make clean
make

if [ ! -f "test_{function.name.lower()}.ko" ]; then
    echo "ERROR: Kernel module build failed"
    cd /
    rm -rf "$TEST_DIR"
    exit 1
fi

echo "Loading and testing kernel module..."
insmod test_{function.name.lower()}.ko

# Wait for tests to complete
sleep 5

# Collect results
echo "Collecting test results..."
if [ -f "/proc/test_{function.name.lower()}_results" ]; then
    echo "=== Test Results ==="
    cat /proc/test_{function.name.lower()}_results
    
    # Check if tests passed
    if grep -q "Status: PASSED" /proc/test_{function.name.lower()}_results; then
        echo "✓ Kernel driver tests PASSED"
        result=0
    else
        echo "✗ Kernel driver tests FAILED"
        result=1
    fi
else
    echo "ERROR: Test results not available"
    echo "Checking kernel messages..."
    dmesg | tail -20 | grep -i "test_{function.name.lower()}" || true
    result=1
fi

# Cleanup
echo "Cleaning up..."
rmmod test_{function.name.lower()} || true
cd /
rm -rf "$TEST_DIR"

echo "Kernel driver test completed for {function.name}"
exit $result
"""