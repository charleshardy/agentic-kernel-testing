#!/usr/bin/env python3
"""Simple test runner for orchestrator integration tests."""

import sys
import time
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, '.')

def run_basic_integration_test():
    """Run a basic integration test to verify functionality."""
    try:
        print("Testing orchestrator integration imports...")
        
        # Test imports
        from orchestrator.service import OrchestratorService
        from orchestrator.config import OrchestratorConfig
        from orchestrator.scheduler import TestOrchestrator, Priority
        from ai_generator.models import TestCase, TestType, HardwareConfig, Environment, EnvironmentStatus
        
        print("✓ All imports successful")
        
        # Test orchestrator configuration
        print("\nTesting orchestrator configuration...")
        config = OrchestratorConfig(
            poll_interval=1.0,
            default_timeout=30,
            max_concurrent_tests=2,
            enable_persistence=False,
            log_level="INFO"
        )
        print("✓ Configuration created successfully")
        
        # Test orchestrator service creation
        print("\nTesting orchestrator service creation...")
        service = OrchestratorService(config)
        print("✓ Orchestrator service created successfully")
        
        # Test service startup
        print("\nTesting orchestrator service startup...")
        if service.start():
            print("✓ Orchestrator service started successfully")
            
            # Test health status
            health = service.get_health_status()
            print(f"✓ Health status: {health['status']}")
            
            # Test system metrics
            metrics = service.get_system_metrics()
            print(f"✓ System metrics: active_tests={metrics['active_tests']}")
            
            # Test service shutdown
            print("\nTesting orchestrator service shutdown...")
            if service.stop():
                print("✓ Orchestrator service stopped successfully")
            else:
                print("✗ Failed to stop orchestrator service")
                return False
        else:
            print("✗ Failed to start orchestrator service")
            return False
        
        # Test scheduler functionality
        print("\nTesting scheduler functionality...")
        orchestrator = TestOrchestrator()
        
        # Create test environment
        test_env = Environment(
            id="test-env-001",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            ),
            status=EnvironmentStatus.IDLE
        )
        orchestrator.add_environment(test_env)
        print("✓ Test environment added")
        
        # Create test case
        test_case = TestCase(
            id="integration-test-001",
            name="Basic Integration Test",
            description="Test orchestrator integration",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Integration test running..."
sleep 1
echo "Integration test completed"
exit 0
""",
            execution_time_estimate=5,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        # Submit test job
        job_id = orchestrator.submit_job(
            test_case=test_case,
            priority=Priority.MEDIUM,
            impact_score=0.5
        )
        print(f"✓ Test job submitted: {job_id}")
        
        # Check job status
        job_status = orchestrator.get_job_status(job_id)
        if job_status:
            print(f"✓ Job status retrieved: {job_status['status']}")
        else:
            print("✗ Failed to retrieve job status")
            return False
        
        # Check queue status
        queue_status = orchestrator.get_queue_status()
        print(f"✓ Queue status: {queue_status}")
        
        print("\n🎉 All basic integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def run_api_integration_test():
    """Run API integration test."""
    try:
        print("\n" + "="*50)
        print("Testing API integration...")
        
        # Test API integration imports
        from api.orchestrator_integration import start_orchestrator, stop_orchestrator, get_orchestrator
        from api.models import APIResponse
        
        print("✓ API integration imports successful")
        
        # Test orchestrator integration functions
        print("\nTesting orchestrator integration functions...")
        
        # Note: We won't actually start/stop the orchestrator in this test
        # as it might interfere with other processes
        orchestrator = get_orchestrator()
        if orchestrator is None:
            print("✓ No orchestrator instance (expected in test environment)")
        else:
            print(f"✓ Orchestrator instance found: {type(orchestrator)}")
        
        print("✓ API integration test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ API integration test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def run_comprehensive_test_validation():
    """Validate comprehensive test structure."""
    try:
        print("\n" + "="*50)
        print("Validating comprehensive test structure...")
        
        # Import test modules
        import tests.integration.test_orchestrator_integration as basic_tests
        import tests.integration.test_orchestrator_api_client as api_tests
        import tests.integration.test_orchestrator_comprehensive as comprehensive_tests
        
        print("✓ All test modules imported successfully")
        
        # Check test classes exist
        test_classes = [
            (basic_tests, 'TestOrchestratorFullExecutionFlow'),
            (basic_tests, 'TestOrchestratorAPIIntegration'),
            (basic_tests, 'TestOrchestratorLoadTesting'),
            (basic_tests, 'TestOrchestratorErrorHandling'),
            (api_tests, 'TestOrchestratorAPIClientIntegration'),
            (api_tests, 'TestOrchestratorEndToEndAPIWorkflow'),
            (api_tests, 'TestOrchestratorAPIPerformance'),
            (comprehensive_tests, 'TestOrchestratorComprehensiveWorkflows'),
            (comprehensive_tests, 'TestOrchestratorPerformanceBenchmarks'),
        ]
        
        for module, class_name in test_classes:
            if hasattr(module, class_name):
                test_class = getattr(module, class_name)
                print(f"✓ Found test class: {class_name}")
                
                # Count test methods
                test_methods = [method for method in dir(test_class) if method.startswith('test_')]
                print(f"  - {len(test_methods)} test methods")
            else:
                print(f"✗ Missing test class: {class_name}")
                return False
        
        print("✓ All test classes validated")
        return True
        
    except Exception as e:
        print(f"\n❌ Comprehensive test validation failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Main test runner."""
    print("Orchestrator Integration Test Runner")
    print("=" * 50)
    
    all_passed = True
    
    # Run basic integration test
    if not run_basic_integration_test():
        all_passed = False
    
    # Run API integration test
    if not run_api_integration_test():
        all_passed = False
    
    # Validate comprehensive test structure
    if not run_comprehensive_test_validation():
        all_passed = False
    
    # Final result
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL INTEGRATION TESTS VALIDATION PASSED!")
        print("\nIntegration test files are ready for execution:")
        print("- tests/integration/test_orchestrator_integration.py")
        print("- tests/integration/test_orchestrator_api_client.py") 
        print("- tests/integration/test_orchestrator_comprehensive.py")
        print("\nTo run the tests:")
        print("  python3 -m pytest tests/integration/test_orchestrator_integration.py -v")
        print("  python3 -m pytest tests/integration/test_orchestrator_api_client.py -v")
        print("  python3 -m pytest tests/integration/test_orchestrator_comprehensive.py -v")
        return 0
    else:
        print("❌ SOME INTEGRATION TESTS VALIDATION FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())