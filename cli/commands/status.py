"""Status monitoring commands."""

import click
import time
from datetime import datetime

from cli.utils import (
    get_client, handle_api_error, print_table, print_json,
    format_test_status, format_duration, format_percentage,
    display_paginated_results
)


@click.group(name='status')
def status_group():
    """Test execution status monitoring commands."""
    pass


@status_group.command()
@click.argument('plan_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--watch', is_flag=True, help='Watch status updates in real-time')
@click.option('--interval', default=10, help='Update interval in seconds (for watch mode)')
@click.pass_context
def plan(ctx, plan_id, output_format, watch, interval):
    """Show execution plan status."""
    
    def show_plan_status():
        try:
            client = get_client(ctx)
            status = client.get_execution_plan_status(plan_id)
            
            if output_format == 'json':
                print_json(status)
                return
            
            # Clear screen for watch mode
            if watch:
                click.clear()
            
            click.echo(f"Execution Plan: {plan_id}")
            click.echo("=" * 60)
            click.echo(f"Submission ID: {status['submission_id']}")
            click.echo(f"Overall Status: {format_test_status(status['overall_status'])}")
            click.echo(f"Progress: {format_percentage(status['progress'])}")
            click.echo(f"Total Tests: {status['total_tests']}")
            click.echo(f"Completed: {status['completed_tests']}")
            click.echo(f"Failed: {status['failed_tests']}")
            
            if status.get('started_at'):
                click.echo(f"Started: {status['started_at']}")
            if status.get('estimated_completion'):
                click.echo(f"Est. Completion: {status['estimated_completion']}")
            if status.get('completed_at'):
                click.echo(f"Completed: {status['completed_at']}")
            
            # Show individual test statuses
            if status.get('test_statuses'):
                click.echo(f"\nTest Status Details:")
                click.echo("-" * 40)
                
                headers = ['Test ID', 'Status', 'Progress', 'Environment', 'Started']
                rows = []
                
                for test_status in status['test_statuses']:
                    rows.append([
                        test_status['test_id'][:12] + '...',
                        format_test_status(test_status['status']),
                        format_percentage(test_status['progress']),
                        test_status.get('environment_id', 'N/A')[:12],
                        test_status.get('started_at', 'N/A')[:19] if test_status.get('started_at') else 'N/A'
                    ])
                
                print_table(headers, rows)
            
            if watch:
                click.echo(f"\nLast updated: {datetime.now().strftime('%H:%M:%S')} (Press Ctrl+C to stop)")
            
        except Exception as e:
            if watch:
                click.echo(f"Error: {e}")
            else:
                handle_api_error(e, ctx.obj.get('debug', False))
    
    if watch:
        try:
            while True:
                show_plan_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            click.echo("\nStopped watching")
    else:
        show_plan_status()


@status_group.command()
@click.argument('test_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--watch', is_flag=True, help='Watch status updates in real-time')
@click.option('--interval', default=5, help='Update interval in seconds (for watch mode)')
@click.pass_context
def test(ctx, test_id, output_format, watch, interval):
    """Show individual test execution status."""
    
    def show_test_status():
        try:
            client = get_client(ctx)
            status = client.get_test_status(test_id)
            
            if output_format == 'json':
                print_json(status)
                return
            
            # Clear screen for watch mode
            if watch:
                click.clear()
            
            click.echo(f"Test: {test_id}")
            click.echo("=" * 50)
            click.echo(f"Status: {format_test_status(status['status'])}")
            click.echo(f"Progress: {format_percentage(status['progress'])}")
            
            if status.get('environment_id'):
                click.echo(f"Environment: {status['environment_id']}")
            
            if status.get('started_at'):
                click.echo(f"Started: {status['started_at']}")
                
                # Calculate elapsed time
                try:
                    start_time = datetime.fromisoformat(status['started_at'].replace('Z', '+00:00'))
                    elapsed = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
                    click.echo(f"Elapsed: {format_duration(elapsed)}")
                except:
                    pass
            
            if status.get('estimated_completion'):
                click.echo(f"Est. Completion: {status['estimated_completion']}")
            
            if status.get('message'):
                click.echo(f"Message: {status['message']}")
            
            if watch:
                click.echo(f"\nLast updated: {datetime.now().strftime('%H:%M:%S')} (Press Ctrl+C to stop)")
            
        except Exception as e:
            if watch:
                click.echo(f"Error: {e}")
            else:
                handle_api_error(e, ctx.obj.get('debug', False))
    
    if watch:
        try:
            while True:
                show_test_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            click.echo("\nStopped watching")
    else:
        show_test_status()


@status_group.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--watch', is_flag=True, help='Watch status updates in real-time')
@click.option('--interval', default=15, help='Update interval in seconds (for watch mode)')
@click.pass_context
def active(ctx, output_format, watch, interval):
    """Show all active test executions."""
    
    def show_active_executions():
        try:
            client = get_client(ctx)
            result = client.get_active_executions()
            
            if output_format == 'json':
                print_json(result)
                return
            
            # Clear screen for watch mode
            if watch:
                click.clear()
            
            executions = result.get('executions', [])
            
            click.echo(f"Active Test Executions ({len(executions)})")
            click.echo("=" * 60)
            
            if not executions:
                click.echo("No active executions")
                return
            
            headers = ['Test ID', 'Plan ID', 'Status', 'Progress', 'Environment', 'Elapsed']
            rows = []
            
            for execution in executions:
                # Calculate elapsed time
                elapsed_str = 'N/A'
                if execution.get('started_at'):
                    try:
                        start_time = datetime.fromisoformat(execution['started_at'].replace('Z', '+00:00'))
                        elapsed = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
                        elapsed_str = format_duration(elapsed)
                    except:
                        pass
                
                rows.append([
                    execution['test_id'][:12] + '...',
                    execution.get('plan_id', 'N/A')[:12] + '...' if execution.get('plan_id') else 'N/A',
                    format_test_status(execution['status']),
                    format_percentage(execution.get('progress', 0)),
                    execution.get('environment_id', 'N/A')[:12],
                    elapsed_str
                ])
            
            print_table(headers, rows)
            
            if watch:
                click.echo(f"\nLast updated: {datetime.now().strftime('%H:%M:%S')} (Press Ctrl+C to stop)")
            
        except Exception as e:
            if watch:
                click.echo(f"Error: {e}")
            else:
                handle_api_error(e, ctx.obj.get('debug', False))
    
    if watch:
        try:
            while True:
                show_active_executions()
                time.sleep(interval)
        except KeyboardInterrupt:
            click.echo("\nStopped watching")
    else:
        show_active_executions()


@status_group.command()
@click.argument('test_id')
@click.option('--force', is_flag=True, help='Force cancellation without confirmation')
@click.pass_context
def cancel(ctx, test_id, force):
    """Cancel a running test execution."""
    
    if not force:
        from cli.utils import confirm_action
        if not confirm_action(f"Cancel test execution {test_id}?"):
            click.echo("Cancellation aborted")
            return
    
    try:
        client = get_client(ctx)
        client.cancel_test(test_id)
        click.echo(f"✅ Test {test_id} cancellation requested")
        click.echo("Note: It may take a few moments for the test to actually stop")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@status_group.command()
@click.argument('plan_id')
@click.option('--timeout', default=3600, help='Maximum wait time in seconds')
@click.option('--poll-interval', default=30, help='Polling interval in seconds')
@click.option('--quiet', is_flag=True, help='Suppress progress output')
@click.pass_context
def wait(ctx, plan_id, timeout, poll_interval, quiet):
    """Wait for execution plan to complete."""
    
    try:
        client = get_client(ctx)
        
        if not quiet:
            click.echo(f"Waiting for execution plan {plan_id} to complete...")
            click.echo(f"Timeout: {format_duration(timeout)}, Poll interval: {poll_interval}s")
            click.echo("Press Ctrl+C to stop waiting (execution will continue)")
        
        start_time = time.time()
        
        try:
            final_status = client.wait_for_completion(plan_id, timeout, poll_interval)
            
            elapsed = time.time() - start_time
            
            if not quiet:
                click.echo(f"\n✅ Execution completed in {format_duration(elapsed)}")
                click.echo(f"Final status: {format_test_status(final_status['overall_status'])}")
                click.echo(f"Tests completed: {final_status['completed_tests']}/{final_status['total_tests']}")
                click.echo(f"Tests failed: {final_status['failed_tests']}")
            
            # Exit with non-zero code if there were failures
            if final_status['failed_tests'] > 0:
                if not quiet:
                    click.echo("⚠️  Some tests failed")
                ctx.exit(1)
            
        except KeyboardInterrupt:
            if not quiet:
                click.echo("\nStopped waiting (execution continues in background)")
            ctx.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@status_group.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def summary(ctx, output_format):
    """Show overall system status summary."""
    
    try:
        client = get_client(ctx)
        
        # Get system metrics
        metrics = client.get_system_metrics()
        
        # Get active executions
        active_result = client.get_active_executions()
        active_count = len(active_result.get('executions', []))
        
        if output_format == 'json':
            summary_data = {
                'metrics': metrics,
                'active_executions': active_count
            }
            print_json(summary_data)
            return
        
        click.echo("System Status Summary")
        click.echo("=" * 40)
        
        # Test queue status
        click.echo(f"🧪 Test Queue:")
        click.echo(f"  Active tests: {metrics.get('active_tests', 0)}")
        click.echo(f"  Queued tests: {metrics.get('queued_tests', 0)}")
        click.echo(f"  Running executions: {active_count}")
        
        # Environment status
        click.echo(f"\n🖥️  Environments:")
        click.echo(f"  Available: {metrics.get('available_environments', 0)}")
        click.echo(f"  Total: {metrics.get('total_environments', 0)}")
        
        # Resource utilization
        click.echo(f"\n📊 Resource Usage:")
        click.echo(f"  CPU: {format_percentage(metrics.get('cpu_usage', 0))}")
        click.echo(f"  Memory: {format_percentage(metrics.get('memory_usage', 0))}")
        click.echo(f"  Disk: {format_percentage(metrics.get('disk_usage', 0))}")
        
        # Network I/O
        network_io = metrics.get('network_io', {})
        if network_io:
            click.echo(f"\n🌐 Network I/O:")
            for metric, value in network_io.items():
                click.echo(f"  {metric}: {value}")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))