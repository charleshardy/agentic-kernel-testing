"""LLM provider abstraction layer for unified interface across multiple providers."""

import time
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any]


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """Initialize LLM provider.
        
        Args:
            api_key: API key for the provider
            model: Model name to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens for generation
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion from prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    def generate_with_retry(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate with exponential backoff retry logic.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return self.generate(prompt, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    raise last_exception


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        **kwargs
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (gpt-4, gpt-3.5-turbo, etc.)
            **kwargs: Additional parameters for BaseLLMProvider
        """
        super().__init__(api_key=api_key or os.getenv("OPENAI_API_KEY"), model=model, **kwargs)
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout)
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using OpenAI API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            tokens_used=response.usage.total_tokens,
            finish_reason=response.choices[0].finish_reason,
            metadata={"id": response.id}
        )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        **kwargs
    ):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model name (claude-3-opus, claude-3-sonnet, etc.)
            **kwargs: Additional parameters for BaseLLMProvider
        """
        super().__init__(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"), model=model, **kwargs)
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Anthropic API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional Anthropic-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            messages=[{"role": "user", "content": prompt}]
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason,
            metadata={"id": response.id}
        )


class BedrockProvider(BaseLLMProvider):
    """Amazon Bedrock API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1",
        **kwargs
    ):
        """Initialize Bedrock provider.
        
        Args:
            api_key: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            model: Model ID (e.g., anthropic.claude-3-sonnet-20240229-v1:0)
            region: AWS region
            **kwargs: Additional parameters for BaseLLMProvider
        """
        super().__init__(api_key=api_key or os.getenv("AWS_ACCESS_KEY_ID"), model=model, **kwargs)
        self.region = region
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        try:
            import boto3
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=self.api_key,
                aws_secret_access_key=self.secret_key
            )
        except ImportError:
            raise ImportError("boto3 package not installed. Install with: pip install boto3")
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Amazon Bedrock API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional Bedrock-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        import json
        
        # Format request based on model family
        if "anthropic" in self.model:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "messages": [{"role": "user", "content": prompt}]
            })
        elif "amazon.titan" in self.model:
            body = json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", self.temperature),
                }
            })
        else:
            raise ValueError(f"Unsupported Bedrock model: {self.model}")
        
        response = self.client.invoke_model(
            modelId=self.model,
            body=body
        )
        
        response_body = json.loads(response["body"].read())
        
        # Parse response based on model family
        if "anthropic" in self.model:
            content = response_body["content"][0]["text"]
            tokens_used = response_body["usage"]["input_tokens"] + response_body["usage"]["output_tokens"]
            finish_reason = response_body["stop_reason"]
        elif "amazon.titan" in self.model:
            content = response_body["results"][0]["outputText"]
            tokens_used = response_body["inputTextTokenCount"] + response_body["results"][0]["tokenCount"]
            finish_reason = response_body["results"][0]["completionReason"]
        else:
            raise ValueError(f"Unsupported Bedrock model: {self.model}")
        
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            metadata={"request_id": response["ResponseMetadata"]["RequestId"]}
        )


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create(
        provider: LLMProvider,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """Create an LLM provider instance.
        
        Args:
            provider: Provider type
            api_key: API key for the provider
            model: Model name (uses provider default if not specified)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider == LLMProvider.OPENAI:
            return OpenAIProvider(api_key=api_key, model=model or "gpt-4", **kwargs)
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicProvider(api_key=api_key, model=model or "claude-3-5-sonnet-20241022", **kwargs)
        elif provider == LLMProvider.BEDROCK:
            return BedrockProvider(api_key=api_key, model=model or "anthropic.claude-3-sonnet-20240229-v1:0", **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
