#!/usr/bin/env python3
"""Configuration validation script for Agentic AI Testing System."""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings, get_settings


class ConfigValidator:
    """Validates system configuration."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_llm_config(self, settings: Settings) -> None:
        """Validate LLM configuration."""
        llm = settings.llm
        
        if not llm.api_key:
            self.errors.append("LLM API key is required")
            
        if llm.provider not in ["openai", "anthropic", "amazon-bedrock"]:
            self.errors.append(f"Unsupported LLM provider: {llm.provider}")
            
        if llm.temperature < 0 or llm.temperature > 2:
            self.warnings.append(f"LLM temperature {llm.temperature} is outside recommended range (0-2)")
            
        if llm.max_tokens < 100:
            self.warnings.append(f"LLM max_tokens {llm.max_tokens} is very low")
            
    def validate_database_config(self, settings: Settings) -> None:
        """Validate database configuration."""
        db = settings.database
        
        if db.type not in ["sqlite", "postgresql"]:
            self.errors.append(f"Unsupported database type: {db.type}")
            
        if db.type == "postgresql":
            if not db.host:
                self.errors.append("Database host is required for PostgreSQL")
            if not db.user:
                self.errors.append("Database user is required for PostgreSQL")
            if not db.password:
                self.errors.append("Database password is required for PostgreSQL")
                
        try:
            connection_string = db.connection_string
            if not connection_string:
                self.errors.append("Invalid database connection string")
        except Exception as e:
            self.errors.append(f"Database configuration error: {e}")
            
    def validate_execution_config(self, settings: Settings) -> None:
        """Validate execution configuration."""
        exec_config = settings.execution
        
        if exec_config.max_parallel_tests < 1:
            self.errors.append("max_parallel_tests must be at least 1")
            
        if exec_config.max_parallel_tests > 100:
            self.warnings.append(f"max_parallel_tests {exec_config.max_parallel_tests} is very high")
            
        if exec_config.test_timeout < 10:
            self.warnings.append(f"test_timeout {exec_config.test_timeout}s is very low")
            
        # Check if QEMU is available when virtual environments are enabled
        if exec_config.virtual_env_enabled:
            if not Path(exec_config.qemu_path).exists():
                self.warnings.append(f"QEMU binary not found at {exec_config.qemu_path}")
                
    def validate_coverage_config(self, settings: Settings) -> None:
        """Validate coverage configuration."""
        coverage = settings.coverage
        
        if coverage.enabled:
            if not Path(coverage.gcov_path).exists():
                self.warnings.append(f"gcov binary not found at {coverage.gcov_path}")
            if not Path(coverage.lcov_path).exists():
                self.warnings.append(f"lcov binary not found at {coverage.lcov_path}")
                
        if coverage.min_line_coverage < 0 or coverage.min_line_coverage > 1:
            self.errors.append("min_line_coverage must be between 0 and 1")
            
        if coverage.min_branch_coverage < 0 or coverage.min_branch_coverage > 1:
            self.errors.append("min_branch_coverage must be between 0 and 1")
            
    def validate_security_config(self, settings: Settings) -> None:
        """Validate security configuration."""
        security = settings.security
        
        if security.fuzzing_enabled and security.syzkaller_path:
            if not Path(security.syzkaller_path).exists():
                self.warnings.append(f"Syzkaller binary not found at {security.syzkaller_path}")
                
        if security.static_analysis_enabled and security.coccinelle_path:
            if not Path(security.coccinelle_path).exists():
                self.warnings.append(f"Coccinelle binary not found at {security.coccinelle_path}")
                
        if security.max_fuzz_time < 60:
            self.warnings.append(f"max_fuzz_time {security.max_fuzz_time}s is very low")
            
    def validate_api_config(self, settings: Settings) -> None:
        """Validate API configuration."""
        api = settings.api
        
        if api.secret_key == "your-secret-key-change-in-production":
            self.errors.append("API secret key must be changed from default value")
            
        if len(api.secret_key) < 32:
            self.warnings.append("API secret key should be at least 32 characters long")
            
        if api.port < 1024 and os.getuid() != 0:
            self.warnings.append(f"API port {api.port} requires root privileges")
            
    def validate_notification_config(self, settings: Settings) -> None:
        """Validate notification configuration."""
        notif = settings.notification
        
        if notif.enabled:
            if notif.slack_enabled and not notif.slack_webhook_url:
                self.errors.append("Slack webhook URL is required when Slack notifications are enabled")
                
            if notif.email_enabled:
                if not notif.email_smtp_host:
                    self.errors.append("SMTP host is required when email notifications are enabled")
                if not notif.email_from:
                    self.errors.append("From email address is required when email notifications are enabled")
                    
    def validate_environment_variables(self) -> None:
        """Validate required environment variables."""
        required_vars = []
        
        # Check for production-specific requirements
        if os.getenv("DEBUG", "false").lower() == "false":
            required_vars.extend([
                "API__SECRET_KEY",
                "DATABASE__PASSWORD"
            ])
            
        # Check LLM provider requirements
        llm_provider = os.getenv("LLM__PROVIDER", "openai")
        if llm_provider in ["openai", "anthropic"]:
            required_vars.append("LLM__API_KEY")
            
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Required environment variable {var} is not set")
                
    def validate_file_permissions(self) -> None:
        """Validate file and directory permissions."""
        paths_to_check = [
            ("./artifacts", True),
            ("./logs", True),
            ("./coverage_data", True),
        ]
        
        for path_str, is_dir in paths_to_check:
            path = Path(path_str)
            if path.exists():
                if is_dir and not path.is_dir():
                    self.errors.append(f"{path} should be a directory")
                elif not is_dir and not path.is_file():
                    self.errors.append(f"{path} should be a file")
                    
                # Check write permissions
                if not os.access(path, os.W_OK):
                    self.errors.append(f"No write permission for {path}")
            else:
                self.warnings.append(f"Path {path} does not exist and will be created")
                
    def validate_docker_config(self) -> None:
        """Validate Docker configuration."""
        compose_file = Path("docker-compose.yml")
        if compose_file.exists():
            try:
                with open(compose_file) as f:
                    compose_config = yaml.safe_load(f)
                    
                # Check for required services
                required_services = ["api", "db", "redis"]
                services = compose_config.get("services", {})
                
                for service in required_services:
                    if service not in services:
                        self.errors.append(f"Required Docker service '{service}' not found in docker-compose.yml")
                        
            except yaml.YAMLError as e:
                self.errors.append(f"Invalid docker-compose.yml: {e}")
        else:
            self.warnings.append("docker-compose.yml not found")
            
    def validate_kubernetes_config(self) -> None:
        """Validate Kubernetes configuration."""
        k8s_dir = Path("k8s")
        if k8s_dir.exists():
            required_files = [
                "namespace.yaml",
                "configmap.yaml",
                "secrets.yaml",
                "api.yaml",
                "postgres.yaml"
            ]
            
            for filename in required_files:
                file_path = k8s_dir / filename
                if not file_path.exists():
                    self.warnings.append(f"Kubernetes manifest {filename} not found")
        else:
            self.warnings.append("Kubernetes manifests directory (k8s/) not found")
            
    def validate_all(self) -> bool:
        """Run all validations."""
        try:
            settings = get_settings()
        except Exception as e:
            self.errors.append(f"Failed to load settings: {e}")
            return False
            
        self.validate_llm_config(settings)
        self.validate_database_config(settings)
        self.validate_execution_config(settings)
        self.validate_coverage_config(settings)
        self.validate_security_config(settings)
        self.validate_api_config(settings)
        self.validate_notification_config(settings)
        self.validate_environment_variables()
        self.validate_file_permissions()
        self.validate_docker_config()
        self.validate_kubernetes_config()
        
        return len(self.errors) == 0
        
    def print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print("❌ Configuration Errors:")
            for error in self.errors:
                print(f"  - {error}")
            print()
            
        if self.warnings:
            print("⚠️  Configuration Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()
            
        if not self.errors and not self.warnings:
            print("✅ Configuration validation passed!")
        elif not self.errors:
            print("✅ Configuration validation passed with warnings")
        else:
            print("❌ Configuration validation failed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate Agentic AI Testing System configuration")
    parser.add_argument("--env-file", help="Environment file to load")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--quiet", action="store_true", help="Only show errors")
    
    args = parser.parse_args()
    
    # Load environment file if specified
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
        
    validator = ConfigValidator()
    is_valid = validator.validate_all()
    
    if args.json:
        result = {
            "valid": is_valid,
            "errors": validator.errors,
            "warnings": validator.warnings
        }
        print(json.dumps(result, indent=2))
    else:
        if not args.quiet or validator.errors:
            validator.print_results()
            
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()