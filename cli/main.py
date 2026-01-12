#!/usr/bin/env python3
"""Main CLI entry point for the Agentic AI Testing System."""

import click
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli.commands.test import test_group
from cli.commands.status import status_group
from cli.commands.results import results_group
from cli.commands.config import config_group
from cli.commands.environment import env_group
from cli.commands.interactive import interactive_group
from cli.commands.spec import spec_group, req_group, generate_group, run_group, report_group
from cli.utils import setup_logging, get_client, handle_api_error
from config.settings import get_settings


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config-file', help='Path to configuration file')
@click.option('--api-url', help='API server URL (overrides config)')
@click.option('--api-key', help='API key for authentication')
@click.pass_context
def cli(ctx, debug, config_file, api_url, api_key):
    """Agentic AI Testing System - Command Line Interface
    
    A comprehensive CLI for managing kernel and BSP testing workflows.
    
    Examples:
        # Submit a test
        agentic-test test submit --name "Memory test" --type unit --subsystem mm
        
        # Check test status
        agentic-test status plan <plan-id>
        
        # View results
        agentic-test results list --failed-only
        
        # Interactive mode
        agentic-test interactive
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Setup logging
    setup_logging(debug)
    
    # Store global options in context
    ctx.obj['debug'] = debug
    ctx.obj['config_file'] = config_file
    ctx.obj['api_url'] = api_url
    ctx.obj['api_key'] = api_key
    
    # Load settings
    try:
        settings = get_settings()
        ctx.obj['settings'] = settings
    except Exception as e:
        if debug:
            click.echo(f"Warning: Failed to load settings: {e}", err=True)


# Add command groups
cli.add_command(test_group)
cli.add_command(status_group)
cli.add_command(results_group)
cli.add_command(config_group)
cli.add_command(env_group)
cli.add_command(interactive_group)
cli.add_command(spec_group)
cli.add_command(req_group)
cli.add_command(generate_group)
cli.add_command(run_group, name='run')
cli.add_command(report_group)


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    from cli import __version__
    
    click.echo(f"Agentic AI Testing System CLI v{__version__}")
    
    try:
        client = get_client(ctx)
        health = client.health_check()
        api_version = health.get('version', 'unknown')
        click.echo(f"API Server: v{api_version}")
    except Exception as e:
        if ctx.obj.get('debug'):
            click.echo(f"API Server: unavailable ({e})")
        else:
            click.echo("API Server: unavailable")


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health."""
    try:
        client = get_client(ctx)
        health_data = client.health_check()
        
        status = health_data.get('status', 'unknown')
        if status == 'healthy':
            click.echo("✅ System is healthy")
        else:
            click.echo("❌ System is unhealthy")
        
        click.echo(f"Status: {status}")
        click.echo(f"Version: {health_data.get('version', 'unknown')}")
        click.echo(f"Uptime: {health_data.get('uptime', 0):.1f}s")
        
        # Show component status
        components = health_data.get('components', {})
        if components:
            click.echo("\nComponents:")
            for name, info in components.items():
                status_icon = "✅" if info.get('status') == 'healthy' else "❌"
                click.echo(f"  {status_icon} {name}: {info.get('status', 'unknown')}")
        
        # Show metrics
        metrics = health_data.get('metrics', {})
        if metrics:
            click.echo("\nMetrics:")
            click.echo(f"  Active tests: {metrics.get('active_tests', 0)}")
            click.echo(f"  Queued tests: {metrics.get('queued_tests', 0)}")
            click.echo(f"  Available environments: {metrics.get('available_environments', 0)}")
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


if __name__ == '__main__':
    cli()