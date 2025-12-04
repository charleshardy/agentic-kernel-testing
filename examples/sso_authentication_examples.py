"""Examples of using SSO authentication with Amazon Q and Kiro.

This demonstrates how to use Single Sign-On (SSO) for authentication
instead of API keys.
"""

from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers_extended import (
    ExtendedLLMProviderFactory,
    ExtendedLLMProvider,
    AmazonQDeveloperProvider,
    KiroProvider
)
from ai_generator.auth import (
    AmazonQSSOProvider,
    KiroSSOProvider,
    get_sso_provider
)


def example_amazon_q_sso_with_profile():
    """Example: Amazon Q with AWS SSO using CLI profile."""
    print("=" * 70)
    print("Example 1: Amazon Q with AWS SSO (CLI Profile)")
    print("=" * 70)
    
    # Method 1: Use AWS CLI profile (easiest)
    provider = AmazonQDeveloperProvider(
        profile="my-sso-profile",  # Your AWS CLI SSO profile
        region="us-east-1"
    )
    
    generator = AITestGenerator(llm_provider=provider)
    
    print("\n✓ Authenticated using AWS CLI SSO profile")
    print("  No manual authentication required!")
    print("  Uses credentials from: aws sso login --profile my-sso-profile")


def example_amazon_q_sso_device_code():
    """Example: Amazon Q with AWS SSO using device code flow."""
    print("\n" + "=" * 70)
    print("Example 2: Amazon Q with AWS SSO (Device Code Flow)")
    print("=" * 70)
    
    # Method 2: Use device code flow for interactive authentication
    provider = AmazonQDeveloperProvider(
        use_sso=True,
        sso_start_url="https://my-company.awsapps.com/start",
        sso_region="us-east-1",
        region="us-east-1"
    )
    
    # This will:
    # 1. Open browser for authentication
    # 2. Display device code
    # 3. Wait for user to authenticate
    # 4. Cache token for future use
    
    generator = AITestGenerator(llm_provider=provider)
    
    print("\n✓ Authenticated using AWS SSO device code flow")
    print("  Token cached for future use")


def example_amazon_q_sso_standalone():
    """Example: Using SSO provider standalone."""
    print("\n" + "=" * 70)
    print("Example 3: Amazon Q SSO Provider Standalone")
    print("=" * 70)
    
    # Create SSO provider directly
    sso = AmazonQSSOProvider(
        sso_start_url="https://my-company.awsapps.com/start",
        sso_region="us-east-1"
    )
    
    # Get token (will authenticate if needed)
    token = sso.get_token()
    print(f"\n✓ Got SSO token")
    print(f"  Token type: {token.token_type}")
    print(f"  Expires: {token.expires_at}")
    
    # Use token with provider
    provider = AmazonQDeveloperProvider(
        api_key=token.access_token,
        region="us-east-1"
    )
    
    generator = AITestGenerator(llm_provider=provider)


def example_kiro_sso_oauth():
    """Example: Kiro with OAuth2 SSO."""
    print("\n" + "=" * 70)
    print("Example 4: Kiro with OAuth2 SSO")
    print("=" * 70)
    
    # Method 1: Use SSO with provider
    provider = KiroProvider(
        use_sso=True,
        client_id="your-client-id",  # From Kiro dashboard
        client_secret="your-client-secret"
    )
    
    # This will:
    # 1. Open browser for OAuth2 authentication
    # 2. Display device code
    # 3. Wait for user to authorize
    # 4. Cache token for future use
    
    generator = AITestGenerator(llm_provider=provider)
    
    print("\n✓ Authenticated using Kiro OAuth2 SSO")
    print("  Token cached and will auto-refresh")


def example_kiro_sso_standalone():
    """Example: Using Kiro SSO provider standalone."""
    print("\n" + "=" * 70)
    print("Example 5: Kiro SSO Provider Standalone")
    print("=" * 70)
    
    # Create SSO provider directly
    sso = KiroSSOProvider(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    
    # Get token (will authenticate if needed)
    token = sso.get_token()
    print(f"\n✓ Got OAuth2 token")
    print(f"  Token type: {token.token_type}")
    print(f"  Scopes: {token.scope}")
    print(f"  Expires: {token.expires_at}")
    
    # Token will auto-refresh when expired
    # Force refresh if needed
    token = sso.get_token(force_refresh=True)
    print("\n✓ Token refreshed")


def example_token_caching():
    """Example: Token caching and reuse."""
    print("\n" + "=" * 70)
    print("Example 6: Token Caching")
    print("=" * 70)
    
    # First authentication - will prompt for login
    print("\nFirst authentication (will open browser):")
    sso1 = KiroSSOProvider(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    token1 = sso1.get_token()
    print("✓ Authenticated and token cached")
    
    # Second authentication - will use cached token
    print("\nSecond authentication (uses cache):")
    sso2 = KiroSSOProvider(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    token2 = sso2.get_token()
    print("✓ Used cached token (no browser needed!)")
    
    # Clear cache if needed
    sso2.clear_cache()
    print("\n✓ Cache cleared")


def example_environment_variables():
    """Example: Configuration via environment variables."""
    print("\n" + "=" * 70)
    print("Example 7: Environment Variable Configuration")
    print("=" * 70)
    
    print("\nFor Amazon Q SSO, set:")
    print("  export AWS_SSO_START_URL='https://my-company.awsapps.com/start'")
    print("  export AWS_SSO_REGION='us-east-1'")
    print("  export AWS_PROFILE='my-sso-profile'")
    
    print("\nFor Kiro SSO, set:")
    print("  export KIRO_CLIENT_ID='your-client-id'")
    print("  export KIRO_CLIENT_SECRET='your-client-secret'")
    
    print("\nThen in code:")
    print("  # Amazon Q - uses env vars automatically")
    print("  provider = AmazonQDeveloperProvider(use_sso=True)")
    print()
    print("  # Kiro - uses env vars automatically")
    print("  provider = KiroProvider(use_sso=True)")


def example_error_handling():
    """Example: Error handling for SSO."""
    print("\n" + "=" * 70)
    print("Example 8: Error Handling")
    print("=" * 70)
    
    try:
        # Attempt authentication
        sso = KiroSSOProvider(
            client_id="your-client-id",
            client_secret="your-client-secret"
        )
        token = sso.get_token()
        print("✓ Authentication successful")
        
    except TimeoutError:
        print("✗ Authentication timed out")
        print("  User did not complete authentication in time")
        
    except RuntimeError as e:
        print(f"✗ Authentication failed: {e}")
        print("  Check your credentials and try again")
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def example_complete_workflow():
    """Example: Complete workflow with SSO."""
    print("\n" + "=" * 70)
    print("Example 9: Complete Workflow with SSO")
    print("=" * 70)
    
    # Step 1: Authenticate with SSO
    print("\nStep 1: Authenticate with Amazon Q SSO")
    provider = AmazonQDeveloperProvider(
        use_sso=True,
        sso_start_url="https://my-company.awsapps.com/start",
        sso_region="us-east-1",
        region="us-east-1"
    )
    print("✓ Authenticated")
    
    # Step 2: Create test generator
    print("\nStep 2: Create test generator")
    generator = AITestGenerator(llm_provider=provider)
    print("✓ Generator created")
    
    # Step 3: Analyze code
    print("\nStep 3: Analyze code changes")
    diff = """
diff --git a/src/main.c b/src/main.c
...
"""
    # analysis = generator.analyze_code_changes(diff)
    print("✓ Code analyzed")
    
    # Step 4: Generate tests
    print("\nStep 4: Generate tests")
    # test_cases = generator.generate_test_cases(analysis)
    print("✓ Tests generated")
    
    print("\n" + "=" * 70)
    print("Complete workflow finished!")
    print("Token will be reused for future runs (no re-authentication needed)")
    print("=" * 70)


def example_factory_with_sso():
    """Example: Using factory with SSO."""
    print("\n" + "=" * 70)
    print("Example 10: Factory Pattern with SSO")
    print("=" * 70)
    
    # Amazon Q with SSO
    amazon_q = ExtendedLLMProviderFactory.create(
        provider=ExtendedLLMProvider.AMAZON_Q,
        use_sso=True,
        sso_start_url="https://my-company.awsapps.com/start",
        sso_region="us-east-1"
    )
    print("✓ Amazon Q provider created with SSO")
    
    # Kiro with SSO
    kiro = ExtendedLLMProviderFactory.create(
        provider=ExtendedLLMProvider.KIRO,
        use_sso=True,
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    print("✓ Kiro provider created with SSO")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("SSO Authentication Examples")
    print("=" * 70)
    
    print("\nThese examples demonstrate SSO authentication.")
    print("To run them, you need:")
    print("  1. AWS SSO configured (for Amazon Q)")
    print("  2. Kiro OAuth2 credentials (for Kiro)")
    
    # Run examples (commented out to avoid actual authentication)
    # example_amazon_q_sso_with_profile()
    # example_amazon_q_sso_device_code()
    # example_amazon_q_sso_standalone()
    # example_kiro_sso_oauth()
    # example_kiro_sso_standalone()
    # example_token_caching()
    example_environment_variables()
    # example_error_handling()
    # example_complete_workflow()
    # example_factory_with_sso()
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
