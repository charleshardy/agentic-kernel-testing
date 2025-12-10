#!/usr/bin/env python3
"""Comprehensive demonstration of the Agentic AI Testing System API."""

import sys
import time
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.client import AgenticTestingClient, TestCase, APIError


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('api_demo.log')
        ]
    )


def create_sample_test_cases() -> List[TestCase]:
    """Create sample test cases for demonstration."""
    return [
        TestCase(
            name="Network Driver Unit Test",
            description="Test Intel e1000e network driver basic functionality",
            test_type="unit",
            target_subsystem="networking",
            code_paths=["drivers/net/ethernet/intel/e1000e/"],
            test_script="""#!/bin/bash
# Test e1000e driver loading and basic operations
set -e

echo "Testing e1000e network driver..."

# Load the driver
modprobe e1000e || {
    echo "Failed to load e1000e driver"
    exit 1
}

# Check if driver is loaded
lsmod | grep e1000e || {
    echo "e1000e driver not found in loaded modules"
    exit 1
}

# Check network interfaces
ip link show | grep -E "(eth|ens|enp)" || {
    echo "No ethernet interfaces found"
    exit 1
}

# Test basic network operations
ping -c 3 127.0.0.1 || {
    echo "Basic network connectivity test failed"
    exit 1
}

echo "e1000e driver test completed successfully"
""",
            execution_time_estimate=180,
            required_hardware={
                "architecture": "x86_64",
                "cpu_model": "Intel Xeon E5-2686 v4",
                "memory_mb": 4096,
                "storage_type": "ssd",
                "is_virtual": True,
                "emulator": "qemu"
            },
            metadata={
                "test_category": "driver_validation",
                "kernel_modules": ["e1000e"],
                "expected_interfaces": ["eth0", "ens3"]
            },
            priority=7
        ),
        
        TestCase(
            name="Memory Management Stress Test",
            description="Comprehensive memory allocation and deallocation stress test",
            test_type="performance",
            target_subsystem="memory_management",
            code_paths=["mm/", "include/linux/mm.h"],
            test_script="""#!/bin/bash
# Memory stress test with various allocation patterns
set -e

echo "Starting memory management stress test..."

# Check initial memory state
free -h
echo "Initial memory state recorded"

# Test 1: Large allocation stress
echo "Test 1: Large allocation stress"
stress-ng --vm 2 --vm-bytes 1G --timeout 60s --metrics-brief || {
    echo "Large allocation stress test failed"
    exit 1
}

# Test 2: Small allocation stress
echo "Test 2: Small allocation stress"  
stress-ng --vm 4 --vm-bytes 256M --timeout 60s --metrics-brief || {
    echo "Small allocation stress test failed"
    exit 1
}

# Test 3: Memory fragmentation test
echo "Test 3: Memory fragmentation test"
for i in {1..10}; do
    stress-ng --vm 1 --vm-bytes 512M --timeout 10s --quiet &
    sleep 1
done
wait

# Check final memory state
free -h
echo "Memory stress test completed successfully"
""",
            execution_time_estimate=300,
            required_hardware={
                "architecture": "x86_64",
                "cpu_model": "Intel Xeon",
                "memory_mb": 8192,
                "storage_type": "ssd",
                "is_virtual": True,
                "emulator": "qemu"
            },
            metadata={
                "test_category": "performance_validation",
                "stress_tools": ["stress-ng"],
                "memory_patterns": ["large_alloc", "small_alloc", "fragmentation"]
            },
            priority=5
        ),
        
        TestCase(
            name="ARM64 Boot Validation",
            description="Validate kernel boot process on ARM64 architecture",
            test_type="integration",
            target_subsystem="boot",
            code_paths=["arch/arm64/", "init/"],
            test_script="""#!/bin/bash
# ARM64 boot validation test
set -e

echo "ARM64 boot validation test starting..."

# Check architecture
uname -m | grep -E "(aarch64|arm64)" || {
    echo "Not running on ARM64 architecture"
    exit 1
}

# Check kernel boot messages
dmesg | grep -i "booting linux" || {
    echo "Boot messages not found in dmesg"
    exit 1
}

# Check essential subsystems
echo "Checking essential subsystems..."

# Check CPU initialization
dmesg | grep -i "cpu.*online" || {
    echo "CPU initialization messages not found"
    exit 1
}

# Check memory initialization
dmesg | grep -i "memory.*available" || {
    echo "Memory initialization messages not found"
    exit 1
}

# Check device tree
ls /proc/device-tree/ > /dev/null || {
    echo "Device tree not accessible"
    exit 1
}

# Check ARM64 specific features
cat /proc/cpuinfo | grep -E "(Features|CPU architecture)" || {
    echo "ARM64 CPU features not found"
    exit 1
}

echo "ARM64 boot validation completed successfully"
""",
            execution_time_estimate=120,
            required_hardware={
                "architecture": "arm64",
                "cpu_model": "ARM Cortex-A72",
                "memory_mb": 4096,
                "storage_type": "ssd",
                "is_virtual": True,
                "emulator": "qemu"
            },
            metadata={
                "test_category": "architecture_validation",
                "architecture": "arm64",
                "boot_components": ["cpu_init", "memory_init", "device_tree"]
            },
            priority=8
        )
    ]


def demonstrate_full_workflow():
    """Demonstrate the complete API workflow."""
    logger = logging.getLogger(__name__)
    
    print("🚀 Comprehensive Agentic AI Testing System API Demo")
    print("=" * 60)
    
    try:
        # Initialize client
        with AgenticTestingClient() as client:
            
            # 1. Health check and system info
            print("\n📊 1. System Health Check")
            print("-" * 30)
            
            health = client.health_check()
            print(f"   System Status: {health['status']}")
            print(f"   API Version: {health['version']}")
            print(f"   Uptime: {health['uptime']:.1f} seconds")
            
            metrics = client.get_system_metrics()
            print(f"   CPU Usage: {metrics['system']['cpu_usage_percent']:.1f}%")
            print(f"   Memory Usage: {metrics['system']['memory_usage_percent']:.1f}%")
            print(f"   Active Tests: {metrics['testing']['active_tests']}")
            
            # 2. Authentication
            print("\n🔐 2. Authentication")
            print("-" * 20)
            
            login_result = client.login("admin", "admin123")
            print(f"   ✓ Logged in as: {login_result['user_info']['username']}")
            print(f"   Permissions: {', '.join(login_result['user_info']['permissions'])}")
            
            user_info = client.get_current_user()
            print(f"   User ID: {user_info['user']['user_id']}")
            print(f"   Email: {user_info['user']['email']}")
            
            # 3. Environment Management
            print("\n🖥️  3. Environment Management")
            print("-" * 30)
            
            environments = client.list_environments()
            print(f"   Available Environments: {len(environments['environments'])}")
            
            env_stats = client.get_environment_stats()
            print(f"   Total: {env_stats['environment_counts']['total']}")
            print(f"   Idle: {env_stats['environment_counts']['idle']}")
            print(f"   Busy: {env_stats['environment_counts']['busy']}")
            print(f"   Utilization: {env_stats['capacity_info']['capacity_utilization']:.1%}")
            
            # Show environment details
            for env in environments['environments'][:2]:  # Show first 2
                print(f"   - {env['id']}: {env['architecture']} ({env['status']})")
            
            # 4. Code Analysis
            print("\n🔍 4. Code Analysis")
            print("-" * 20)
            
            analysis = client.analyze_code(
                repository_url="https://github.com/torvalds/linux.git",
                commit_sha="v6.1-rc1",
                branch="master"
            )
            
            print(f"   Analysis ID: {analysis['analysis_id']}")
            print(f"   Commit SHA: {analysis['commit_sha']}")
            print(f"   Impact Score: {analysis['impact_score']:.2f}")
            print(f"   Risk Level: {analysis['risk_level']}")
            print(f"   Affected Subsystems: {', '.join(analysis['affected_subsystems'])}")
            print(f"   Suggested Test Types: {', '.join(analysis['suggested_test_types'])}")
            
            # 5. Test Submission
            print("\n📝 5. Test Submission")
            print("-" * 20)
            
            test_cases = create_sample_test_cases()
            print(f"   Created {len(test_cases)} test cases")
            
            submission = client.submit_tests(
                test_cases=test_cases,
                priority=6,
                webhook_url="https://example.com/webhook"
            )
            
            submission_id = submission["submission_id"]
            plan_id = submission["execution_plan_id"]
            test_ids = submission["test_case_ids"]
            
            print(f"   ✓ Submitted {len(test_ids)} tests")
            print(f"   Submission ID: {submission_id}")
            print(f"   Execution Plan: {plan_id}")
            print(f"   Estimated Completion: {submission['estimated_completion_time']}")
            
            # 6. Status Monitoring
            print("\n⏱️  6. Status Monitoring")
            print("-" * 25)
            
            # Get execution plan status
            plan_status = client.get_execution_plan_status(plan_id)
            print(f"   Plan Status: {plan_status['overall_status']}")
            print(f"   Progress: {plan_status['progress']:.1%}")
            print(f"   Tests: {plan_status['completed_tests']}/{plan_status['total_tests']}")
            
            # Monitor individual test statuses
            print("   Individual Test Status:")
            for test_status in plan_status['test_statuses'][:3]:  # Show first 3
                print(f"   - {test_status['test_id']}: {test_status['status']} ({test_status['progress']:.1%})")
            
            # Get active executions
            active = client.get_active_executions()
            print(f"   Active Tests: {len(active['active_tests'])}")
            print(f"   Active Plans: {len(active['active_plans'])}")
            
            # 7. Results Retrieval
            print("\n📊 7. Results Retrieval")
            print("-" * 25)
            
            # List recent results
            results = client.list_test_results(page=1, page_size=5)
            print(f"   Recent Results: {len(results['results'])}")
            print(f"   Total Results: {results['pagination']['total_items']}")
            
            # Show summary statistics
            summary = results.get('summary', {})
            if summary:
                print(f"   Pass Rate: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)}")
                print(f"   Avg Execution Time: {summary.get('avg_execution_time', 0):.1f}s")
            
            # Get detailed results for available tests
            for result in results['results'][:2]:  # Show first 2
                test_id = result['test_id']
                print(f"   - {test_id}: {result['status']} ({result['execution_time']:.1f}s)")
                
                try:
                    detailed_result = client.get_test_result(test_id)
                    print(f"     Environment: {detailed_result['environment']['id']}")
                    print(f"     Architecture: {detailed_result['environment']['architecture']}")
                    
                    # Get coverage if available
                    if detailed_result.get('coverage_data'):
                        coverage = client.get_coverage_report(test_id)
                        print(f"     Coverage: {coverage['line_coverage']:.1%} lines, {coverage['branch_coverage']:.1%} branches")
                    
                    # Get failure analysis if test failed
                    if result['status'] == 'failed':
                        try:
                            failure = client.get_failure_analysis(test_id)
                            print(f"     Root Cause: {failure['root_cause']}")
                            print(f"     Confidence: {failure['confidence']:.1%}")
                        except APIError:
                            print("     No failure analysis available")
                            
                except APIError as e:
                    print(f"     Error getting details: {e}")
            
            # 8. Results Summary and Export
            print("\n📈 8. Results Summary & Export")
            print("-" * 35)
            
            summary = client.get_results_summary(days=7)
            print(f"   Last 7 Days Summary:")
            print(f"   - Total Tests: {summary['total_tests']}")
            print(f"   - Pass Rate: {summary['pass_rate']:.1%}")
            print(f"   - Avg Duration: {summary['avg_execution_time_seconds']:.1f}s")
            
            # Architecture breakdown
            arch_breakdown = summary.get('architecture_breakdown', {})
            if arch_breakdown:
                print("   Architecture Breakdown:")
                for arch, stats in arch_breakdown.items():
                    print(f"   - {arch}: {stats['passed']}/{stats['total']} passed")
            
            # Export results (demonstration)
            print("   Exporting results...")
            try:
                export_data = client.export_results(
                    format="json",
                    start_date=(datetime.now() - timedelta(days=7)).isoformat(),
                    end_date=datetime.now().isoformat()
                )
                print(f"   ✓ Exported {len(export_data)} bytes of results data")
            except APIError as e:
                print(f"   Export failed: {e}")
            
            # 9. Advanced Features
            print("\n🔧 9. Advanced Features")
            print("-" * 25)
            
            # Create API key for programmatic access
            try:
                api_key = client.create_api_key("Demo API Key")
                print(f"   ✓ Created API key: {api_key[:20]}...")
            except APIError as e:
                print(f"   API key creation failed: {e}")
            
            # Iterate through all results (demonstration of pagination)
            print("   Iterating through all results...")
            result_count = 0
            for result in client.iterate_results(page_size=10):
                result_count += 1
                if result_count >= 5:  # Limit for demo
                    break
            print(f"   ✓ Processed {result_count} results")
            
            # 10. Cleanup and Summary
            print("\n🧹 10. Cleanup & Summary")
            print("-" * 30)
            
            print("   Demo completed successfully!")
            print("   Key achievements:")
            print("   ✓ System health verified")
            print("   ✓ User authenticated")
            print("   ✓ Environments inspected")
            print("   ✓ Code analyzed")
            print("   ✓ Tests submitted")
            print("   ✓ Status monitored")
            print("   ✓ Results retrieved")
            print("   ✓ Data exported")
            
            # Final system state
            final_metrics = client.get_system_metrics()
            print(f"   Final system state:")
            print(f"   - Active tests: {final_metrics['testing']['active_tests']}")
            print(f"   - Queued tests: {final_metrics['testing']['queued_tests']}")
            print(f"   - System load: moderate")
            
    except APIError as e:
        logger.error(f"API Error: {e}")
        if e.status_code == 401:
            print("❌ Authentication failed - check credentials")
        elif e.status_code == 403:
            print("❌ Permission denied - check user permissions")
        else:
            print(f"❌ API Error ({e.status_code}): {e}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n✅ Comprehensive API demonstration completed successfully!")
    return True


def main():
    """Main entry point."""
    setup_logging()
    
    try:
        success = demonstrate_full_workflow()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()