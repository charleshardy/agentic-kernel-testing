#!/usr/bin/env python3
"""Verify Task 21 implementation is complete."""

import sys
import subprocess

def run_test(description, command):
    """Run a test command and report results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print('='*60)
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ PASSED")
        return True
    else:
        print(f"❌ FAILED")
        print(result.stdout)
        print(result.stderr)
        return False

def main():
    """Run all verification tests."""
    print("\n" + "="*60)
    print("Task 21: VCS Integration - Verification")
    print("="*60)
    
    tests = [
        ("Import all VCS modules", "python3 -c 'from integration import VCSIntegration, VCSProvider, EventType, Repository, TestStatus, StatusReport, WebhookParser, VCSClient'"),
        ("Run VCS trigger responsiveness tests", "python3 -m pytest tests/property/test_vcs_trigger_responsiveness.py -v --tb=short -q"),
        ("Run VCS result reporting tests", "python3 -m pytest tests/property/test_vcs_result_reporting.py -v --tb=short -q"),
        ("Run VCS integration example", "python3 examples/vcs_integration_example.py"),
    ]
    
    results = []
    for description, command in tests:
        results.append(run_test(description, command))
    
    print("\n" + "="*60)
    print("Verification Summary")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ Task 21 implementation is COMPLETE and VERIFIED")
        print("\nImplemented:")
        print("  ✓ VCS data models with serialization")
        print("  ✓ Webhook parser for GitHub/GitLab")
        print("  ✓ VCS client for status reporting")
        print("  ✓ VCS integration handler")
        print("  ✓ Property test: VCS trigger responsiveness (5 tests)")
        print("  ✓ Property test: Result reporting completeness (6 tests)")
        print("  ✓ Example usage demonstration")
        print("\nRequirements validated:")
        print("  ✓ 5.1: VCS trigger responsiveness")
        print("  ✓ 5.2: Result reporting completeness")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
