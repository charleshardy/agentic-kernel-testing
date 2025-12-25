import React, { useState } from 'react'
import { Card, Button, Space, Alert, Modal } from 'antd'
import { CodeOutlined, EyeOutlined } from '@ant-design/icons'
import TestCaseModal from '../components/TestCaseModal'
import { EnhancedTestCase } from '../services/api'

const KernelDriverTest: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedTestCase, setSelectedTestCase] = useState<EnhancedTestCase | null>(null)

  // Mock kernel driver test case with the exact structure from the API
  const mockKernelDriverTest: EnhancedTestCase = {
    id: "kernel_driver_test_123",
    name: "Kernel Driver Test for kmalloc",
    description: "Comprehensive kernel-space testing of kmalloc using generated kernel module",
    test_type: "integration",
    target_subsystem: "kernel/mm",
    code_paths: ["mm/slab.c"],
    execution_time_estimate: 300,
    test_script: "#!/bin/bash\n# Kernel Driver Test for kmalloc\necho 'Running kernel driver test...'\n# Test execution logic here",
    created_at: "2025-12-24T05:22:29.267906",
    updated_at: "2025-12-24T05:22:29.267906",
    metadata: {},
    test_metadata: {
      generation_method: "ai_kernel_driver",
      kernel_module: "test_kmalloc.ko",
      requires_root: true,
      requires_kernel_headers: true,
      test_types: ["unit", "integration"],
      driver_files: {
        "test_kmalloc.c": `#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>

#define MODULE_NAME "test_kmalloc"
#define PROC_NAME "test_kmalloc_results"

static struct proc_dir_entry *proc_entry;
static int test_results = 0;
static char test_log[4096];
static int log_pos = 0;

// Test logging function
static void test_log_msg(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    log_pos += vsnprintf(test_log + log_pos, sizeof(test_log) - log_pos, fmt, args);
    va_end(args);
}

// Memory allocation test functions
static int test_memory_allocation_basic(void) {
    void *ptr;
    int i, failures = 0;
    
    test_log_msg("Testing basic memory allocation...\\n");
    
    // Test various allocation sizes
    for (i = 0; i < 100; i++) {
        size_t size = (i % 10 + 1) * 1024; // 1KB to 10KB
        ptr = kmalloc(size, GFP_KERNEL);
        if (!ptr) {
            failures++;
            test_log_msg("Allocation failed for size %zu\\n", size);
            continue;
        }
        
        // Write and verify pattern
        memset(ptr, 0xAA, size);
        if (((char*)ptr)[0] != (char)0xAA || ((char*)ptr)[size-1] != (char)0xAA) {
            failures++;
            test_log_msg("Memory pattern verification failed for size %zu\\n", size);
        }
        
        kfree(ptr);
    }
    
    test_log_msg("Basic allocation test: %d failures out of 100\\n", failures);
    return failures;
}

static int run_all_tests(void) {
    int total_failures = 0;
    
    total_failures += test_memory_allocation_basic();
    
    test_log_msg("\\nTotal test failures: %d\\n", total_failures);
    return total_failures;
}

// Proc file operations
static int test_proc_show(struct seq_file *m, void *v) {
    seq_printf(m, "Test Results for kmalloc:\\n");
    seq_printf(m, "Status: %s\\n", test_results == 0 ? "PASSED" : "FAILED");
    seq_printf(m, "Log:\\n%s\\n", test_log);
    return 0;
}

static int test_proc_open(struct inode *inode, struct file *file) {
    return single_open(file, test_proc_show, NULL);
}

static const struct proc_ops test_proc_ops = {
    .proc_open = test_proc_open,
    .proc_read = seq_read,
    .proc_lseek = seq_lseek,
    .proc_release = single_release,
};

static int __init test_module_init(void) {
    printk(KERN_INFO "Loading test module for kmalloc\\n");
    
    // Create proc entry for results
    proc_entry = proc_create(PROC_NAME, 0644, NULL, &test_proc_ops);
    if (!proc_entry) {
        printk(KERN_ERR "Failed to create proc entry\\n");
        return -ENOMEM;
    }
    
    // Run tests
    test_results = run_all_tests();
    
    printk(KERN_INFO "Test module loaded, results: %s\\n", 
           test_results == 0 ? "PASSED" : "FAILED");
    return 0;
}

static void __exit test_module_exit(void) {
    if (proc_entry) {
        proc_remove(proc_entry);
    }
    printk(KERN_INFO "Test module for kmalloc unloaded\\n");
}

module_init(test_module_init);
module_exit(test_module_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("AI Test Generator");
MODULE_DESCRIPTION("Test driver for kmalloc");
MODULE_VERSION("1.0");`,
        "Makefile": `# Makefile for kmalloc test driver
obj-m := test_kmalloc.o

KERNEL_DIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

all:
\tmake -C $(KERNEL_DIR) M=$(PWD) modules

clean:
\tmake -C $(KERNEL_DIR) M=$(PWD) clean

install: all
\tsudo insmod test_kmalloc.ko

uninstall:
\tsudo rmmod test_kmalloc || true

test: install
\t@echo "Running kernel test for kmalloc..."
\t@sleep 2
\t@cat /proc/test_kmalloc_results || echo "Test results not available"
\t@make uninstall

.PHONY: all clean install uninstall test`,
        "run_test.sh": `#!/bin/bash
# Test script for kmalloc kernel driver

set -e

echo "Building and testing kernel driver for kmalloc..."

# Build the module
make clean
make

if [ ! -f "test_kmalloc.ko" ]; then
    echo "ERROR: Module build failed"
    exit 1
fi

echo "Module built successfully"

# Load the module
echo "Loading test module..."
sudo insmod test_kmalloc.ko

# Wait for tests to complete
sleep 3

# Check results
echo "Test results:"
echo "============="
if [ -f "/proc/test_kmalloc_results" ]; then
    cat /proc/test_kmalloc_results
else
    echo "ERROR: Test results not available"
    dmesg | tail -20 | grep -i "test_kmalloc" || true
fi

# Unload the module
echo "Unloading test module..."
sudo rmmod test_kmalloc || true

echo "Test completed"`,
        "install.sh": `#!/bin/bash
# Installation script for kmalloc kernel test driver

echo "Installing kernel test driver for kmalloc..."

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

if [ -f "test_kmalloc.ko" ]; then
    echo "Module built successfully"
    
    # Copy to modules directory
    cp test_kmalloc.ko /lib/modules/$(uname -r)/extra/
    depmod -a
    
    echo "Module installed successfully"
    echo "Use 'modprobe test_kmalloc' to load"
    echo "Use 'rmmod test_kmalloc' to unload"
else
    echo "ERROR: Module build failed"
    exit 1
fi`,
        "README.md": `# Kernel Test Driver for kmalloc

This is an AI-generated kernel test driver for testing the \`kmalloc\` function.

## Overview

- **Function**: kmalloc
- **Subsystem**: kernel/mm
- **File**: mm/slab.c

## Building

\`\`\`bash
make
\`\`\`

## Testing

\`\`\`bash
# Quick test
make test

# Manual testing
sudo insmod test_kmalloc.ko
cat /proc/test_kmalloc_results
sudo rmmod test_kmalloc
\`\`\`

## Installation

\`\`\`bash
sudo ./install.sh
\`\`\`

## Files

- \`test_kmalloc.c\` - Main kernel module source
- \`Makefile\` - Build configuration
- \`run_test.sh\` - Test execution script
- \`install.sh\` - Installation script

## Test Results

Test results are available in \`/proc/test_kmalloc_results\` while the module is loaded.

## Requirements

- Linux kernel headers for your kernel version
- GCC compiler
- Root privileges for loading/unloading modules

## Generated by

AI Test Generator - Kernel Driver Generator`
      }
    },
    generation_info: {
      method: "ai_kernel_driver",
      source_data: {
        function_name: "kmalloc",
        file_path: "mm/slab.c",
        subsystem: "kernel/mm",
        test_types: ["unit", "integration"]
      },
      generated_at: "2025-12-24T05:22:29.267906",
      ai_model: "kernel_driver_generator"
    },
    requires_root: true,
    kernel_module: true
  }

  const handleViewTest = () => {
    setSelectedTestCase(mockKernelDriverTest)
    setModalVisible(true)
  }

  const handleCloseModal = () => {
    setModalVisible(false)
    setSelectedTestCase(null)
  }

  const handleSaveTest = async (testCase: EnhancedTestCase) => {
    console.log('Test case saved:', testCase)
  }

  return (
    <div style={{ padding: '24px' }}>
      <Alert
        message="Kernel Driver Files Tab Test"
        description="This page tests the Kernel Driver Files tab functionality with a mock kernel driver test case."
        type="info"
        style={{ marginBottom: 24 }}
      />
      
      <Card title="Test Kernel Driver Modal">
        <Space>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            onClick={handleViewTest}
          >
            View Kernel Driver Test Case
          </Button>
          <Button
            icon={<CodeOutlined />}
            onClick={() => window.open('http://localhost:3001/syntax-test', '_blank')}
          >
            Test Syntax Highlighting
          </Button>
        </Space>
        
        <div style={{ marginTop: 16 }}>
          <Alert
            message="Expected Behavior"
            description={
              <div>
                <p>When you click "View Kernel Driver Test Case", you should see:</p>
                <ul>
                  <li>A modal with three tabs: Details, Test Script, and <strong>Kernel Driver Files</strong></li>
                  <li>The Kernel Driver Files tab should show colored syntax highlighting</li>
                  <li>Files should include: test_kmalloc.c, Makefile, run_test.sh, install.sh, README.md</li>
                  <li>Each file should have copy, download, and view buttons</li>
                  <li>Code should be properly highlighted with colors</li>
                </ul>
              </div>
            }
            type="success"
          />
        </div>
      </Card>

      <TestCaseModal
        testCase={selectedTestCase}
        visible={modalVisible}
        mode="view"
        onClose={handleCloseModal}
        onSave={handleSaveTest}
        onModeChange={() => {}}
      />
    </div>
  )
}

export default KernelDriverTest