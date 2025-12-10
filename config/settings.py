"""System-wide configuration settings."""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseModel):
    """LLM API configuration."""
    
    provider: str = Field(default="openai", description="LLM provider (openai, anthropic)")
    api_key: Optional[str] = Field(default=None, description="API key for LLM provider")
    model: str = Field(default="gpt-4", description="Model name to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=2000, description="Maximum tokens for generation")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    type: str = Field(default="sqlite", description="Database type (sqlite, postgresql)")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="agentic_testing", description="Database name")
    user: Optional[str] = Field(default=None, description="Database user")
    password: Optional[str] = Field(default=None, description="Database password")
    
    @property
    def connection_string(self) -> str:
        """Generate database connection string."""
        if self.type == "sqlite":
            return f"sqlite:///{self.name}.db"
        elif self.type == "postgresql":
            auth = f"{self.user}:{self.password}@" if self.user and self.password else ""
            return f"postgresql://{auth}{self.host}:{self.port}/{self.name}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


class ExecutionConfig(BaseModel):
    """Test execution configuration."""
    
    max_parallel_tests: int = Field(default=10, description="Maximum parallel test executions")
    test_timeout: int = Field(default=300, description="Test timeout in seconds")
    virtual_env_enabled: bool = Field(default=True, description="Enable virtual environments")
    physical_hw_enabled: bool = Field(default=False, description="Enable physical hardware")
    qemu_path: str = Field(default="/usr/bin/qemu-system-x86_64", description="QEMU binary path")
    artifact_dir: Path = Field(default=Path("./artifacts"), description="Artifact storage directory")


class CoverageConfig(BaseModel):
    """Coverage analysis configuration."""
    
    enabled: bool = Field(default=True, description="Enable coverage collection")
    gcov_path: str = Field(default="/usr/bin/gcov", description="gcov binary path")
    lcov_path: str = Field(default="/usr/bin/lcov", description="lcov binary path")
    min_line_coverage: float = Field(default=0.7, description="Minimum line coverage threshold")
    min_branch_coverage: float = Field(default=0.6, description="Minimum branch coverage threshold")


class SecurityConfig(BaseModel):
    """Security testing configuration."""
    
    fuzzing_enabled: bool = Field(default=True, description="Enable fuzzing")
    static_analysis_enabled: bool = Field(default=True, description="Enable static analysis")
    syzkaller_path: Optional[str] = Field(default=None, description="Syzkaller binary path")
    coccinelle_path: Optional[str] = Field(default=None, description="Coccinelle binary path")
    max_fuzz_time: int = Field(default=3600, description="Maximum fuzzing time in seconds")


class PerformanceConfig(BaseModel):
    """Performance testing configuration."""
    
    enabled: bool = Field(default=True, description="Enable performance testing")
    regression_threshold: float = Field(default=0.1, description="Performance regression threshold (10%)")
    benchmark_iterations: int = Field(default=5, description="Number of benchmark iterations")


class NotificationConfig(BaseModel):
    """Notification configuration."""
    
    enabled: bool = Field(default=True, description="Enable notifications")
    email_enabled: bool = Field(default=False, description="Enable email notifications")
    slack_enabled: bool = Field(default=False, description="Enable Slack notifications")
    slack_webhook_url: Optional[str] = Field(default=None, description="Slack webhook URL")
    email_smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    email_smtp_port: int = Field(default=587, description="SMTP port")
    email_from: Optional[str] = Field(default=None, description="From email address")


class APIConfig(BaseModel):
    """API server configuration."""
    
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    debug: bool = Field(default=False, description="API debug mode")
    secret_key: str = Field(default="your-secret-key-change-in-production", description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    token_expire_hours: int = Field(default=24, description="Token expiration in hours")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=1000, description="Requests per hour limit")
    max_request_size: int = Field(default=10485760, description="Max request size in bytes (10MB)")
    docs_enabled: bool = Field(default=True, description="Enable API documentation")


class Settings(BaseSettings):
    """Main application settings."""
    
    # General settings
    app_name: str = Field(default="Agentic AI Testing System", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Component configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    coverage: CoverageConfig = Field(default_factory=CoverageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    
    # CI/CD integration
    vcs_webhook_secret: Optional[str] = Field(default=None, description="VCS webhook secret")
    github_token: Optional[str] = Field(default=None, description="GitHub API token")
    gitlab_token: Optional[str] = Field(default=None, description="GitLab API token")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
