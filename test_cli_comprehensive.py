#!/usr/bin/env python3
"""Comprehensive CLI functionality test."""

import subprocess
import sys
import json
import tempfile
import os
from pathlib import Path

def run_cli_command(args, input_text=None):
    """Run a CLI command and return the result."""
    cmd = ["python3", "-m", "cli.main"] + args
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30,
            input=input_text
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_template_generation():
    """Test template generation in different formats."""
    print("🧪 Testing template generation...")
    
    tests = [
        (["test", "template", "--format", "yaml"], "YAML template"),
        (["test", "template", "--format", "json"], "JSON template"),
    ]
    
    results = []
    
    for args, description in tests:
        print(f"  Testing: {description}")
        returncode, stdout, stderr = run_cli_command(args)
        
        success = returncode == 0 and "Template saved" in stdout
        results.append({
            "test": description,
            "success": success,
            "details": f"Exit code: {returncode}"
        })
        
        if success:
            print(f"    ✅ PASS")
        else:
            print(f"    ❌ FAIL - {stderr[:100] if stderr else 'No error message'}")
    
    return results

def test_configuration_commands():
    """Test configuration management commands."""
    print("🧪 Testing configuration commands...")
    
    tests = [
        (["config", "show"], "Show configuration"),
        (["config", "validate"], "Validate configuration"),
        (["config", "get", "llm.provider"], "Get specific config value"),
    ]
    
    results = []
    
    for args, description in tests:
        print(f"  Testing: {description}")
        returncode, stdout, stderr = run_cli_command(args)
        
        # Configuration commands should work even without API server
        success = returncode == 0 or "Configuration" in stdout
        results.append({
            "test": description,
            "success": success,
            "details": f"Exit code: {returncode}"
        })
        
        if success:
            print(f"    ✅ PASS")
        else:
            print(f"    ❌ FAIL - {stderr[:100] if stderr else 'No error message'}")
    
    return results

def test_help_commands():
    """Test help functionality for all command groups."""
    print("🧪 Testing help commands...")
    
    command_groups = [
        "test", "status", "results", "env", "config"
    ]
    
    results = []
    
    for group in command_groups:
        print(f"  Testing: {group} --help")
        returncode, stdout, stderr = run_cli_command([group, "--help"])
        
        success = returncode == 0 and "Usage:" in stdout
        results.append({
            "test": f"{group} help",
            "success": success,
            "details": f"Exit code: {returncode}"
        })
        
        if success:
            print(f"    ✅ PASS")
        else:
            print(f"    ❌ FAIL - {stderr[:100] if stderr else 'No error message'}")
    
    return results

def test_dry_run_functionality():
    """Test dry-run functionality."""
    print("🧪 Testing dry-run functionality...")
    
    # Create a temporary test script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write("#!/bin/bash\necho 'Test script'\nexit 0\n")
        script_path = f.name
    
    try:
        os.chmod(script_path, 0o755)
        
        tests = [
            ([
                "test", "submit",
                "--name", "Dry Run Test",
                "--description", "Testing dry run functionality",
                "--type", "unit",
                "--subsystem", "mm",
                "--script-file", script_path,
                "--dry-run"
            ], "Test submit dry-run"),
        ]
        
        results = []
        
        for args, description in tests:
            print(f"  Testing: {description}")
            returncode, stdout, stderr = run_cli_command(args)
            
            success = returncode == 0 and "Would submit test case:" in stdout
            results.append({
                "test": description,
                "success": success,
                "details": f"Exit code: {returncode}"
            })
            
            if success:
                print(f"    ✅ PASS")
            else:
                print(f"    ❌ FAIL - {stderr[:100] if stderr else 'No error message'}")
        
        return results
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(script_path)
        except:
            pass

def test_batch_submission():
    """Test batch test submission with config file."""
    print("🧪 Testing batch submission...")
    
    # Create a test configuration file
    test_config = {
        "tests": [
            {
                "name": "Batch Test 1",
                "description": "First batch test",
                "test_type": "unit",
                "target_subsystem": "mm",
                "test_script": "echo 'Test 1'",
                "priority": 5
            },
            {
                "name": "Batch Test 2", 
                "description": "Second batch test",
                "test_type": "integration",
                "target_subsystem": "net",
                "test_script": "echo 'Test 2'",
                "priority": 3
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f, indent=2)
        config_path = f.name
    
    try:
        tests = [
            ([
                "test", "submit-batch",
                "--config-file", config_path,
                "--dry-run"
            ], "Batch submit dry-run"),
        ]
        
        results = []
        
        for args, description in tests:
            print(f"  Testing: {description}")
            returncode, stdout, stderr = run_cli_command(args)
            
            success = returncode == 0 and "Would submit" in stdout and "test cases:" in stdout
            results.append({
                "test": description,
                "success": success,
                "details": f"Exit code: {returncode}"
            })
            
            if success:
                print(f"    ✅ PASS")
            else:
                print(f"    ❌ FAIL - {stderr[:100] if stderr else 'No error message'}")
        
        return results
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(config_path)
        except:
            pass

def test_api_dependent_commands():
    """Test commands that require API server (should fail gracefully)."""
    print("🧪 Testing API-dependent commands (should fail gracefully)...")
    
    tests = [
        (["health"], "Health check"),
        (["test", "list"], "List tests"),
        (["status", "active"], "Active status"),
        (["results", "summary"], "Results summary"),
        (["env", "list"], "List environments"),
    ]
    
    results = []
    
    for args, description in tests:
        print(f"  Testing: {description}")
        returncode, stdout, stderr = run_cli_command(args)
        
        # These should fail gracefully with a clear error message
        success = (returncode != 0 and 
                  ("API Error" in stderr or "Error" in stderr or 
                   "unavailable" in stdout or "Could not connect" in stdout))
        
        results.append({
            "test": description,
            "success": success,
            "details": f"Exit code: {returncode}, graceful failure: {success}"
        })
        
        if success:
            print(f"    ✅ PASS (graceful failure)")
        else:
            print(f"    ❌ FAIL - Should fail gracefully")
    
    return results

def main():
    """Run comprehensive CLI tests."""
    print("🚀 Comprehensive CLI Testing")
    print("=" * 60)
    
    all_results = []
    
    # Run all test suites
    test_suites = [
        test_help_commands,
        test_template_generation,
        test_configuration_commands,
        test_dry_run_functionality,
        test_batch_submission,
        test_api_dependent_commands,
    ]
    
    for test_suite in test_suites:
        try:
            results = test_suite()
            all_results.extend(results)
            print()
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            all_results.append({
                "test": test_suite.__name__,
                "success": False,
                "details": str(e)
            })
    
    # Summary
    print("📊 Test Summary")
    print("=" * 40)
    
    passed = sum(1 for r in all_results if r["success"])
    total = len(all_results)
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    print("\nDetailed Results:")
    print("-" * 30)
    
    for result in all_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}")
        if not result["success"]:
            print(f"   Details: {result['details']}")
    
    if passed >= total * 0.8:  # 80% pass rate
        print("\n🎉 CLI testing completed successfully!")
        return 0
    else:
        print(f"\n⚠️  CLI testing completed with issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())