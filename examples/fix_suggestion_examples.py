"""Examples demonstrating the fix suggestion generator.

This module shows how to use the FixSuggestionGenerator to generate
fix suggestions and code patches for test failures.
"""

import os
from datetime import datetime

from analysis.fix_suggestion_generator import (
    FixSuggestionGenerator,
    CodeContext
)
from analysis.root_cause_analyzer import RootCauseAnalyzer
from ai_generator.models import (
    TestResult, TestStatus, FailureInfo, Environment,
    HardwareConfig, EnvironmentStatus, Commit
)


def example_basic_fix_suggestion():
    """Example: Generate basic fix suggestions for a test failure."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Fix Suggestion Generation")
    print("=" * 70)
    
    # Create a test failure
    env = Environment(
        id="env-1",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel Core i7",
            memory_mb=8192
        ),
        status=EnvironmentStatus.IDLE
    )
    
    failure = TestResult(
        test_id="test-null-pointer-001",
        status=TestStatus.FAILED,
        execution_time=2.5,
        environment=env,
        failure_info=FailureInfo(
            error_message="NULL pointer dereference at address 0x0000000000000000",
            stack_trace="""
[  123.456789] BUG: kernel NULL pointer dereference, address: 0000000000000000
[  123.456790] #PF: supervisor read access in kernel mode
[  123.456791] #PF: error_code(0x0000) - not-present page
[  123.456792] PGD 0 P4D 0
[  123.456793] Oops: 0000 [#1] SMP PTI
[  123.456794] CPU: 2 PID: 1234 Comm: test_process Not tainted 5.15.0-test #1
[  123.456795] Hardware name: QEMU Standard PC (i440FX + PIIX, 1996)
[  123.456796] RIP: 0010:my_driver_read+0x42/0x100 [my_driver]
[  123.456797] Code: 48 8b 47 10 48 85 c0 74 05 48 8b 40 08 c3 31 c0 c3
[  123.456798] RSP: 0018:ffffc90000123d80 EFLAGS: 00010246
[  123.456799] Call Trace:
[  123.456800]  vfs_read+0x95/0x190
[  123.456801]  ksys_read+0x67/0xe0
[  123.456802]  do_syscall_64+0x5c/0xc0
[  123.456803]  entry_SYSCALL_64_after_hwframe+0x44/0xae
""",
            exit_code=1,
            kernel_panic=True
        )
    )
    
    # Initialize fix suggestion generator
    # Note: In production, you would provide actual API credentials
    try:
        generator = FixSuggestionGenerator(
            provider_type="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4"
        )
        
        # Generate fix suggestions
        print("\nGenerating fix suggestions...")
        suggestions = generator.suggest_fixes_for_failure(failure)
        
        print(f"\nGenerated {len(suggestions)} fix suggestions:\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion.description}")
            print(f"   Confidence: {suggestion.confidence:.2f}")
            print(f"   Rationale: {suggestion.rationale}")
            if suggestion.code_patch:
                print(f"   Patch available: Yes")
            print()
        
    except Exception as e:
        print(f"\nNote: This example requires API credentials.")
        print(f"Set OPENAI_API_KEY environment variable to run.")
        print(f"Error: {e}")


def example_fix_with_code_context():
    """Example: Generate fix suggestions with code context."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Fix Suggestion with Code Context")
    print("=" * 70)
    
    # Create failure with detailed context
    env = Environment(
        id="env-2",
        config=HardwareConfig(
            architecture="arm64",
            cpu_model="ARM Cortex-A72",
            memory_mb=4096
        ),
        status=EnvironmentStatus.IDLE
    )
    
    failure = TestResult(
        test_id="test-buffer-overflow-001",
        status=TestStatus.FAILED,
        execution_time=1.8,
        environment=env,
        failure_info=FailureInfo(
            error_message="KASAN: slab-out-of-bounds in strcpy",
            stack_trace="strcpy+0x20/0x40\nmy_function+0x15/0x30",
            exit_code=1
        )
    )
    
    # Provide code context
    code_context = CodeContext(
        file_path="drivers/my_driver/main.c",
        function_name="my_function",
        line_number=156,
        surrounding_code="""
static int my_function(const char *input) {
    char buffer[32];
    strcpy(buffer, input);  // Line 156 - Potential overflow
    return process_buffer(buffer);
}
""",
        error_message="Buffer overflow in strcpy",
        stack_trace=failure.failure_info.stack_trace
    )
    
    try:
        generator = FixSuggestionGenerator(
            provider_type="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4"
        )
        
        # Perform root cause analysis first
        analyzer = RootCauseAnalyzer(
            provider_type="openai",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        print("\nPerforming root cause analysis...")
        failure_analysis = analyzer.analyze_failure(failure)
        
        print(f"Root Cause: {failure_analysis.root_cause}")
        print(f"Confidence: {failure_analysis.confidence:.2f}")
        
        # Generate fix suggestions with code context
        print("\nGenerating fix suggestions with code context...")
        suggestions = generator.generate_fix_suggestions(
            failure_analysis,
            code_context=code_context
        )
        
        print(f"\nGenerated {len(suggestions)} fix suggestions:\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion.description}")
            print(f"   Confidence: {suggestion.confidence:.2f}")
            print(f"   Rationale: {suggestion.rationale}")
            print()
            
            # Generate code patch
            print("   Generating code patch...")
            patch = generator.generate_code_patch(suggestion, code_context)
            if patch:
                print("   Patch:")
                print("   " + "\n   ".join(patch.split("\n")[:10]))
                print("   ...")
            print()
        
    except Exception as e:
        print(f"\nNote: This example requires API credentials.")
        print(f"Error: {e}")


def example_fix_with_git_history():
    """Example: Generate fix suggestions using git history."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Fix Suggestion with Git History")
    print("=" * 70)
    
    # Create failure
    env = Environment(
        id="env-3",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="AMD EPYC",
            memory_mb=16384
        ),
        status=EnvironmentStatus.IDLE
    )
    
    failure = TestResult(
        test_id="test-regression-001",
        status=TestStatus.FAILED,
        execution_time=3.2,
        environment=env,
        failure_info=FailureInfo(
            error_message="Use-after-free in network subsystem",
            stack_trace="kfree+0x10/0x20\nnet_cleanup+0x30/0x50",
            exit_code=1
        )
    )
    
    # Provide suspicious commits
    commits = [
        Commit(
            sha="abc123def456",
            message="net: Refactor cleanup logic in network subsystem",
            author="developer@example.com",
            timestamp=datetime(2024, 12, 7, 10, 30),
            files_changed=["net/core/dev.c", "net/core/cleanup.c"]
        ),
        Commit(
            sha="789ghi012jkl",
            message="net: Add new feature for packet processing",
            author="developer@example.com",
            timestamp=datetime(2024, 12, 6, 15, 45),
            files_changed=["net/core/packet.c"]
        ),
        Commit(
            sha="345mno678pqr",
            message="mm: Optimize memory allocation paths",
            author="another@example.com",
            timestamp=datetime(2024, 12, 5, 9, 15),
            files_changed=["mm/slab.c", "mm/page_alloc.c"]
        )
    ]
    
    try:
        generator = FixSuggestionGenerator(
            provider_type="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4"
        )
        
        analyzer = RootCauseAnalyzer(
            provider_type="openai",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        print("\nPerforming root cause analysis...")
        failure_analysis = analyzer.analyze_failure(failure)
        
        print(f"Root Cause: {failure_analysis.root_cause}")
        
        # Correlate with commits
        print("\nCorrelating with recent commits...")
        suspicious_commits = analyzer.correlate_with_changes(failure, commits)
        
        print(f"Found {len(suspicious_commits)} suspicious commits:")
        for commit in suspicious_commits:
            print(f"  - {commit.sha[:8]}: {commit.message[:60]}")
        
        # Generate fix suggestions with commit context
        print("\nGenerating fix suggestions with commit context...")
        suggestions = generator.generate_fix_suggestions(
            failure_analysis,
            commits=suspicious_commits
        )
        
        print(f"\nGenerated {len(suggestions)} fix suggestions:\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion.description}")
            print(f"   Confidence: {suggestion.confidence:.2f}")
            print(f"   Rationale: {suggestion.rationale}")
            print()
        
    except Exception as e:
        print(f"\nNote: This example requires API credentials.")
        print(f"Error: {e}")


def example_using_amazon_q():
    """Example: Using Amazon Q Developer for fix suggestions."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Using Amazon Q Developer Pro")
    print("=" * 70)
    
    env = Environment(
        id="env-4",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel Xeon",
            memory_mb=8192
        ),
        status=EnvironmentStatus.IDLE
    )
    
    failure = TestResult(
        test_id="test-deadlock-001",
        status=TestStatus.FAILED,
        execution_time=5.0,
        environment=env,
        failure_info=FailureInfo(
            error_message="Possible circular locking dependency detected",
            stack_trace="mutex_lock+0x10/0x20\nmy_lock_function+0x30/0x50",
            exit_code=1,
            timeout_occurred=True
        )
    )
    
    try:
        # Initialize with Amazon Q Developer
        generator = FixSuggestionGenerator(
            provider_type="amazon_q",
            region="us-east-1",
            use_sso=True,
            sso_start_url=os.getenv("AWS_SSO_START_URL")
        )
        
        print("\nGenerating fix suggestions using Amazon Q Developer...")
        suggestions = generator.suggest_fixes_for_failure(failure)
        
        print(f"\nGenerated {len(suggestions)} fix suggestions:\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion.description}")
            print(f"   Confidence: {suggestion.confidence:.2f}")
            print()
        
    except Exception as e:
        print(f"\nNote: This example requires AWS credentials and Amazon Q access.")
        print(f"Error: {e}")


def example_using_kiro():
    """Example: Using Kiro AI for fix suggestions."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Using Kiro AI")
    print("=" * 70)
    
    env = Environment(
        id="env-5",
        config=HardwareConfig(
            architecture="riscv64",
            cpu_model="SiFive U74",
            memory_mb=4096
        ),
        status=EnvironmentStatus.IDLE
    )
    
    failure = TestResult(
        test_id="test-race-condition-001",
        status=TestStatus.FAILED,
        execution_time=2.1,
        environment=env,
        failure_info=FailureInfo(
            error_message="KTSAN: data race detected",
            stack_trace="read_data+0x10/0x20\nwrite_data+0x30/0x40",
            exit_code=1
        )
    )
    
    try:
        # Initialize with Kiro AI
        generator = FixSuggestionGenerator(
            provider_type="kiro",
            api_key=os.getenv("KIRO_API_KEY")
        )
        
        print("\nGenerating fix suggestions using Kiro AI...")
        suggestions = generator.suggest_fixes_for_failure(failure)
        
        print(f"\nGenerated {len(suggestions)} fix suggestions:\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion.description}")
            print(f"   Confidence: {suggestion.confidence:.2f}")
            print()
        
    except Exception as e:
        print(f"\nNote: This example requires Kiro API credentials.")
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FIX SUGGESTION GENERATOR EXAMPLES")
    print("=" * 70)
    print("\nThese examples demonstrate the fix suggestion generator capabilities.")
    print("Note: Most examples require API credentials to run.")
    print()
    
    # Run examples
    example_basic_fix_suggestion()
    example_fix_with_code_context()
    example_fix_with_git_history()
    example_using_amazon_q()
    example_using_kiro()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
