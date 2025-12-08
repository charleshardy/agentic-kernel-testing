"""Examples of using the Root Cause Analyzer with different LLM providers.

This script demonstrates how to use the RootCauseAnalyzer with:
- OpenAI
- Anthropic
- Amazon Bedrock
- Amazon Q Developer Pro
- Kiro AI
"""

from datetime import datetime
from analysis.root_cause_analyzer import RootCauseAnalyzer
from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, FailureInfo, ArtifactBundle
)


def create_sample_failure() -> TestResult:
    """Create a sample test failure for demonstration."""
    env = Environment(
        id="test_env_001",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel Xeon",
            memory_mb=8192
        ),
        status=EnvironmentStatus.IDLE,
        created_at=datetime.now(),
        last_used=datetime.now()
    )
    
    failure_info = FailureInfo(
        error_message="NULL pointer dereference at address 0xdeadbeef",
        stack_trace="""Call Trace:
 [<ffffffffa0123456>] problematic_function+0x42/0x100 [mymodule]
 [<ffffffff81234567>] caller_function+0x10/0x20
 [<ffffffff81345678>] sys_call_handler+0x5/0x10
 [<ffffffff81456789>] entry_SYSCALL_64+0x1/0x5
""",
        exit_code=139,
        kernel_panic=True
    )
    
    return TestResult(
        test_id="test_kernel_module_001",
        status=TestStatus.FAILED,
        execution_time=2.5,
        environment=env,
        artifacts=ArtifactBundle(
            logs=["kernel.log", "dmesg.log"],
            core_dumps=["core.dump"]
        ),
        failure_info=failure_info,
        timestamp=datetime.now()
    )


def example_openai():
    """Example using OpenAI for root cause analysis."""
    print("\n=== OpenAI Example ===")
    
    # Initialize analyzer with OpenAI
    analyzer = RootCauseAnalyzer(
        provider_type="openai",
        api_key="your-openai-api-key",  # Set via environment variable OPENAI_API_KEY
        model="gpt-4"
    )
    
    # Analyze a failure
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")
    print(f"Error Pattern: {analysis.error_pattern}")
    print(f"Suggested Fixes: {len(analysis.suggested_fixes)}")


def example_anthropic():
    """Example using Anthropic Claude for root cause analysis."""
    print("\n=== Anthropic Claude Example ===")
    
    # Initialize analyzer with Anthropic
    analyzer = RootCauseAnalyzer(
        provider_type="anthropic",
        api_key="your-anthropic-api-key",  # Set via environment variable ANTHROPIC_API_KEY
        model="claude-3-5-sonnet-20241022"
    )
    
    # Analyze a failure
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")


def example_amazon_q_with_api_keys():
    """Example using Amazon Q Developer Pro with API keys."""
    print("\n=== Amazon Q Developer Pro (API Keys) Example ===")
    
    # Initialize analyzer with Amazon Q using API keys
    analyzer = RootCauseAnalyzer(
        provider_type="amazon_q",
        api_key="your-aws-access-key",  # Set via environment variable AWS_ACCESS_KEY_ID
        region="us-east-1"
    )
    
    # Analyze a failure
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")
    print(f"Suggested Fixes:")
    for i, fix in enumerate(analysis.suggested_fixes, 1):
        print(f"  {i}. {fix.description}")


def example_amazon_q_with_sso():
    """Example using Amazon Q Developer Pro with AWS SSO."""
    print("\n=== Amazon Q Developer Pro (AWS SSO) Example ===")
    
    # Initialize analyzer with Amazon Q using SSO
    analyzer = RootCauseAnalyzer(
        provider_type="amazon_q",
        region="us-east-1",
        use_sso=True,
        sso_start_url="https://my-company.awsapps.com/start",
        sso_region="us-east-1",
        profile="my-sso-profile"
    )
    
    # Analyze a failure
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")


def example_amazon_q_with_profile():
    """Example using Amazon Q Developer Pro with AWS CLI profile."""
    print("\n=== Amazon Q Developer Pro (AWS Profile) Example ===")
    
    # Initialize analyzer with Amazon Q using AWS CLI profile
    analyzer = RootCauseAnalyzer(
        provider_type="amazon_q",
        region="us-east-1",
        profile="my-aws-profile"  # Uses credentials from ~/.aws/credentials
    )
    
    # Analyze a failure
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")


def example_kiro():
    """Example using Kiro AI for root cause analysis."""
    print("\n=== Kiro AI Example ===")
    
    # Initialize analyzer with Kiro
    analyzer = RootCauseAnalyzer(
        provider_type="kiro",
        api_key="your-kiro-api-key",  # Set via environment variable KIRO_API_KEY
        api_url="https://api.kiro.ai/v1"
    )
    
    # Analyze a failure
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")
    print(f"Suggested Fixes:")
    for i, fix in enumerate(analysis.suggested_fixes, 1):
        print(f"  {i}. {fix.description} (confidence: {fix.confidence:.2f})")


def example_kiro_with_sso():
    """Example using Kiro AI with OAuth2 SSO."""
    print("\n=== Kiro AI (OAuth2 SSO) Example ===")
    
    # Initialize analyzer with Kiro using SSO
    analyzer = RootCauseAnalyzer(
        provider_type="kiro",
        use_sso=True,
        client_id="your-oauth-client-id",
        client_secret="your-oauth-client-secret"
    )
    
    # Analyze a failure
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")


def example_fallback_pattern_based():
    """Example using pattern-based analysis (no LLM)."""
    print("\n=== Pattern-Based Analysis (No LLM) Example ===")
    
    # Initialize analyzer without LLM provider
    analyzer = RootCauseAnalyzer()
    
    # Analyze a failure - will use pattern-based analysis
    failure = create_sample_failure()
    analysis = analyzer.analyze_failure(failure)
    
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence}")
    print(f"Error Pattern: {analysis.error_pattern}")
    print(f"Suggested Fixes:")
    for i, fix in enumerate(analysis.suggested_fixes, 1):
        print(f"  {i}. {fix.description}")


def example_failure_grouping():
    """Example of grouping related failures."""
    print("\n=== Failure Grouping Example ===")
    
    analyzer = RootCauseAnalyzer()
    
    # Create multiple failures with similar patterns
    failures = []
    for i in range(5):
        env = Environment(
            id=f"env_{i}",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=8192
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        # First 3 have NULL pointer errors
        if i < 3:
            failure_info = FailureInfo(
                error_message="NULL pointer dereference at address 0xdeadbeef",
                stack_trace="Call Trace:\n [deadbeef] test_function+0x42/0x100\n",
                exit_code=139
            )
        # Last 2 have use-after-free errors
        else:
            failure_info = FailureInfo(
                error_message="use-after-free in function uaf_test",
                stack_trace="Call Trace:\n [cafebabe] uaf_test+0x10/0x50\n",
                exit_code=139
            )
        
        failures.append(TestResult(
            test_id=f"test_{i}",
            status=TestStatus.FAILED,
            execution_time=1.0,
            environment=env,
            artifacts=ArtifactBundle(),
            failure_info=failure_info,
            timestamp=datetime.now()
        ))
    
    # Group failures
    groups = analyzer.group_failures(failures)
    
    print(f"Found {len(groups)} distinct failure groups:")
    for signature, group_failures in groups.items():
        print(f"\nGroup {signature[:8]}... ({len(group_failures)} failures):")
        # Analyze one failure from the group
        analysis = analyzer.analyze_failure(group_failures[0])
        print(f"  Root Cause: {analysis.root_cause}")
        print(f"  Test IDs: {[f.test_id for f in group_failures]}")


if __name__ == "__main__":
    print("Root Cause Analyzer Examples")
    print("=" * 60)
    
    # Run examples (comment out those requiring API keys)
    
    # Pattern-based analysis (no API key needed)
    example_fallback_pattern_based()
    
    # Failure grouping (no API key needed)
    example_failure_grouping()
    
    # Uncomment to run with actual API keys:
    # example_openai()
    # example_anthropic()
    # example_amazon_q_with_api_keys()
    # example_amazon_q_with_sso()
    # example_amazon_q_with_profile()
    # example_kiro()
    # example_kiro_with_sso()
