#!/usr/bin/env python3
"""Verification script for Task 24: Coverage Analyzer Implementation."""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✓ {description} PASSED")
            return True
        else:
            print(f"✗ {description} FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ {description} TIMED OUT")
        return False
    except Exception as e:
        print(f"✗ {description} ERROR: {e}")
        return False

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Task 24: Coverage Analyzer - Verification")
    print("=" * 60)
    
    tests = [
        ("Import coverage analyzer modules", 
         "python3 -c 'from analysis.coverage_analyzer import CoverageAnalyzer, LcovParser, CoverageMerger, CoverageCollector, FileCoverage'"),
        
        ("Import coverage data model", 
         "python3 -c 'from ai_generator.models import CoverageData'"),
        
        ("Run basic coverage tests", 
         "python3 test_coverage_direct.py"),
        
        ("Run property-based tests for coverage metric completeness", 
         "python3 -m pytest tests/property/test_coverage_metric_completeness.py -v --tb=short -q"),
    ]
    
    passed = 0
    failed = 0
    
    for description, cmd in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Verification Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ Task 24: Coverage Analyzer - COMPLETE")
        print("✓ All components implemented:")
        print("  - gcov/lcov integration for coverage collection")
        print("  - Coverage data parser and merger")
        print("  - Line, branch, and function coverage calculation")
        print("  - Coverage data storage and retrieval")
        print("\n✓ Property 26: Coverage metric completeness - VERIFIED")
        print("  Requirements 6.1 validated")
        return 0
    else:
        print(f"\n✗ {failed} verification test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
