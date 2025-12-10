#!/usr/bin/env python3
"""CLI Demonstration Script - Showcases the Agentic AI Testing System CLI capabilities."""

import subprocess
import sys
import time
import json

def run_cli_command(args, show_output=True):
    """Run a CLI command and optionally show output."""
    cmd = ["python3", "-m", "cli.main"] + args
    
    if show_output:
        print(f"🔧 Running: agentic-test {' '.join(args)}")
        print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if show_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr and result.returncode != 0:
                print(f"Error: {result.stderr}")
            print()
        
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        if show_output:
            print(f"Error running command: {e}")
            print()
        return -1, "", str(e)

def demo_section(title, description):
    """Print a demo section header."""
    print("=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)
    print(description)
    print()

def main():
    """Run CLI demonstration."""
    print("🚀 Agentic AI Testing System - CLI Demonstration")
    print("=" * 80)
    print("This demo showcases the comprehensive CLI functionality for")
    print("managing kernel and BSP testing workflows.")
    print()
    
    # 1. Basic Information
    demo_section(
        "1. Basic System Information",
        "Check CLI version and system health status"
    )
    
    run_cli_command(["version"])
    run_cli_command(["health"])
    
    # 2. Configuration Management
    demo_section(
        "2. Configuration Management", 
        "View and manage system configuration"
    )
    
    run_cli_command(["config", "show"])
    run_cli_command(["config", "validate"])
    
    # 3. Test Template Generation
    demo_section(
        "3. Test Template Generation",
        "Generate test configuration templates in different formats"
    )
    
    run_cli_command(["test", "template", "--format", "yaml", "--output-file", "demo_template.yaml"])
    run_cli_command(["test", "template", "--format", "json", "--output-file", "demo_template.json"])
    
    # Show generated template content
    print("📄 Generated YAML Template (first 20 lines):")
    print("-" * 40)
    try:
        with open("demo_template.yaml", "r") as f:
            lines = f.readlines()[:20]
            for line in lines:
                print(line.rstrip())
        print("... (truncated)")
        print()
    except:
        print("Could not read template file")
        print()
    
    # 4. Dry Run Test Submission
    demo_section(
        "4. Test Submission (Dry Run)",
        "Submit test cases without actually executing them"
    )
    
    run_cli_command([
        "test", "submit",
        "--name", "Demo Memory Test",
        "--description", "Demonstration of memory allocation testing",
        "--type", "unit",
        "--subsystem", "mm",
        "--script", "echo 'Testing memory allocation'; exit 0",
        "--priority", "7",
        "--hardware-arch", "x86_64",
        "--hardware-memory", "4096",
        "--virtual",
        "--dry-run"
    ])
    
    # 5. Batch Test Submission
    demo_section(
        "5. Batch Test Submission (Dry Run)",
        "Submit multiple tests from configuration file"
    )
    
    run_cli_command([
        "test", "submit-batch",
        "--config-file", "demo_template.yaml",
        "--priority", "5",
        "--dry-run"
    ])
    
    # 6. Help System
    demo_section(
        "6. Comprehensive Help System",
        "Explore available commands and options"
    )
    
    print("📚 Main help:")
    run_cli_command(["--help"])
    
    print("📚 Test commands help:")
    run_cli_command(["test", "--help"])
    
    # 7. API-Dependent Commands (Expected to Fail)
    demo_section(
        "7. API-Dependent Commands",
        "Commands that require API server (will show graceful error handling)"
    )
    
    print("🔍 These commands demonstrate graceful error handling when API server is unavailable:")
    print()
    
    api_commands = [
        (["test", "list"], "List submitted tests"),
        (["status", "active"], "Show active executions"),
        (["results", "summary"], "Results summary"),
        (["env", "list"], "List environments"),
    ]
    
    for args, description in api_commands:
        print(f"📡 {description}:")
        run_cli_command(args)
    
    # 8. Interactive Mode Info
    demo_section(
        "8. Interactive Mode",
        "Information about interactive shell and explorer modes"
    )
    
    print("🖥️  Interactive Shell Mode:")
    print("   Command: agentic-test interactive shell")
    print("   Features:")
    print("   • Interactive command prompt")
    print("   • Real-time system status")
    print("   • Guided test submission")
    print("   • Built-in help system")
    print()
    
    print("🔍 System Explorer Mode:")
    print("   Command: agentic-test interactive explore")
    print("   Features:")
    print("   • Browse test results")
    print("   • Explore active executions")
    print("   • Environment status")
    print("   • Failure analysis")
    print()
    
    # 9. Advanced Features
    demo_section(
        "9. Advanced Features",
        "Showcase of advanced CLI capabilities"
    )
    
    print("🔧 Configuration Management:")
    print("   • Export/import configuration: agentic-test config export/import")
    print("   • Interactive wizard: agentic-test config wizard")
    print("   • Environment variables support")
    print()
    
    print("📊 Monitoring & Analysis:")
    print("   • Real-time status watching: agentic-test status active --watch")
    print("   • Coverage reports: agentic-test results coverage <test-id>")
    print("   • Failure analysis: agentic-test results failure <test-id>")
    print()
    
    print("🖥️  Environment Management:")
    print("   • Create environments: agentic-test env create --architecture x86_64")
    print("   • Environment cleanup: agentic-test env cleanup --idle-only")
    print("   • Resource statistics: agentic-test env stats")
    print()
    
    print("🤖 AI-Powered Features:")
    print("   • Code analysis: agentic-test test analyze --repository-url <url>")
    print("   • Automatic test generation from code changes")
    print("   • Intelligent failure analysis and suggestions")
    print()
    
    # Summary
    demo_section(
        "🎉 Demo Complete",
        "CLI Features Summary"
    )
    
    features = [
        "✅ Comprehensive test management (submit, list, monitor)",
        "✅ Real-time status monitoring with watch mode",
        "✅ Detailed results analysis and reporting",
        "✅ Environment management and resource control",
        "✅ Configuration management with validation",
        "✅ Interactive shell and explorer modes",
        "✅ Template generation for batch operations",
        "✅ Dry-run functionality for safe testing",
        "✅ Graceful error handling and user-friendly messages",
        "✅ Comprehensive help system",
        "✅ JSON/YAML output formats for scripting",
        "✅ CI/CD integration capabilities"
    ]
    
    print("The Agentic AI Testing System CLI provides:")
    print()
    for feature in features:
        print(f"  {feature}")
    
    print()
    print("🚀 Ready for production use!")
    print("📖 See cli/README.md for complete documentation")
    print("🔧 Use 'agentic-test --help' to get started")
    
    # Cleanup
    try:
        import os
        os.unlink("demo_template.yaml")
        os.unlink("demo_template.json")
    except:
        pass

if __name__ == "__main__":
    main()