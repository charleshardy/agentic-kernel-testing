"""Configuration management commands."""

import click
import os
from pathlib import Path

from cli.utils import (
    print_json, print_yaml, load_config_file, save_config_file,
    confirm_action, prompt_for_input, select_from_list
)
from config.settings import get_settings, reload_settings


@click.group(name='config')
def config_group():
    """Configuration management commands."""
    pass


@config_group.command()
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml', 'table']), default='table', help='Output format')
@click.pass_context
def show(ctx, output_format):
    """Show current configuration."""
    
    try:
        settings = get_settings()
        
        if output_format == 'json':
            # Convert to dict for JSON serialization
            config_dict = settings.dict()
            print_json(config_dict)
            return
        elif output_format == 'yaml':
            config_dict = settings.dict()
            print_yaml(config_dict)
            return
        
        # Table format
        click.echo("Current Configuration")
        click.echo("=" * 50)
        
        # General settings
        click.echo(f"🔧 General:")
        click.echo(f"  App Name: {settings.app_name}")
        click.echo(f"  Debug Mode: {settings.debug}")
        click.echo(f"  Log Level: {settings.log_level}")
        
        # API settings
        click.echo(f"\n🌐 API Server:")
        click.echo(f"  Host: {settings.api.host}")
        click.echo(f"  Port: {settings.api.port}")
        click.echo(f"  Debug: {settings.api.debug}")
        click.echo(f"  CORS Origins: {', '.join(settings.api.cors_origins)}")
        
        # Database settings
        click.echo(f"\n💾 Database:")
        click.echo(f"  Type: {settings.database.type}")
        click.echo(f"  Host: {settings.database.host}")
        click.echo(f"  Port: {settings.database.port}")
        click.echo(f"  Database: {settings.database.name}")
        click.echo(f"  User: {settings.database.user or 'N/A'}")
        
        # LLM settings
        click.echo(f"\n🤖 LLM:")
        click.echo(f"  Provider: {settings.llm.provider}")
        click.echo(f"  Model: {settings.llm.model}")
        click.echo(f"  Temperature: {settings.llm.temperature}")
        click.echo(f"  Max Tokens: {settings.llm.max_tokens}")
        click.echo(f"  API Key: {'***' if settings.llm.api_key else 'Not set'}")
        
        # Execution settings
        click.echo(f"\n⚡ Execution:")
        click.echo(f"  Max Parallel Tests: {settings.execution.max_parallel_tests}")
        click.echo(f"  Test Timeout: {settings.execution.test_timeout}s")
        click.echo(f"  Virtual Env Enabled: {settings.execution.virtual_env_enabled}")
        click.echo(f"  Physical HW Enabled: {settings.execution.physical_hw_enabled}")
        
        # Coverage settings
        click.echo(f"\n📊 Coverage:")
        click.echo(f"  Enabled: {settings.coverage.enabled}")
        click.echo(f"  Min Line Coverage: {settings.coverage.min_line_coverage:.1%}")
        click.echo(f"  Min Branch Coverage: {settings.coverage.min_branch_coverage:.1%}")
        
        # Security settings
        click.echo(f"\n🔒 Security:")
        click.echo(f"  Fuzzing Enabled: {settings.security.fuzzing_enabled}")
        click.echo(f"  Static Analysis Enabled: {settings.security.static_analysis_enabled}")
        click.echo(f"  Max Fuzz Time: {settings.security.max_fuzz_time}s")
        
        # Performance settings
        click.echo(f"\n🚀 Performance:")
        click.echo(f"  Enabled: {settings.performance.enabled}")
        click.echo(f"  Regression Threshold: {settings.performance.regression_threshold:.1%}")
        click.echo(f"  Benchmark Iterations: {settings.performance.benchmark_iterations}")
        
        # Notification settings
        click.echo(f"\n📢 Notifications:")
        click.echo(f"  Enabled: {settings.notification.enabled}")
        click.echo(f"  Email Enabled: {settings.notification.email_enabled}")
        click.echo(f"  Slack Enabled: {settings.notification.slack_enabled}")
        
    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {e}", err=True)


@config_group.command()
@click.argument('key')
@click.argument('value')
@click.option('--type', 'value_type', type=click.Choice(['str', 'int', 'float', 'bool']), default='str', help='Value type')
@click.pass_context
def set(ctx, key, value, value_type):
    """Set a configuration value."""
    
    # Convert value to appropriate type
    try:
        if value_type == 'int':
            value = int(value)
        elif value_type == 'float':
            value = float(value)
        elif value_type == 'bool':
            value = value.lower() in ('true', '1', 'yes', 'on')
    except ValueError:
        click.echo(f"❌ Invalid {value_type} value: {value}", err=True)
        return
    
    # Set environment variable (this is a simple approach)
    # In a real implementation, you might want to update a config file
    env_key = key.upper().replace('.', '__')
    os.environ[env_key] = str(value)
    
    click.echo(f"✅ Set {key} = {value}")
    click.echo(f"Environment variable: {env_key}")
    click.echo("Note: Restart the application for changes to take effect")


@config_group.command()
@click.argument('key')
@click.pass_context
def get(ctx, key):
    """Get a configuration value."""
    
    try:
        settings = get_settings()
        
        # Navigate nested configuration
        parts = key.split('.')
        value = settings
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                click.echo(f"❌ Configuration key not found: {key}", err=True)
                return
        
        click.echo(f"{key} = {value}")
        
    except Exception as e:
        click.echo(f"❌ Failed to get configuration: {e}", err=True)


@config_group.command()
@click.option('--output-file', help='Output file path')
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml']), default='yaml', help='Output format')
@click.pass_context
def export(ctx, output_file, output_format):
    """Export current configuration to file."""
    
    try:
        settings = get_settings()
        config_dict = settings.dict()
        
        if not output_file:
            output_file = f"agentic_config.{output_format}"
        
        save_config_file(config_dict, output_file, output_format)
        click.echo(f"✅ Configuration exported to {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Failed to export configuration: {e}", err=True)


@config_group.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Show what would be imported without actually importing')
@click.pass_context
def import_config(ctx, config_file, dry_run):
    """Import configuration from file."""
    
    try:
        config_data = load_config_file(config_file)
        
        if dry_run:
            click.echo("Would import the following configuration:")
            print_yaml(config_data)
            return
        
        if not confirm_action(f"Import configuration from {config_file}?"):
            click.echo("Import cancelled")
            return
        
        # Convert config to environment variables
        def set_env_vars(data, prefix=''):
            for key, value in data.items():
                env_key = f"{prefix}{key}".upper()
                if isinstance(value, dict):
                    set_env_vars(value, f"{env_key}__")
                else:
                    os.environ[env_key] = str(value)
        
        set_env_vars(config_data)
        
        click.echo(f"✅ Configuration imported from {config_file}")
        click.echo("Note: Restart the application for changes to take effect")
        
    except Exception as e:
        click.echo(f"❌ Failed to import configuration: {e}", err=True)


@config_group.command()
@click.pass_context
def validate(ctx):
    """Validate current configuration."""
    
    try:
        settings = get_settings()
        
        click.echo("Validating configuration...")
        
        errors = []
        warnings = []
        
        # Validate API settings
        if settings.api.port < 1 or settings.api.port > 65535:
            errors.append("API port must be between 1 and 65535")
        
        # Validate database settings
        if settings.database.type not in ['sqlite', 'postgresql']:
            errors.append("Database type must be 'sqlite' or 'postgresql'")
        
        if settings.database.type == 'postgresql':
            if not settings.database.user:
                errors.append("PostgreSQL requires a username")
            if not settings.database.password:
                warnings.append("PostgreSQL password not set")
        
        # Validate LLM settings
        if settings.llm.provider not in ['openai', 'anthropic', 'amazon_q', 'kiro']:
            errors.append("LLM provider must be one of: openai, anthropic, amazon_q, kiro")
        
        if not settings.llm.api_key and settings.llm.provider in ['openai', 'anthropic']:
            warnings.append(f"API key not set for {settings.llm.provider}")
        
        # Validate execution settings
        if settings.execution.max_parallel_tests < 1:
            errors.append("Max parallel tests must be at least 1")
        
        if settings.execution.test_timeout < 1:
            errors.append("Test timeout must be at least 1 second")
        
        # Validate coverage settings
        if not (0 <= settings.coverage.min_line_coverage <= 1):
            errors.append("Min line coverage must be between 0 and 1")
        
        if not (0 <= settings.coverage.min_branch_coverage <= 1):
            errors.append("Min branch coverage must be between 0 and 1")
        
        # Show results
        if errors:
            click.echo("❌ Configuration validation failed:")
            for error in errors:
                click.echo(f"  • {error}")
        else:
            click.echo("✅ Configuration is valid")
        
        if warnings:
            click.echo("\n⚠️  Warnings:")
            for warning in warnings:
                click.echo(f"  • {warning}")
        
        if errors:
            ctx.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Failed to validate configuration: {e}", err=True)
        ctx.exit(1)


@config_group.command()
@click.pass_context
def reload(ctx):
    """Reload configuration from environment."""
    
    try:
        old_settings = get_settings()
        new_settings = reload_settings()
        
        click.echo("✅ Configuration reloaded")
        
        # Show what changed
        if old_settings.llm.provider != new_settings.llm.provider:
            click.echo(f"  LLM provider: {old_settings.llm.provider} → {new_settings.llm.provider}")
        
        if old_settings.api.port != new_settings.api.port:
            click.echo(f"  API port: {old_settings.api.port} → {new_settings.api.port}")
        
        if old_settings.database.type != new_settings.database.type:
            click.echo(f"  Database type: {old_settings.database.type} → {new_settings.database.type}")
        
    except Exception as e:
        click.echo(f"❌ Failed to reload configuration: {e}", err=True)


@config_group.command()
@click.pass_context
def wizard(ctx):
    """Interactive configuration wizard."""
    
    click.echo("🧙 Configuration Wizard")
    click.echo("=" * 40)
    click.echo("This wizard will help you configure the Agentic AI Testing System.")
    click.echo()
    
    config = {}
    
    try:
        # LLM Configuration
        click.echo("🤖 LLM Configuration")
        click.echo("-" * 20)
        
        providers = ['openai', 'anthropic', 'amazon_q', 'kiro']
        llm_provider = select_from_list(providers, "Select LLM provider")
        
        config['llm_provider'] = llm_provider
        
        if llm_provider in ['openai', 'anthropic']:
            api_key = prompt_for_input(f"Enter {llm_provider} API key", hide_input=True)
            config[f'{llm_provider}_api_key'] = api_key
        
        if llm_provider == 'openai':
            models = ['gpt-4', 'gpt-3.5-turbo']
            model = select_from_list(models, "Select OpenAI model")
            config['llm_model'] = model
        elif llm_provider == 'anthropic':
            models = ['claude-3-sonnet-20240229', 'claude-3-opus-20240229']
            model = select_from_list(models, "Select Anthropic model")
            config['llm_model'] = model
        
        # Database Configuration
        click.echo("\n💾 Database Configuration")
        click.echo("-" * 25)
        
        db_types = ['sqlite', 'postgresql']
        db_type = select_from_list(db_types, "Select database type")
        config['database_type'] = db_type
        
        if db_type == 'postgresql':
            config['database_host'] = prompt_for_input("Database host", default="localhost")
            config['database_port'] = prompt_for_input("Database port", default="5432")
            config['database_name'] = prompt_for_input("Database name", default="agentic_testing")
            config['database_user'] = prompt_for_input("Database user")
            config['database_password'] = prompt_for_input("Database password", hide_input=True)
        
        # Execution Configuration
        click.echo("\n⚡ Execution Configuration")
        click.echo("-" * 26)
        
        config['max_parallel_tests'] = prompt_for_input("Max parallel tests", default="10")
        config['test_timeout'] = prompt_for_input("Test timeout (seconds)", default="300")
        
        virtual_env = click.confirm("Enable virtual environments?", default=True)
        config['virtual_env_enabled'] = virtual_env
        
        physical_hw = click.confirm("Enable physical hardware testing?", default=False)
        config['physical_hw_enabled'] = physical_hw
        
        # API Configuration
        click.echo("\n🌐 API Configuration")
        click.echo("-" * 19)
        
        config['api_host'] = prompt_for_input("API host", default="0.0.0.0")
        config['api_port'] = prompt_for_input("API port", default="8000")
        
        # Show summary
        click.echo("\n📋 Configuration Summary")
        click.echo("-" * 25)
        for key, value in config.items():
            if 'password' in key or 'key' in key:
                display_value = '***'
            else:
                display_value = value
            click.echo(f"  {key}: {display_value}")
        
        if confirm_action("Apply this configuration?"):
            # Set environment variables
            for key, value in config.items():
                env_key = key.upper()
                os.environ[env_key] = str(value)
            
            click.echo("✅ Configuration applied")
            click.echo("Note: Restart the application for changes to take effect")
        else:
            click.echo("Configuration cancelled")
        
    except (KeyboardInterrupt, click.Abort):
        click.echo("\nConfiguration wizard cancelled")


@config_group.command()
@click.pass_context
def reset(ctx):
    """Reset configuration to defaults."""
    
    if not confirm_action("Reset all configuration to defaults? This cannot be undone."):
        click.echo("Reset cancelled")
        return
    
    try:
        # Clear relevant environment variables
        env_vars_to_clear = []
        for key in os.environ:
            if key.startswith(('LLM_', 'DATABASE_', 'API_', 'EXECUTION_', 'COVERAGE_', 'SECURITY_', 'PERFORMANCE_', 'NOTIFICATION_')):
                env_vars_to_clear.append(key)
        
        for var in env_vars_to_clear:
            del os.environ[var]
        
        click.echo(f"✅ Reset {len(env_vars_to_clear)} configuration variables")
        click.echo("Configuration has been reset to defaults")
        click.echo("Note: Restart the application for changes to take effect")
        
    except Exception as e:
        click.echo(f"❌ Failed to reset configuration: {e}", err=True)