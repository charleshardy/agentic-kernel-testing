"""Extended LLM provider support for Amazon Q Developer and Kiro.

This module extends the base LLM providers with support for:
- Amazon Q Developer Pro (via AWS SDK)
- Kiro AI (via Kiro API)
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from .llm_providers import BaseLLMProvider, LLMResponse, LLMProvider as BaseLLMProvider_Enum
from enum import Enum


class ExtendedLLMProvider(str, Enum):
    """Extended LLM providers including Amazon Q and Kiro."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    AMAZON_Q = "amazon_q"
    KIRO = "kiro"


class AmazonQDeveloperProvider(BaseLLMProvider):
    """Amazon Q Developer Pro provider for code generation.
    
    Amazon Q Developer is AWS's AI-powered coding assistant that can:
    - Generate test code
    - Analyze code for issues
    - Suggest improvements
    - Generate documentation
    
    Supports authentication via:
    - AWS access keys
    - AWS CLI profiles
    - AWS SSO (IAM Identity Center)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        region: str = "us-east-1",
        profile: Optional[str] = None,
        use_sso: bool = False,
        sso_start_url: Optional[str] = None,
        sso_region: Optional[str] = None,
        **kwargs
    ):
        """Initialize Amazon Q Developer provider.
        
        Args:
            api_key: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            region: AWS region for Q Developer
            profile: AWS profile name (optional)
            use_sso: Use AWS SSO for authentication
            sso_start_url: AWS SSO start URL (required if use_sso=True)
            sso_region: AWS SSO region (defaults to region)
            **kwargs: Additional parameters for BaseLLMProvider
        """
        super().__init__(
            api_key=api_key or os.getenv("AWS_ACCESS_KEY_ID"),
            model="amazon-q-developer",
            **kwargs
        )
        self.region = region
        self.profile = profile
        self.use_sso = use_sso
        self.sso_start_url = sso_start_url
        self.sso_region = sso_region or region
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.sso_provider = None
        
        try:
            import boto3
            
            # Use SSO if requested
            if self.use_sso:
                from ai_generator.auth import AmazonQSSOProvider
                self.sso_provider = AmazonQSSOProvider(
                    sso_start_url=self.sso_start_url,
                    sso_region=self.sso_region,
                    profile_name=self.profile
                )
                # Get SSO token
                token = self.sso_provider.get_token()
                # Use token for session
                session = boto3.Session(
                    aws_access_key_id=token.access_token,
                    aws_secret_access_key=token.refresh_token,
                    region_name=self.region
                )
            # Create session with profile if specified
            elif self.profile:
                session = boto3.Session(profile_name=self.profile)
            else:
                session = boto3.Session(
                    aws_access_key_id=self.api_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
            
            # Amazon Q Developer uses the Q service
            self.client = session.client('q', region_name=self.region)
            
        except ImportError:
            raise ImportError(
                "boto3 package not installed. Install with: pip install boto3"
            )
        except Exception as e:
            # Fallback to bedrock-agent-runtime for Q Developer features
            try:
                if self.profile:
                    session = boto3.Session(profile_name=self.profile)
                else:
                    session = boto3.Session(
                        aws_access_key_id=self.api_key,
                        aws_secret_access_key=self.secret_key,
                        region_name=self.region
                    )
                self.client = session.client('bedrock-agent-runtime', region_name=self.region)
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to initialize Amazon Q Developer client: {e}. "
                    f"Fallback also failed: {e2}"
                )
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate code using Amazon Q Developer.
        
        Args:
            prompt: Input prompt for code generation
            **kwargs: Additional Q Developer-specific parameters
            
        Returns:
            LLMResponse with generated code
        """
        try:
            # Amazon Q Developer API call
            # Note: The actual API may vary - this is a conceptual implementation
            response = self.client.invoke_model(
                modelId="amazon-q-developer",
                body=json.dumps({
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", self.temperature),
                    "maxTokens": kwargs.get("max_tokens", self.max_tokens),
                    "context": kwargs.get("context", "test_generation")
                })
            )
            
            response_body = json.loads(response['body'].read())
            
            return LLMResponse(
                content=response_body.get("completion", response_body.get("output", "")),
                model="amazon-q-developer",
                tokens_used=response_body.get("usage", {}).get("totalTokens", 0),
                finish_reason=response_body.get("stopReason", "complete"),
                metadata={
                    "request_id": response.get("ResponseMetadata", {}).get("RequestId", ""),
                    "provider": "amazon_q"
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Amazon Q Developer API call failed: {e}")


class KiroProvider(BaseLLMProvider):
    """Kiro AI provider for test generation.
    
    Kiro is an AI-powered IDE that can:
    - Generate test code
    - Analyze codebases
    - Suggest improvements
    - Execute tasks autonomously
    
    Supports authentication via:
    - API key
    - OAuth2/OIDC SSO
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: str = "kiro-default",
        use_sso: bool = False,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        **kwargs
    ):
        """Initialize Kiro provider.
        
        Args:
            api_key: Kiro API key (defaults to KIRO_API_KEY env var)
            api_url: Kiro API endpoint (defaults to KIRO_API_URL env var)
            model: Kiro model to use
            use_sso: Use OAuth2 SSO for authentication
            client_id: OAuth2 client ID (required if use_sso=True)
            client_secret: OAuth2 client secret (required if use_sso=True)
            **kwargs: Additional parameters for BaseLLMProvider
        """
        super().__init__(
            api_key=api_key or os.getenv("KIRO_API_KEY"),
            model=model,
            **kwargs
        )
        self.api_url = api_url or os.getenv("KIRO_API_URL", "https://api.kiro.ai/v1")
        self.use_sso = use_sso
        self.client_id = client_id
        self.client_secret = client_secret
        self.sso_provider = None
        
        # Initialize SSO if requested
        if self.use_sso:
            from ai_generator.auth import KiroSSOProvider
            self.sso_provider = KiroSSOProvider(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            # Get initial token
            token = self.sso_provider.get_token()
            self.api_key = token.access_token
        elif not self.api_key:
            raise ValueError(
                "Kiro API key required. Set KIRO_API_KEY environment variable, "
                "pass api_key parameter, or use use_sso=True for SSO authentication."
            )
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate code using Kiro AI.
        
        Args:
            prompt: Input prompt for code generation
            **kwargs: Additional Kiro-specific parameters
            
        Returns:
            LLMResponse with generated code
        """
        # Refresh SSO token if needed
        if self.sso_provider:
            token = self.sso_provider.get_token()
            self.api_key = token.access_token
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "model": self.model,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "task_type": kwargs.get("task_type", "test_generation")
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/generate",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            return LLMResponse(
                content=data.get("content", data.get("output", "")),
                model=data.get("model", self.model),
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                finish_reason=data.get("finish_reason", "complete"),
                metadata={
                    "request_id": data.get("id", ""),
                    "provider": "kiro"
                }
            )
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Kiro API call failed: {e}")


class ExtendedLLMProviderFactory:
    """Factory for creating extended LLM providers including Amazon Q and Kiro."""
    
    @staticmethod
    def create(
        provider: ExtendedLLMProvider,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """Create an extended LLM provider instance.
        
        Args:
            provider: Provider type (including Amazon Q and Kiro)
            api_key: API key for the provider
            model: Model name (uses provider default if not specified)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider is not supported
            
        Examples:
            # Amazon Q Developer
            provider = ExtendedLLMProviderFactory.create(
                provider=ExtendedLLMProvider.AMAZON_Q,
                region="us-east-1"
            )
            
            # Kiro AI
            provider = ExtendedLLMProviderFactory.create(
                provider=ExtendedLLMProvider.KIRO,
                api_key="your-kiro-key"
            )
        """
        # Import base providers
        from .llm_providers import OpenAIProvider, AnthropicProvider, BedrockProvider
        
        if provider == ExtendedLLMProvider.OPENAI:
            return OpenAIProvider(api_key=api_key, model=model or "gpt-4", **kwargs)
        elif provider == ExtendedLLMProvider.ANTHROPIC:
            return AnthropicProvider(
                api_key=api_key,
                model=model or "claude-3-5-sonnet-20241022",
                **kwargs
            )
        elif provider == ExtendedLLMProvider.BEDROCK:
            return BedrockProvider(
                api_key=api_key,
                model=model or "anthropic.claude-3-sonnet-20240229-v1:0",
                **kwargs
            )
        elif provider == ExtendedLLMProvider.AMAZON_Q:
            return AmazonQDeveloperProvider(
                api_key=api_key,
                **kwargs
            )
        elif provider == ExtendedLLMProvider.KIRO:
            return KiroProvider(
                api_key=api_key,
                model=model or "kiro-default",
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Convenience function for backward compatibility
def create_provider(provider_name: str, **kwargs) -> BaseLLMProvider:
    """Create a provider by name string.
    
    Args:
        provider_name: Name of provider ("openai", "anthropic", "bedrock", "amazon_q", "kiro")
        **kwargs: Provider-specific parameters
        
    Returns:
        Configured LLM provider instance
        
    Examples:
        # Using Amazon Q Developer
        provider = create_provider("amazon_q", region="us-east-1")
        
        # Using Kiro
        provider = create_provider("kiro", api_key="your-key")
    """
    provider_enum = ExtendedLLMProvider(provider_name)
    return ExtendedLLMProviderFactory.create(provider_enum, **kwargs)
