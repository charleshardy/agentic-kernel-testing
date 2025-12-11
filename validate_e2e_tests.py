#!/usr/bin/env python3
"""Validation script for end-to-end integration tests.

This script validates that all end-to-end integration tests can be imported
and their basic structure is correct.
"""

import sys
import importlib
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def validate_test_imports():
    """Validate that all test modules can be imported."""
    test_modules = [
        'tests.integration.test_end_to_end_workflows',
        'tests.integration.test_system_workflows',
        'tests.integration.test_runner_e2e',
        'tests.fixtures.end_to_end_fixtures'
    ]
    
    print("Validating test module imports...")
    
    for module_name in test_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ {module_name}")
            
            # Check for test classes
            if hasattr(module, '__dict__'):
                test_classes = [
                    name for name, obj in module.__dict__.items()
                    if name.startswith('Test') and hasattr(obj, '__dict__')
                ]
                if test_classes:
                    print(f"  Test classes: {', '.join(test_classes)}")
                
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            return False
        except Exception as e:
            print(f"✗ {module_name}: Unexpected error: {e}")
            return False
    
    return True


def validate_fixtures():
    """Validate that fixtures are properly defined."""
    print("\nValidating test fixtures...")
    
    try:
        from tests.fixtures.end_to_end_fixtures import (
            comprehensive_test_environments,
            comprehensive_test_cases,
            sample_test_results,
            sample_code_analyses,
            sample_failure_analyses,
            mock_vcs_events,
            performance_baselines,
            security_vulnerability_patterns
        )
        
        fixtures = [
            'comprehensive_test_environments',
            'comprehensive_test_cases', 
            'sample_test_results',
            'sample_code_analyses',
            'sample_failure_analyses',
            'mock_vcs_events',
            'performance_baselines',
            'security_vulnerability_patterns'
        ]
        
        for fixture_name in fixtures:
            print(f"✓ {fixture_name}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Fixture import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Fixture validation failed: {e}")
        return False


def validate_test_structure():
    """Validate test class and method structure."""
    print("\nValidating test structure...")
    
    try:
        from tests.integration.test_end_to_end_workflows import (
            TestEndToEndWorkflows,
            TestSystemIntegration
        )
        from tests.integration.test_system_workflows import (
            TestCodeAnalysisWorkflow,
            TestTestExecutionWorkflow,
            TestAnalysisWorkflow,
            TestNotificationWorkflow
        )
        
        test_classes = [
            TestEndToEndWorkflows,
            TestSystemIntegration,
            TestCodeAnalysisWorkflow,
            TestTestExecutionWorkflow,
            TestAnalysisWorkflow,
            TestNotificationWorkflow
        ]
        
        for test_class in test_classes:
            class_name = test_class.__name__
            test_methods = [
                method for method in dir(test_class)
                if method.startswith('test_') and callable(getattr(test_class, method))
            ]
            
            if test_methods:
                print(f"✓ {class_name}: {len(test_methods)} test methods")
            else:
                print(f"✗ {class_name}: No test methods found")
                return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Test class import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test structure validation failed: {e}")
        return False


def validate_dependencies():
    """Validate that required dependencies are available."""
    print("\nValidating dependencies...")
    
    required_modules = [
        'pytest',
        'ai_generator.models',
        'ai_generator.test_generator',
        'orchestrator.scheduler',
        'execution.test_runner',
        'analysis.coverage_analyzer',
        'analysis.root_cause_analyzer',
        'integration.vcs_integration',
        'integration.notification_service'
    ]
    
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            return False
    
    return True


def main():
    """Main validation function."""
    print("End-to-End Integration Test Validation")
    print("=" * 50)
    
    validations = [
        ("Test Imports", validate_test_imports),
        ("Test Fixtures", validate_fixtures),
        ("Test Structure", validate_test_structure),
        ("Dependencies", validate_dependencies)
    ]
    
    all_passed = True
    
    for validation_name, validation_func in validations:
        try:
            if not validation_func():
                all_passed = False
                print(f"\n❌ {validation_name} validation failed")
            else:
                print(f"\n✅ {validation_name} validation passed")
        except Exception as e:
            all_passed = False
            print(f"\n❌ {validation_name} validation error: {e}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All validations passed! End-to-end tests are ready to run.")
        print("\nTo run the tests:")
        print("  python tests/integration/test_runner_e2e.py")
        print("  pytest tests/integration/ -v")
        return 0
    else:
        print("❌ Some validations failed. Please fix the issues before running tests.")
        return 1


if __name__ == '__main__':
    sys.exit(main())