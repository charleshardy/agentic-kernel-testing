"""Interactive mode commands."""

import click
import sys
from typing import Dict, Any, List

from cli.utils import (
    get_client, handle_api_error, print_table, print_json,
    format_test_status, format_duration, select_from_list,
    confirm_action, prompt_for_input, display_paginated_results
)


@click.group(name='interactive')
def interactive_group():
    """Interactive exploration mode."""
    pass


@interactive_group.command()
@click.pass_context
def shell(ctx):
    """Start interactive shell mode."""
    
    click.echo("🚀 Agentic AI Testing System - Interactive Shell")
    click.echo("=" * 60)
    click.echo("Type 'help' for available commands or 'exit' to quit")
    click.echo()
    
    # Initialize client
    try:
        client = get_client(ctx)
        # Test connection
        health = client.health_check()
        click.echo(f"✅ Connected to API server (v{health.get('version', 'unknown')})")
    except Exception as e:
        click.echo(f"⚠️  Warning: Could not connect to API server: {e}")
        if not confirm_action("Continue in offline mode?"):
            return
        client = None
    
    click.echo()
    
    # Interactive shell loop
    while True:
        try:
            command = prompt_for_input("agentic> ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['exit', 'quit', 'q']:
                click.echo("Goodbye! 👋")
                break
            elif command.lower() in ['help', 'h', '?']:
                show_help()
            elif command.lower() in ['status', 'st']:
                show_system_status(client, ctx)
            elif command.lower().startswith('tests'):
                handle_tests_command(client, ctx, command)
            elif command.lower().startswith('results'):
                handle_results_command(client, ctx, command)
            elif command.lower().startswith('envs'):
                handle_environments_command(client, ctx, command)
            elif command.lower() in ['clear', 'cls']:
                click.clear()
            else:
                click.echo(f"Unknown command: {command}")
                click.echo("Type 'help' for available commands")
        
        except KeyboardInterrupt:
            click.echo("\nUse 'exit' to quit")
        except EOFError:
            click.echo("\nGoodbye! 👋")
            break
        except Exception as e:
            click.echo(f"Error: {e}")


def show_help():
    """Show interactive shell help."""
    click.echo("Available Commands:")
    click.echo("=" * 30)
    click.echo("📊 System:")
    click.echo("  status, st          - Show system status")
    click.echo("  clear, cls          - Clear screen")
    click.echo()
    click.echo("🧪 Tests:")
    click.echo("  tests               - List recent tests")
    click.echo("  tests active        - Show active tests")
    click.echo("  tests submit        - Submit a new test")
    click.echo()
    click.echo("📈 Results:")
    click.echo("  results             - List recent results")
    click.echo("  results failed      - Show failed tests")
    click.echo("  results summary     - Show results summary")
    click.echo()
    click.echo("🖥️  Environments:")
    click.echo("  envs                - List environments")
    click.echo("  envs available      - Show available environments")
    click.echo("  envs stats          - Show environment statistics")
    click.echo()
    click.echo("❓ General:")
    click.echo("  help, h, ?          - Show this help")
    click.echo("  exit, quit, q       - Exit interactive mode")


def show_system_status(client, ctx):
    """Show system status in interactive mode."""
    if not client:
        click.echo("❌ Not connected to API server")
        return
    
    try:
        # Get system metrics
        metrics = client.get_system_metrics()
        
        # Get active executions
        active_result = client.get_active_executions()
        active_count = len(active_result.get('executions', []))
        
        click.echo("System Status")
        click.echo("=" * 20)
        click.echo(f"🧪 Active tests: {metrics.get('active_tests', 0)}")
        click.echo(f"📋 Queued tests: {metrics.get('queued_tests', 0)}")
        click.echo(f"🏃 Running executions: {active_count}")
        click.echo(f"🖥️  Available environments: {metrics.get('available_environments', 0)}")
        click.echo(f"💾 CPU usage: {metrics.get('cpu_usage', 0):.1%}")
        click.echo(f"🧠 Memory usage: {metrics.get('memory_usage', 0):.1%}")
        
    except Exception as e:
        click.echo(f"❌ Failed to get system status: {e}")


def handle_tests_command(client, ctx, command):
    """Handle tests-related commands."""
    if not client:
        click.echo("❌ Not connected to API server")
        return
    
    parts = command.split()
    
    try:
        if len(parts) == 1:  # Just "tests"
            # List recent tests
            result = client.list_tests(page=1, page_size=10)
            tests = result.get('results', [])
            
            if not tests:
                click.echo("No tests found")
                return
            
            click.echo("Recent Tests:")
            click.echo("-" * 20)
            
            for test in tests:
                status_str = format_test_status(test.get('status', 'unknown'))
                click.echo(f"• {test['name'][:40]} - {status_str}")
                click.echo(f"  ID: {test['id'][:12]}... | Type: {test['test_type']} | Subsystem: {test['target_subsystem']}")
        
        elif len(parts) == 2 and parts[1] == 'active':
            # Show active tests
            result = client.get_active_executions()
            executions = result.get('executions', [])
            
            if not executions:
                click.echo("No active test executions")
                return
            
            click.echo("Active Test Executions:")
            click.echo("-" * 30)
            
            for execution in executions:
                status_str = format_test_status(execution['status'])
                progress = execution.get('progress', 0) * 100
                click.echo(f"• {execution['test_id'][:12]}... - {status_str} ({progress:.1f}%)")
                if execution.get('environment_id'):
                    click.echo(f"  Environment: {execution['environment_id'][:12]}...")
        
        elif len(parts) == 2 and parts[1] == 'submit':
            # Interactive test submission
            submit_test_interactive(client)
        
        else:
            click.echo("Usage: tests [active|submit]")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")


def handle_results_command(client, ctx, command):
    """Handle results-related commands."""
    if not client:
        click.echo("❌ Not connected to API server")
        return
    
    parts = command.split()
    
    try:
        if len(parts) == 1:  # Just "results"
            # List recent results
            result = client.list_test_results(page=1, page_size=10)
            results = result.get('results', [])
            
            if not results:
                click.echo("No test results found")
                return
            
            click.echo("Recent Test Results:")
            click.echo("-" * 25)
            
            for test_result in results:
                status_str = format_test_status(test_result['status'])
                duration = format_duration(test_result.get('execution_time', 0))
                click.echo(f"• {test_result['test_id'][:12]}... - {status_str} ({duration})")
                click.echo(f"  Timestamp: {test_result['timestamp'][:19]}")
        
        elif len(parts) == 2 and parts[1] == 'failed':
            # Show failed tests
            result = client.list_test_results(page=1, page_size=10, status_filter='failed')
            results = result.get('results', [])
            
            if not results:
                click.echo("No failed tests found")
                return
            
            click.echo("Failed Test Results:")
            click.echo("-" * 25)
            
            for test_result in results:
                duration = format_duration(test_result.get('execution_time', 0))
                click.echo(f"• {test_result['test_id'][:12]}... - FAILED ({duration})")
                
                # Try to get failure info
                try:
                    detailed_result = client.get_test_result(test_result['test_id'])
                    failure_info = detailed_result.get('failure_info', {})
                    if failure_info.get('error_message'):
                        error_msg = failure_info['error_message'][:60]
                        click.echo(f"  Error: {error_msg}...")
                except:
                    pass
        
        elif len(parts) == 2 and parts[1] == 'summary':
            # Show results summary
            summary = client.get_results_summary(days=7)
            
            click.echo("Results Summary (Last 7 days):")
            click.echo("-" * 35)
            
            total_tests = summary.get('total_tests', 0)
            passed_tests = summary.get('passed_tests', 0)
            failed_tests = summary.get('failed_tests', 0)
            pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            click.echo(f"📊 Total tests: {total_tests}")
            click.echo(f"✅ Passed: {passed_tests}")
            click.echo(f"❌ Failed: {failed_tests}")
            click.echo(f"📈 Pass rate: {pass_rate:.1f}%")
        
        else:
            click.echo("Usage: results [failed|summary]")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")


def handle_environments_command(client, ctx, command):
    """Handle environment-related commands."""
    if not client:
        click.echo("❌ Not connected to API server")
        return
    
    parts = command.split()
    
    try:
        if len(parts) == 1:  # Just "envs"
            # List environments
            result = client.list_environments(page=1, page_size=10)
            environments = result.get('results', [])
            
            if not environments:
                click.echo("No environments found")
                return
            
            click.echo("Test Environments:")
            click.echo("-" * 20)
            
            for env in environments:
                config = env.get('config', {})
                env_type = 'Virtual' if config.get('is_virtual', True) else 'Physical'
                memory = config.get('memory_mb', 0)
                
                click.echo(f"• {env['id'][:12]}... - {env['status'].upper()}")
                click.echo(f"  {config.get('architecture', 'N/A')} | {memory}MB | {env_type}")
        
        elif len(parts) == 2 and parts[1] == 'available':
            # Show available environments
            result = client.list_environments(status_filter='idle', page_size=20)
            environments = result.get('results', [])
            
            if not environments:
                click.echo("No available environments")
                return
            
            click.echo("Available Environments:")
            click.echo("-" * 30)
            
            # Group by architecture
            by_arch = {}
            for env in environments:
                arch = env.get('config', {}).get('architecture', 'unknown')
                if arch not in by_arch:
                    by_arch[arch] = []
                by_arch[arch].append(env)
            
            for arch, arch_envs in by_arch.items():
                click.echo(f"\n🏗️  {arch.upper()} ({len(arch_envs)} available)")
                for env in arch_envs[:3]:  # Show first 3
                    config = env.get('config', {})
                    memory = config.get('memory_mb', 0)
                    click.echo(f"  • {env['id'][:12]}... ({memory}MB)")
                if len(arch_envs) > 3:
                    click.echo(f"  ... and {len(arch_envs) - 3} more")
        
        elif len(parts) == 2 and parts[1] == 'stats':
            # Show environment statistics
            stats = client.get_environment_stats()
            
            click.echo("Environment Statistics:")
            click.echo("-" * 25)
            click.echo(f"📊 Total: {stats.get('total_environments', 0)}")
            click.echo(f"✅ Available: {stats.get('available_environments', 0)}")
            click.echo(f"🏃 Busy: {stats.get('busy_environments', 0)}")
            click.echo(f"💤 Idle: {stats.get('idle_environments', 0)}")
            click.echo(f"❌ Error: {stats.get('error_environments', 0)}")
        
        else:
            click.echo("Usage: envs [available|stats]")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")


def submit_test_interactive(client):
    """Interactive test submission wizard."""
    click.echo("\n🧪 Interactive Test Submission")
    click.echo("=" * 35)
    
    try:
        # Get test details
        name = prompt_for_input("Test name")
        description = prompt_for_input("Test description")
        
        # Test type selection
        test_types = ['unit', 'integration', 'fuzz', 'performance', 'security']
        test_type = select_from_list(test_types, "Select test type")
        
        subsystem = prompt_for_input("Target subsystem")
        
        # Test script
        click.echo("\nTest script options:")
        click.echo("1. Enter script content directly")
        click.echo("2. Provide file path")
        click.echo("3. Skip (empty script)")
        
        script_choice = prompt_for_input("Choice (1-3)", default="3")
        test_script = ""
        
        if script_choice == "1":
            click.echo("Enter test script (press Ctrl+D when done):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                test_script = "\n".join(lines)
        elif script_choice == "2":
            script_path = prompt_for_input("Script file path")
            try:
                from pathlib import Path
                test_script = Path(script_path).read_text()
            except Exception as e:
                click.echo(f"Warning: Could not read script file: {e}")
        
        # Optional settings
        timeout = int(prompt_for_input("Test timeout (seconds)", default="300"))
        priority = int(prompt_for_input("Priority (0-10)", default="5"))
        
        # Hardware requirements
        if confirm_action("Specify hardware requirements?"):
            architectures = ['x86_64', 'arm64', 'riscv64', 'arm']
            arch = select_from_list(architectures, "Select architecture")
            memory = int(prompt_for_input("Memory (MB)", default="2048"))
            virtual = confirm_action("Use virtual environment?", default=True)
            
            hardware_config = {
                "architecture": arch,
                "cpu_model": "generic",
                "memory_mb": memory,
                "storage_type": "ssd",
                "peripherals": [],
                "is_virtual": virtual
            }
        else:
            hardware_config = None
        
        # Create test case
        from api.client import TestCase
        test_case = TestCase(
            name=name,
            description=description,
            test_type=test_type,
            target_subsystem=subsystem,
            test_script=test_script,
            execution_time_estimate=timeout,
            required_hardware=hardware_config,
            priority=priority
        )
        
        # Show summary
        click.echo("\n📋 Test Summary:")
        click.echo("-" * 20)
        click.echo(f"Name: {name}")
        click.echo(f"Type: {test_type}")
        click.echo(f"Subsystem: {subsystem}")
        click.echo(f"Priority: {priority}")
        if hardware_config:
            click.echo(f"Hardware: {hardware_config['architecture']} ({hardware_config['memory_mb']}MB)")
        
        if confirm_action("Submit this test?"):
            result = client.submit_test(test_case, priority=priority)
            
            click.echo("\n✅ Test submitted successfully!")
            click.echo(f"Test ID: {result['test_case_ids'][0]}")
            click.echo(f"Execution Plan: {result['execution_plan_id']}")
        else:
            click.echo("Test submission cancelled")
    
    except (KeyboardInterrupt, EOFError):
        click.echo("\nTest submission cancelled")
    except Exception as e:
        click.echo(f"❌ Error submitting test: {e}")


@interactive_group.command()
@click.pass_context
def explore(ctx):
    """Explore system data interactively."""
    
    click.echo("🔍 System Explorer")
    click.echo("=" * 30)
    
    try:
        client = get_client(ctx)
    except Exception as e:
        click.echo(f"❌ Could not connect to API: {e}")
        return
    
    while True:
        try:
            click.echo("\nWhat would you like to explore?")
            click.echo("1. Recent test results")
            click.echo("2. Active test executions")
            click.echo("3. Environment status")
            click.echo("4. System metrics")
            click.echo("5. Failed tests analysis")
            click.echo("0. Exit explorer")
            
            choice = prompt_for_input("Choice (0-5)")
            
            if choice == "0":
                break
            elif choice == "1":
                explore_test_results(client)
            elif choice == "2":
                explore_active_executions(client)
            elif choice == "3":
                explore_environments(client)
            elif choice == "4":
                explore_system_metrics(client)
            elif choice == "5":
                explore_failed_tests(client)
            else:
                click.echo("Invalid choice")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            click.echo(f"Error: {e}")
    
    click.echo("Explorer closed")


def explore_test_results(client):
    """Explore test results interactively."""
    try:
        result = client.list_test_results(page=1, page_size=50)
        results = result.get('results', [])
        
        if not results:
            click.echo("No test results found")
            return
        
        def format_result(test_result):
            status_str = format_test_status(test_result['status'])
            duration = format_duration(test_result.get('execution_time', 0))
            click.echo(f"ID: {test_result['test_id']}")
            click.echo(f"Status: {status_str}")
            click.echo(f"Duration: {duration}")
            click.echo(f"Timestamp: {test_result['timestamp']}")
            click.echo("-" * 40)
        
        display_paginated_results(results, page_size=5, formatter=format_result)
        
    except Exception as e:
        click.echo(f"Error exploring test results: {e}")


def explore_active_executions(client):
    """Explore active executions interactively."""
    try:
        result = client.get_active_executions()
        executions = result.get('executions', [])
        
        if not executions:
            click.echo("No active executions")
            return
        
        click.echo(f"Active Executions ({len(executions)}):")
        click.echo("=" * 40)
        
        for execution in executions:
            status_str = format_test_status(execution['status'])
            progress = execution.get('progress', 0) * 100
            
            click.echo(f"Test ID: {execution['test_id']}")
            click.echo(f"Status: {status_str}")
            click.echo(f"Progress: {progress:.1f}%")
            
            if execution.get('environment_id'):
                click.echo(f"Environment: {execution['environment_id']}")
            
            if execution.get('started_at'):
                click.echo(f"Started: {execution['started_at']}")
            
            click.echo("-" * 30)
        
    except Exception as e:
        click.echo(f"Error exploring active executions: {e}")


def explore_environments(client):
    """Explore environments interactively."""
    try:
        result = client.list_environments(page_size=50)
        environments = result.get('results', [])
        
        if not environments:
            click.echo("No environments found")
            return
        
        # Group by status
        by_status = {}
        for env in environments:
            status = env['status']
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(env)
        
        click.echo("Environments by Status:")
        click.echo("=" * 30)
        
        for status, envs in by_status.items():
            click.echo(f"\n{status.upper()} ({len(envs)}):")
            for env in envs[:5]:  # Show first 5
                config = env.get('config', {})
                arch = config.get('architecture', 'N/A')
                memory = config.get('memory_mb', 0)
                env_type = 'Virtual' if config.get('is_virtual', True) else 'Physical'
                
                click.echo(f"  • {env['id'][:12]}... - {arch} ({memory}MB {env_type})")
            
            if len(envs) > 5:
                click.echo(f"  ... and {len(envs) - 5} more")
        
    except Exception as e:
        click.echo(f"Error exploring environments: {e}")


def explore_system_metrics(client):
    """Explore system metrics interactively."""
    try:
        metrics = client.get_system_metrics()
        
        click.echo("System Metrics:")
        click.echo("=" * 20)
        
        click.echo(f"🧪 Active tests: {metrics.get('active_tests', 0)}")
        click.echo(f"📋 Queued tests: {metrics.get('queued_tests', 0)}")
        click.echo(f"🖥️  Available environments: {metrics.get('available_environments', 0)}")
        click.echo(f"🏗️  Total environments: {metrics.get('total_environments', 0)}")
        click.echo(f"💾 CPU usage: {metrics.get('cpu_usage', 0):.1%}")
        click.echo(f"🧠 Memory usage: {metrics.get('memory_usage', 0):.1%}")
        click.echo(f"💿 Disk usage: {metrics.get('disk_usage', 0):.1%}")
        
        network_io = metrics.get('network_io', {})
        if network_io:
            click.echo(f"\n🌐 Network I/O:")
            for metric, value in network_io.items():
                click.echo(f"  {metric}: {value}")
        
    except Exception as e:
        click.echo(f"Error exploring system metrics: {e}")


def explore_failed_tests(client):
    """Explore failed tests interactively."""
    try:
        result = client.list_test_results(status_filter='failed', page_size=20)
        failed_tests = result.get('results', [])
        
        if not failed_tests:
            click.echo("No failed tests found")
            return
        
        click.echo(f"Failed Tests ({len(failed_tests)}):")
        click.echo("=" * 30)
        
        for test_result in failed_tests:
            click.echo(f"\nTest ID: {test_result['test_id']}")
            click.echo(f"Timestamp: {test_result['timestamp']}")
            click.echo(f"Duration: {format_duration(test_result.get('execution_time', 0))}")
            
            # Try to get detailed failure info
            try:
                detailed_result = client.get_test_result(test_result['test_id'])
                failure_info = detailed_result.get('failure_info', {})
                
                if failure_info.get('error_message'):
                    error_msg = failure_info['error_message']
                    if len(error_msg) > 100:
                        error_msg = error_msg[:100] + "..."
                    click.echo(f"Error: {error_msg}")
                
                if failure_info.get('exit_code'):
                    click.echo(f"Exit Code: {failure_info['exit_code']}")
                
            except:
                pass  # Skip if we can't get detailed info
            
            click.echo("-" * 40)
        
    except Exception as e:
        click.echo(f"Error exploring failed tests: {e}")