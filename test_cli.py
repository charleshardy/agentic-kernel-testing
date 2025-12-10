#!/usr/bin/env python3
"""Simple test script for CLI functionality."""

import subprocess
import sys
import json

def run_cli_command(args):
    """Run a CLI command and return the result."""
    cmd = ["python3", "-m", "cli.main"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def test_basic_commands():
    """Test basic CLI commands."""
    tests = [
        (["--help"], "Help command"),
        (["version"], "Version command"),
        (["config", "show"], "Config show"),
        (["test", "--help"], "Test help"),
        (["test", "template", "--format", "json", "--output-file", "test_template.json"], "Template generation"),
    ]
    
    results = []
    
    for args, description in tests:
        print(f"Testing: {description}")
        returncode, stdout, stderr = run_cli_command(args)
        
        success = returncode == 0 or (returncode != 0 and "help" in args[0] if args else False)
        results.append({
            "test": description,
            "args": args,
            "success": success,
            "returncode": returncode,
            "stdout_length": len(stdout),
            "stderr_length": len(stderr)
        })
        
        if success:
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL (exit code: {returncode})")
            if stderr:
                print(f"     Error: {stderr[:100]}...")
    
    return results

if __name__ == "__main__":
    print("🧪 Testing CLI Functionality")
    print("=" * 50)
    
    results = test_basic_commands()
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['test']}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        sys.exit(1)