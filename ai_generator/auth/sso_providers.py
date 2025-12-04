"""SSO authentication providers for Amazon Q and Kiro.

This module provides Single Sign-On (SSO) authentication support for:
- Amazon Q Developer (via AWS SSO/IAM Identity Center)
- Kiro AI (via OAuth2/OIDC)
"""

import os
import json
import time
import webbrowser
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests


@dataclass
class SSOToken:
    """SSO authentication token."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    token_type: str = "Bearer"
    scope: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "token_type": self.token_type,
            "scope": self.scope
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SSOToken':
        """Create from dictionary."""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope")
        )


class BaseSSOProvider(ABC):
    """Base class for SSO providers."""
    
    def __init__(self, token_cache_path: Optional[str] = None):
        """Initialize SSO provider.
        
        Args:
            token_cache_path: Path to cache tokens (default: ~/.kiro/sso_tokens.json)
        """
        self.token_cache_path = token_cache_path or os.path.expanduser(
            "~/.kiro/sso_tokens.json"
        )
        self._token: Optional[SSOToken] = None
    
    @abstractmethod
    def authenticate(self) -> SSOToken:
        """Perform SSO authentication.
        
        Returns:
            SSOToken with access credentials
        """
        pass
    
    @abstractmethod
    def refresh_token(self, token: SSOToken) -> SSOToken:
        """Refresh an expired token.
        
        Args:
            token: Expired token to refresh
            
        Returns:
            New SSOToken
        """
        pass
    
    def get_token(self, force_refresh: bool = False) -> SSOToken:
        """Get valid token, refreshing if necessary.
        
        Args:
            force_refresh: Force token refresh even if not expired
            
        Returns:
            Valid SSOToken
        """
        # Try to load cached token
        if not self._token and not force_refresh:
            self._token = self._load_cached_token()
        
        # Check if token needs refresh
        if self._token and (force_refresh or self._token.is_expired()):
            try:
                self._token = self.refresh_token(self._token)
                self._cache_token(self._token)
            except Exception:
                # If refresh fails, re-authenticate
                self._token = None
        
        # Authenticate if no valid token
        if not self._token:
            self._token = self.authenticate()
            self._cache_token(self._token)
        
        return self._token
    
    def _cache_token(self, token: SSOToken) -> None:
        """Cache token to disk.
        
        Args:
            token: Token to cache
        """
        try:
            os.makedirs(os.path.dirname(self.token_cache_path), exist_ok=True)
            
            # Load existing cache
            cache = {}
            if os.path.exists(self.token_cache_path):
                with open(self.token_cache_path, 'r') as f:
                    cache = json.load(f)
            
            # Update cache for this provider
            provider_name = self.__class__.__name__
            cache[provider_name] = token.to_dict()
            
            # Save cache
            with open(self.token_cache_path, 'w') as f:
                json.dump(cache, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.token_cache_path, 0o600)
            
        except Exception as e:
            print(f"Warning: Failed to cache token: {e}")
    
    def _load_cached_token(self) -> Optional[SSOToken]:
        """Load cached token from disk.
        
        Returns:
            Cached SSOToken or None
        """
        try:
            if not os.path.exists(self.token_cache_path):
                return None
            
            with open(self.token_cache_path, 'r') as f:
                cache = json.load(f)
            
            provider_name = self.__class__.__name__
            if provider_name not in cache:
                return None
            
            return SSOToken.from_dict(cache[provider_name])
            
        except Exception:
            return None
    
    def clear_cache(self) -> None:
        """Clear cached token."""
        try:
            if os.path.exists(self.token_cache_path):
                with open(self.token_cache_path, 'r') as f:
                    cache = json.load(f)
                
                provider_name = self.__class__.__name__
                if provider_name in cache:
                    del cache[provider_name]
                
                with open(self.token_cache_path, 'w') as f:
                    json.dump(cache, f, indent=2)
        except Exception:
            pass


class AmazonQSSOProvider(BaseSSOProvider):
    """AWS SSO provider for Amazon Q Developer.
    
    Supports authentication via:
    - AWS IAM Identity Center (AWS SSO)
    - AWS CLI SSO profiles
    - Device code flow for CLI authentication
    """
    
    def __init__(
        self,
        sso_start_url: Optional[str] = None,
        sso_region: Optional[str] = None,
        sso_account_id: Optional[str] = None,
        sso_role_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        **kwargs
    ):
        """Initialize Amazon Q SSO provider.
        
        Args:
            sso_start_url: AWS SSO start URL (e.g., https://my-sso.awsapps.com/start)
            sso_region: AWS SSO region
            sso_account_id: AWS account ID
            sso_role_name: IAM role name
            profile_name: AWS CLI profile name (alternative to explicit config)
            **kwargs: Additional parameters for BaseSSOProvider
        """
        super().__init__(**kwargs)
        self.sso_start_url = sso_start_url or os.getenv("AWS_SSO_START_URL")
        self.sso_region = sso_region or os.getenv("AWS_SSO_REGION", "us-east-1")
        self.sso_account_id = sso_account_id or os.getenv("AWS_SSO_ACCOUNT_ID")
        self.sso_role_name = sso_role_name or os.getenv("AWS_SSO_ROLE_NAME")
        self.profile_name = profile_name or os.getenv("AWS_PROFILE")
        
        try:
            import boto3
            self.boto3 = boto3
        except ImportError:
            raise ImportError("boto3 required for AWS SSO. Install with: pip install boto3")
    
    def authenticate(self) -> SSOToken:
        """Authenticate via AWS SSO.
        
        Returns:
            SSOToken with AWS credentials
        """
        # Try AWS CLI profile first
        if self.profile_name:
            return self._authenticate_with_profile()
        
        # Otherwise use device code flow
        return self._authenticate_with_device_code()
    
    def _authenticate_with_profile(self) -> SSOToken:
        """Authenticate using AWS CLI profile.
        
        Returns:
            SSOToken with credentials from profile
        """
        try:
            session = self.boto3.Session(profile_name=self.profile_name)
            credentials = session.get_credentials()
            
            if not credentials:
                raise ValueError(f"No credentials found for profile: {self.profile_name}")
            
            # Get frozen credentials
            frozen = credentials.get_frozen_credentials()
            
            return SSOToken(
                access_token=frozen.access_key,
                refresh_token=frozen.secret_key,
                token_type="AWS4-HMAC-SHA256",
                scope="aws"
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to authenticate with AWS profile: {e}")
    
    def _authenticate_with_device_code(self) -> SSOToken:
        """Authenticate using device code flow.
        
        Returns:
            SSOToken with credentials from device code flow
        """
        if not self.sso_start_url:
            raise ValueError(
                "AWS SSO start URL required. Set AWS_SSO_START_URL or pass sso_start_url"
            )
        
        try:
            # Create SSO OIDC client
            sso_oidc = self.boto3.client('sso-oidc', region_name=self.sso_region)
            
            # Register client
            client_response = sso_oidc.register_client(
                clientName='agentic-testing-system',
                clientType='public'
            )
            
            client_id = client_response['clientId']
            client_secret = client_response['clientSecret']
            
            # Start device authorization
            device_response = sso_oidc.start_device_authorization(
                clientId=client_id,
                clientSecret=client_secret,
                startUrl=self.sso_start_url
            )
            
            # Display instructions to user
            print("\n" + "=" * 70)
            print("AWS SSO Authentication Required")
            print("=" * 70)
            print(f"\nPlease visit: {device_response['verificationUriComplete']}")
            print(f"And enter code: {device_response['userCode']}")
            print("\nOpening browser...")
            
            # Open browser
            webbrowser.open(device_response['verificationUriComplete'])
            
            # Poll for token
            device_code = device_response['deviceCode']
            interval = device_response['interval']
            expires_in = device_response['expiresIn']
            
            print("\nWaiting for authentication...")
            start_time = time.time()
            
            while time.time() - start_time < expires_in:
                time.sleep(interval)
                
                try:
                    token_response = sso_oidc.create_token(
                        clientId=client_id,
                        clientSecret=client_secret,
                        grantType='urn:ietf:params:oauth:grant-type:device_code',
                        deviceCode=device_code
                    )
                    
                    print("✓ Authentication successful!")
                    
                    expires_at = datetime.now() + timedelta(seconds=token_response['expiresIn'])
                    
                    return SSOToken(
                        access_token=token_response['accessToken'],
                        refresh_token=token_response.get('refreshToken'),
                        expires_at=expires_at,
                        token_type=token_response.get('tokenType', 'Bearer')
                    )
                    
                except sso_oidc.exceptions.AuthorizationPendingException:
                    # Still waiting for user to authorize
                    continue
                except Exception as e:
                    raise RuntimeError(f"Token creation failed: {e}")
            
            raise TimeoutError("Authentication timed out")
            
        except Exception as e:
            raise RuntimeError(f"AWS SSO authentication failed: {e}")
    
    def refresh_token(self, token: SSOToken) -> SSOToken:
        """Refresh AWS SSO token.
        
        Args:
            token: Expired token to refresh
            
        Returns:
            New SSOToken
        """
        if not token.refresh_token:
            # Re-authenticate if no refresh token
            return self.authenticate()
        
        try:
            sso_oidc = self.boto3.client('sso-oidc', region_name=self.sso_region)
            
            # This would require client_id and client_secret from original auth
            # For simplicity, re-authenticate
            return self.authenticate()
            
        except Exception:
            return self.authenticate()


class KiroSSOProvider(BaseSSOProvider):
    """OAuth2/OIDC SSO provider for Kiro AI.
    
    Supports authentication via:
    - OAuth2 authorization code flow
    - OIDC (OpenID Connect)
    - Device code flow for CLI
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        auth_url: Optional[str] = None,
        token_url: Optional[str] = None,
        redirect_uri: str = "http://localhost:8080/callback",
        scopes: Optional[list] = None,
        **kwargs
    ):
        """Initialize Kiro SSO provider.
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            auth_url: Authorization endpoint URL
            token_url: Token endpoint URL
            redirect_uri: OAuth2 redirect URI
            scopes: List of OAuth2 scopes
            **kwargs: Additional parameters for BaseSSOProvider
        """
        super().__init__(**kwargs)
        self.client_id = client_id or os.getenv("KIRO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("KIRO_CLIENT_SECRET")
        self.auth_url = auth_url or os.getenv(
            "KIRO_AUTH_URL",
            "https://auth.kiro.ai/oauth/authorize"
        )
        self.token_url = token_url or os.getenv(
            "KIRO_TOKEN_URL",
            "https://auth.kiro.ai/oauth/token"
        )
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["api", "test_generation"]
        
        if not self.client_id:
            raise ValueError(
                "Kiro client ID required. Set KIRO_CLIENT_ID or pass client_id"
            )
    
    def authenticate(self) -> SSOToken:
        """Authenticate via Kiro OAuth2.
        
        Returns:
            SSOToken with Kiro credentials
        """
        # Use device code flow for CLI
        return self._authenticate_with_device_code()
    
    def _authenticate_with_device_code(self) -> SSOToken:
        """Authenticate using device code flow.
        
        Returns:
            SSOToken with credentials
        """
        try:
            # Request device code
            device_response = requests.post(
                f"{self.auth_url.replace('/authorize', '/device/code')}",
                data={
                    "client_id": self.client_id,
                    "scope": " ".join(self.scopes)
                }
            )
            device_response.raise_for_status()
            device_data = device_response.json()
            
            # Display instructions
            print("\n" + "=" * 70)
            print("Kiro SSO Authentication Required")
            print("=" * 70)
            print(f"\nPlease visit: {device_data['verification_uri']}")
            print(f"And enter code: {device_data['user_code']}")
            print("\nOpening browser...")
            
            # Open browser
            webbrowser.open(device_data['verification_uri_complete'])
            
            # Poll for token
            device_code = device_data['device_code']
            interval = device_data.get('interval', 5)
            expires_in = device_data.get('expires_in', 300)
            
            print("\nWaiting for authentication...")
            start_time = time.time()
            
            while time.time() - start_time < expires_in:
                time.sleep(interval)
                
                token_response = requests.post(
                    self.token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                    }
                )
                
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    print("✓ Authentication successful!")
                    
                    expires_at = datetime.now() + timedelta(
                        seconds=token_data.get('expires_in', 3600)
                    )
                    
                    return SSOToken(
                        access_token=token_data['access_token'],
                        refresh_token=token_data.get('refresh_token'),
                        expires_at=expires_at,
                        token_type=token_data.get('token_type', 'Bearer'),
                        scope=token_data.get('scope')
                    )
                elif token_response.status_code == 400:
                    error = token_response.json().get('error')
                    if error == 'authorization_pending':
                        continue
                    elif error == 'slow_down':
                        interval += 5
                        continue
                    else:
                        raise RuntimeError(f"Authentication error: {error}")
            
            raise TimeoutError("Authentication timed out")
            
        except Exception as e:
            raise RuntimeError(f"Kiro SSO authentication failed: {e}")
    
    def refresh_token(self, token: SSOToken) -> SSOToken:
        """Refresh Kiro OAuth2 token.
        
        Args:
            token: Expired token to refresh
            
        Returns:
            New SSOToken
        """
        if not token.refresh_token:
            return self.authenticate()
        
        try:
            response = requests.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": token.refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            response.raise_for_status()
            
            token_data = response.json()
            expires_at = datetime.now() + timedelta(
                seconds=token_data.get('expires_in', 3600)
            )
            
            return SSOToken(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', token.refresh_token),
                expires_at=expires_at,
                token_type=token_data.get('token_type', 'Bearer'),
                scope=token_data.get('scope')
            )
            
        except Exception:
            return self.authenticate()


def get_sso_provider(provider_type: str, **kwargs) -> BaseSSOProvider:
    """Factory function to create SSO provider.
    
    Args:
        provider_type: Type of provider ("amazon_q" or "kiro")
        **kwargs: Provider-specific parameters
        
    Returns:
        Configured SSO provider
        
    Examples:
        # Amazon Q with AWS SSO
        provider = get_sso_provider(
            "amazon_q",
            sso_start_url="https://my-sso.awsapps.com/start",
            sso_region="us-east-1"
        )
        
        # Kiro with OAuth2
        provider = get_sso_provider(
            "kiro",
            client_id="your-client-id",
            client_secret="your-secret"
        )
    """
    if provider_type == "amazon_q":
        return AmazonQSSOProvider(**kwargs)
    elif provider_type == "kiro":
        return KiroSSOProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported SSO provider: {provider_type}")
