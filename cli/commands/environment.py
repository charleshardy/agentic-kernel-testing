"""Environment management commands."""

import click
from cli.utils import (
    get_client, handle_api_error, print_table, print_json,
    format_bytes, confirm_action, validate_architecture
)


@click.group(name='env')
def env_group():
    """Test environment management commands."""
    pass


@env_group.command()
@click.option('--page', default=1, help='Page number')
@click.option('--page-size', default=20, help='Items per page')
@click.option('--status-filter', help='Filter by status (idle, busy, provisioning, error)')
@click.option('--architecture', help='Filter by architecture')
@click.option('--virtual/--physical', 'is_virtual', default=None, help='Filter by virtual/physical')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list(ctx, page, page_size, status_filter, architecture, is_virtual, output_format):
    """List available test environments."""
    
    try:
        client = get_client(ctx)
        result = client.list_environments(
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            architecture=architecture,
            is_virtual=is_virtual
        )
        
        environments = result.get('results', [])
        pagination = result.get('pagination', {})
        
        if output_format == 'json':
            print_json(result)
            return
        
        if not environments:
            click.echo("No environments found")
            return
        
        # Format table
        headers = ['ID', 'Status', 'Architecture', 'Memory', 'Type', 'Created', 'Last Used']
        rows = []
        
        for env in environments:
            config = env.get('config', {})
            env_type = 'Virtual' if config.get('is_virtual', True) else 'Physical'
            memory = f"{config.get('memory_mb', 0)}MB"
            
            rows.append([
                env['id'][:12] + '...',
                env['status'].upper(),
                config.get('architecture', 'N/A'),
                memory,
                env_type,
                env['created_at'][:19],
                env.get('last_used', 'Never')[:19] if env.get('last_used') else 'Never'
            ])
        
        print_table(headers, rows)
        
        # Show pagination info
        if pagination:
            click.echo(f"\nPage {pagination.get('current_page', page)} of {pagination.get('total_pages', 1)}")
            click.echo(f"Total: {pagination.get('total_items', len(environments))} environments")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@env_group.command()
@click.argument('env_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def show(ctx, env_id, output_format):
    """Show detailed environment information."""
    
    try:
        client = get_client(ctx)
        env = client.get_environment(env_id)
        
        if output_format == 'json':
            print_json(env)
            return
        
        # Display environment details
        click.echo(f"Environment: {env['id']}")
        click.echo("=" * 60)
        click.echo(f"Status: {env['status'].upper()}")
        click.echo(f"Created: {env['created_at']}")
        click.echo(f"Last Used: {env.get('last_used', 'Never')}")
        
        # Hardware configuration
        config = env.get('config', {})
        click.echo(f"\nHardware Configuration:")
        click.echo(f"  Architecture: {config.get('architecture', 'N/A')}")
        click.echo(f"  CPU Model: {config.get('cpu_model', 'N/A')}")
        click.echo(f"  Memory: {config.get('memory_mb', 0)}MB")
        click.echo(f"  Storage Type: {config.get('storage_type', 'N/A')}")
        click.echo(f"  Type: {'Virtual' if config.get('is_virtual', True) else 'Physical'}")
        
        if config.get('emulator'):
            click.echo(f"  Emulator: {config['emulator']}")
        
        # Peripherals
        peripherals = config.get('peripherals', [])
        if peripherals:
            click.echo(f"  Peripherals:")
            for peripheral in peripherals:
                click.echo(f"    • {peripheral.get('name', 'Unknown')}: {peripheral.get('type', 'N/A')}")
        
        # Network info
        if env.get('ip_address'):
            click.echo(f"\nNetwork:")
            click.echo(f"  IP Address: {env['ip_address']}")
        
        # Current kernel
        if env.get('kernel_version'):
            click.echo(f"\nKernel:")
            click.echo(f"  Version: {env['kernel_version']}")
        
        # Usage statistics
        stats = env.get('statistics', {})
        if stats:
            click.echo(f"\nUsage Statistics:")
            click.echo(f"  Total Tests Run: {stats.get('total_tests', 0)}")
            click.echo(f"  Successful Tests: {stats.get('successful_tests', 0)}")
            click.echo(f"  Failed Tests: {stats.get('failed_tests', 0)}")
            click.echo(f"  Total Runtime: {stats.get('total_runtime', 0):.1f}s")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@env_group.command()
@click.option('--architecture', required=True, callback=lambda c, p, v: validate_architecture(v), help='CPU architecture (x86_64, arm64, riscv64, arm)')
@click.option('--cpu-model', default='generic', help='CPU model name')
@click.option('--memory', default=2048, help='Memory in MB')
@click.option('--storage-type', default='ssd', help='Storage type')
@click.option('--virtual/--physical', default=True, help='Create virtual or physical environment')
@click.option('--emulator', help='Emulator type (qemu, kvm)')
@click.option('--dry-run', is_flag=True, help='Show what would be created without actually creating')
@click.pass_context
def create(ctx, architecture, cpu_model, memory, storage_type, virtual, emulator, dry_run):
    """Create a new test environment."""
    
    hardware_config = {
        "architecture": architecture,
        "cpu_model": cpu_model,
        "memory_mb": memory,
        "storage_type": storage_type,
        "peripherals": [],
        "is_virtual": virtual
    }
    
    if emulator:
        hardware_config["emulator"] = emulator
    
    if dry_run:
        click.echo("Would create environment with configuration:")
        print_json(hardware_config)
        return
    
    try:
        client = get_client(ctx)
        result = client.create_environment(hardware_config)
        
        click.echo("✅ Environment created successfully")
        click.echo(f"Environment ID: {result['id']}")
        click.echo(f"Status: {result['status']}")
        click.echo(f"Architecture: {result['config']['architecture']}")
        click.echo(f"Memory: {result['config']['memory_mb']}MB")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@env_group.command()
@click.argument('env_id')
@click.option('--force', is_flag=True, help='Force deletion even if environment is busy')
@click.pass_context
def delete(ctx, env_id, force):
    """Delete a test environment."""
    
    if not force:
        if not confirm_action(f"Delete environment {env_id}?"):
            click.echo("Deletion cancelled")
            return
    
    try:
        client = get_client(ctx)
        client.delete_environment(env_id, force=force)
        click.echo(f"✅ Environment {env_id} deleted successfully")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@env_group.command()
@click.argument('env_id')
@click.pass_context
def reset(ctx, env_id):
    """Reset an environment to clean state."""
    
    try:
        client = get_client(ctx)
        result = client.reset_environment(env_id)
        
        click.echo(f"✅ Environment {env_id} reset successfully")
        click.echo(f"Status: {result['status']}")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@env_group.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def stats(ctx, output_format):
    """Show environment statistics."""
    
    try:
        client = get_client(ctx)
        stats = client.get_environment_stats()
        
        if output_format == 'json':
            print_json(stats)
            return
        
        click.echo("Environment Statistics")
        click.echo("=" * 40)
        
        # Overall stats
        click.echo(f"📊 Overall:")
        click.echo(f"  Total Environments: {stats.get('total_environments', 0)}")
        click.echo(f"  Available: {stats.get('available_environments', 0)}")
        click.echo(f"  Busy: {stats.get('busy_environments', 0)}")
        click.echo(f"  Idle: {stats.get('idle_environments', 0)}")
        click.echo(f"  Error State: {stats.get('error_environments', 0)}")
        
        # By architecture
        by_arch = stats.get('by_architecture', {})
        if by_arch:
            click.echo(f"\n🏗️  By Architecture:")
            for arch, count in by_arch.items():
                click.echo(f"  {arch}: {count}")
        
        # By type
        virtual_count = stats.get('virtual_environments', 0)
        physical_count = stats.get('physical_environments', 0)
        if virtual_count or physical_count:
            click.echo(f"\n💻 By Type:")
            click.echo(f"  Virtual: {virtual_count}")
            click.echo(f"  Physical: {physical_count}")
        
        # Resource utilization
        resource_usage = stats.get('resource_usage', {})
        if resource_usage:
            click.echo(f"\n⚡ Resource Usage:")
            total_memory = resource_usage.get('total_memory_mb', 0)
            used_memory = resource_usage.get('used_memory_mb', 0)
            click.echo(f"  Memory: {format_bytes(used_memory * 1024 * 1024)} / {format_bytes(total_memory * 1024 * 1024)}")
            
            if resource_usage.get('cpu_cores'):
                click.echo(f"  CPU Cores: {resource_usage.get('used_cpu_cores', 0)} / {resource_usage['cpu_cores']}")
        
        # Performance metrics
        perf_metrics = stats.get('performance_metrics', {})
        if perf_metrics:
            click.echo(f"\n🚀 Performance:")
            click.echo(f"  Avg Provisioning Time: {perf_metrics.get('avg_provisioning_time', 0):.1f}s")
            click.echo(f"  Avg Test Execution Time: {perf_metrics.get('avg_execution_time', 0):.1f}s")
            click.echo(f"  Environment Uptime: {perf_metrics.get('avg_uptime', 0):.1f}s")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@env_group.command()
@click.option('--idle-only', is_flag=True, help='Clean up only idle environments')
@click.option('--older-than', type=int, help='Clean up environments older than N hours')
@click.option('--dry-run', is_flag=True, help='Show what would be cleaned up without actually doing it')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def cleanup(ctx, idle_only, older_than, dry_run, force):
    """Clean up unused environments."""
    
    if not dry_run and not force:
        action = "idle environments" if idle_only else "all unused environments"
        if older_than:
            action += f" older than {older_than} hours"
        
        if not confirm_action(f"Clean up {action}?"):
            click.echo("Cleanup cancelled")
            return
    
    try:
        # Get list of environments to clean up
        client = get_client(ctx)
        result = client.list_environments(page_size=100)
        environments = result.get('results', [])
        
        to_cleanup = []
        
        for env in environments:
            should_cleanup = False
            
            if idle_only and env['status'] == 'idle':
                should_cleanup = True
            elif not idle_only and env['status'] in ['idle', 'error']:
                should_cleanup = True
            
            if should_cleanup and older_than:
                # Check if environment is older than specified hours
                from datetime import datetime, timedelta
                try:
                    created_at = datetime.fromisoformat(env['created_at'].replace('Z', '+00:00'))
                    cutoff_time = datetime.now(created_at.tzinfo) - timedelta(hours=older_than)
                    if created_at > cutoff_time:
                        should_cleanup = False
                except:
                    pass  # Skip if we can't parse the date
            
            if should_cleanup:
                to_cleanup.append(env)
        
        if not to_cleanup:
            click.echo("No environments to clean up")
            return
        
        if dry_run:
            click.echo(f"Would clean up {len(to_cleanup)} environments:")
            for env in to_cleanup:
                click.echo(f"  • {env['id'][:12]}... ({env['status']}) - {env['config']['architecture']}")
            return
        
        # Perform cleanup
        cleaned_count = 0
        error_count = 0
        
        for env in to_cleanup:
            try:
                client.delete_environment(env['id'], force=True)
                cleaned_count += 1
                click.echo(f"✅ Cleaned up {env['id'][:12]}...")
            except Exception as e:
                error_count += 1
                click.echo(f"❌ Failed to clean up {env['id'][:12]}...: {e}")
        
        click.echo(f"\n✅ Cleanup completed")
        click.echo(f"Cleaned up: {cleaned_count} environments")
        if error_count > 0:
            click.echo(f"Errors: {error_count} environments")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@env_group.command()
@click.option('--architecture', help='Filter by architecture')
@click.option('--min-memory', type=int, help='Minimum memory in MB')
@click.option('--virtual/--physical', 'is_virtual', default=None, help='Filter by virtual/physical')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def available(ctx, architecture, min_memory, is_virtual, output_format):
    """Show available environments for testing."""
    
    try:
        client = get_client(ctx)
        result = client.list_environments(
            status_filter='idle',
            architecture=architecture,
            is_virtual=is_virtual,
            page_size=100
        )
        
        environments = result.get('results', [])
        
        # Filter by memory if specified
        if min_memory:
            environments = [env for env in environments 
                         if env.get('config', {}).get('memory_mb', 0) >= min_memory]
        
        if output_format == 'json':
            print_json({'available_environments': environments})
            return
        
        if not environments:
            click.echo("No available environments found")
            return
        
        click.echo(f"Available Environments ({len(environments)})")
        click.echo("=" * 50)
        
        # Group by architecture
        by_arch = {}
        for env in environments:
            arch = env.get('config', {}).get('architecture', 'unknown')
            if arch not in by_arch:
                by_arch[arch] = []
            by_arch[arch].append(env)
        
        for arch, arch_envs in by_arch.items():
            click.echo(f"\n🏗️  {arch.upper()} ({len(arch_envs)} available):")
            
            for env in arch_envs:
                config = env.get('config', {})
                env_type = 'Virtual' if config.get('is_virtual', True) else 'Physical'
                memory = config.get('memory_mb', 0)
                
                click.echo(f"  • {env['id'][:12]}... - {memory}MB {env_type}")
                if config.get('emulator'):
                    click.echo(f"    Emulator: {config['emulator']}")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))