"""Examples of using Amazon Q Developer and Kiro as LLM providers for test generation.

This demonstrates how to use the extended LLM providers for the AI test generator.
"""

from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers_extended import (
    ExtendedLLMProviderFactory,
    ExtendedLLMProvider,
    create_provider
)
from ai_generator.models import Function, CodeAnalysis, TestType, RiskLevel


def example_amazon_q_developer():
    """Example: Using Amazon Q Developer Pro for test generation."""
    print("=" * 70)
    print("Example 1: Amazon Q Developer Pro")
    print("=" * 70)
    
    # Method 1: Using factory
    provider = ExtendedLLMProviderFactory.create(
        provider=ExtendedLLMProvider.AMAZON_Q,
        region="us-east-1",
        # Optional: specify AWS profile
        # profile="my-aws-profile"
    )
    
    # Create test generator with Amazon Q
    generator = AITestGenerator(llm_provider=provider)
    
    # Sample code diff
    diff = """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -100,6 +100,10 @@ void schedule(void)
     struct task_struct *prev, *next;
     
     prev = current;
+    
+    /* New scheduling logic */
+    if (prev->policy == SCHED_FIFO)
+        return;
     
     next = pick_next_task(rq);
"""
    
    print("\n1. Analyzing code changes with Amazon Q...")
    analysis = generator.analyze_code_changes(diff)
    print(f"   - Changed files: {len(analysis.changed_files)}")
    print(f"   - Affected subsystems: {analysis.affected_subsystems}")
    print(f"   - Impact score: {analysis.impact_score}")
    
    print("\n2. Generating test cases with Amazon Q...")
    test_cases = generator.generate_test_cases(analysis)
    print(f"   - Generated {len(test_cases)} test cases")
    
    if test_cases:
        print(f"\n3. Sample test case:")
        tc = test_cases[0]
        print(f"   - Name: {tc.name}")
        print(f"   - Type: {tc.test_type}")
        print(f"   - Description: {tc.description}")


def example_kiro_provider():
    """Example: Using Kiro AI for test generation."""
    print("\n" + "=" * 70)
    print("Example 2: Kiro AI Provider")
    print("=" * 70)
    
    # Method 2: Using convenience function
    provider = create_provider(
        "kiro",
        api_key="your-kiro-api-key",  # Or set KIRO_API_KEY env var
        model="kiro-default"
    )
    
    # Create test generator with Kiro
    generator = AITestGenerator(llm_provider=provider)
    
    # Create analysis for a function
    function = Function(
        name="hash_table_insert",
        file_path="lib/hashtable.c",
        line_number=150,
        subsystem="data_structures",
        signature="int hash_table_insert(hash_table_t *table, const char *key, void *value)"
    )
    
    analysis = CodeAnalysis(
        changed_files=["lib/hashtable.c"],
        changed_functions=[function],
        affected_subsystems=["data_structures"],
        impact_score=0.6,
        risk_level=RiskLevel.MEDIUM,
        suggested_test_types=[TestType.UNIT, TestType.FUZZ]
    )
    
    print("\n1. Generating tests for hash_table_insert with Kiro...")
    test_cases = generator.generate_test_cases(analysis)
    print(f"   - Generated {len(test_cases)} test cases")
    
    print("\n2. Generating property-based tests with Kiro...")
    property_tests = generator.generate_property_tests([function])
    print(f"   - Generated {len(property_tests)} property tests")
    
    if test_cases:
        print(f"\n3. Test types generated:")
        test_types = set(tc.test_type for tc in test_cases)
        for tt in test_types:
            count = sum(1 for tc in test_cases if tc.test_type == tt)
            print(f"   - {tt}: {count} tests")


def example_configuration_via_settings():
    """Example: Configuring providers via settings."""
    print("\n" + "=" * 70)
    print("Example 3: Configuration via Settings")
    print("=" * 70)
    
    # You can configure the provider in your settings
    from config import get_settings
    
    settings = get_settings()
    
    # Option 1: Use Amazon Q Developer
    print("\nOption 1: Amazon Q Developer")
    print("Set in .env file:")
    print("  LLM__PROVIDER=amazon_q")
    print("  AWS_ACCESS_KEY_ID=your-key")
    print("  AWS_SECRET_ACCESS_KEY=your-secret")
    print("  AWS_REGION=us-east-1")
    
    # Option 2: Use Kiro
    print("\nOption 2: Kiro AI")
    print("Set in .env file:")
    print("  LLM__PROVIDER=kiro")
    print("  KIRO_API_KEY=your-kiro-key")
    print("  KIRO_API_URL=https://api.kiro.ai/v1")
    
    # Then create generator without specifying provider
    # It will use the configured provider from settings
    print("\nThen in your code:")
    print("  generator = AITestGenerator()  # Uses settings")


def example_comparing_providers():
    """Example: Comparing different providers for the same task."""
    print("\n" + "=" * 70)
    print("Example 4: Comparing Providers")
    print("=" * 70)
    
    function = Function(
        name="validate_input",
        file_path="src/validation.c",
        line_number=50,
        subsystem="input_validation"
    )
    
    analysis = CodeAnalysis(
        changed_files=["src/validation.c"],
        changed_functions=[function],
        affected_subsystems=["input_validation"],
        impact_score=0.8,
        risk_level=RiskLevel.HIGH,
        suggested_test_types=[TestType.UNIT, TestType.SECURITY]
    )
    
    providers = {
        "Amazon Q Developer": create_provider("amazon_q", region="us-east-1"),
        "Kiro AI": create_provider("kiro", api_key="your-key"),
        # You can also compare with other providers
        # "OpenAI": create_provider("openai", api_key="your-key"),
        # "Anthropic": create_provider("anthropic", api_key="your-key"),
    }
    
    print("\nGenerating tests with different providers:")
    for provider_name, provider in providers.items():
        print(f"\n{provider_name}:")
        try:
            generator = AITestGenerator(llm_provider=provider)
            test_cases = generator.generate_test_cases(analysis)
            print(f"  ✓ Generated {len(test_cases)} test cases")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def example_advanced_amazon_q_features():
    """Example: Using advanced Amazon Q Developer features."""
    print("\n" + "=" * 70)
    print("Example 5: Advanced Amazon Q Features")
    print("=" * 70)
    
    # Amazon Q Developer can use AWS profile for authentication
    provider = ExtendedLLMProviderFactory.create(
        provider=ExtendedLLMProvider.AMAZON_Q,
        profile="my-dev-profile",  # Use AWS CLI profile
        region="us-west-2"
    )
    
    generator = AITestGenerator(llm_provider=provider)
    
    print("\nAmazon Q Developer Pro features:")
    print("  - Uses your AWS credentials and profiles")
    print("  - Integrated with AWS services")
    print("  - Can access your AWS resources for context")
    print("  - Supports multiple AWS regions")
    print("  - Enterprise-grade security and compliance")
    
    # Generate tests with additional context
    print("\nGenerating tests with AWS context...")
    # The provider can leverage AWS-specific knowledge
    # for better test generation


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("AI Test Generator: Amazon Q Developer & Kiro Examples")
    print("=" * 70)
    
    # Note: These examples require proper API keys and credentials
    print("\nNote: To run these examples, you need:")
    print("  1. Amazon Q Developer: AWS credentials with Q access")
    print("  2. Kiro AI: Kiro API key")
    print("\nSet environment variables:")
    print("  - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    print("  - KIRO_API_KEY")
    
    # Uncomment to run examples (requires valid credentials)
    # example_amazon_q_developer()
    # example_kiro_provider()
    example_configuration_via_settings()
    # example_comparing_providers()
    # example_advanced_amazon_q_features()
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
