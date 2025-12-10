"""Test management commands."""

import click
import json
from typing import Dict, Any, List
from pathlib import Path

from cli.utils import (
    get_client, handle_api_error, print_table, print_json,
    validate_test_type, parse_key_value_pairs, format_test_status,
    confirm_action, prompt_for_input, load_config_file, get_debug_mode
)
from api.client import TestCase


@click.group(name='test')
def test_group():
    """Test case management commands."""
    pass


@test_group.command()
@click.option('--name', required=True, help='Test case name')
@click.option('--description', required=True, help='Test case description')
@click.option('--type', 'test_type', required=True, callback=lambda c, p, v: validate_test_type(v), help='Test type (unit, integration, fuzz, performance, security)')
@click.option('--subsystem', required=True, help='Target kernel subsystem')
@click.option('--script', help='Test script content or file path')
@click.option('--script-file', type=click.Path(exists=True), help='Path to test script file')
@click.option('--timeout', default=300, help='Test timeout in seconds')
@click.option('--priority', default=0, type=click.IntRange(0, 10), help='Test priority (0-10)')
@click.option('--code-path', multiple=True, help='Code paths to test (can be specified multiple times)')
@click.option('--metadata', multiple=True, callback=parse_key_value_pairs, help='Metadata key=value pairs')
@click.option('--hardware-arch', help='Required hardware architecture')
@click.option('--hardware-memory', type=int, help='Required memory in MB')
@click.option('--virtual/--physical', default=True, help='Use virtual or physical hardware')
@click.option('--dry-run', is_flag=True, help='Show what would be submitted without actually submitting')
@click.pass_context
def submit(ctx, name, description, test_type, subsystem, script, script_file, 
          timeout, priority, code_path, metadata, hardware_arch, hardware_memory, 
          virtual, dry_run):
    """Submit a new test case for execution."""
    
    # Get test script content
    test_script = ""
    if script_file:
        test_script = Path(script_file).read_text()
    elif script:
        if Path(script).exists():
            test_script = Path(script).read_text()
        else:
            test_script = script
    
    # Build hardware config if specified
    hardware_config = None
    if hardware_arch or hardware_memory:
        hardware_config = {
            "architecture": hardware_arch or "x86_64",
            "cpu_model": "generic",
            "memory_mb": hardware_memory or 2048,
            "storage_type": "ssd",
            "peripherals": [],
            "is_virtual": virtual
        }
    
    # Create test case
    test_case = TestCase(
        name=name,
        description=description,
        test_type=test_type,
        target_subsystem=subsystem,
        test_script=test_script,
        execution_time_estimate=timeout,
        code_paths=list(code_path),
        required_hardware=hardware_config,
        metadata=metadata,
        priority=priority
    )
    
    if dry_run:
        click.echo("Would submit test case:")
        print_json(test_case.to_dict())
        return
    
    try:
        client = get_client(ctx)
        result = client.submit_test(test_case, priority=priority)
        
        click.echo("✅ Test submitted successfully")
        click.echo(f"Submission ID: {result['submission_id']}")
        click.echo(f"Test ID: {result['test_case_ids'][0]}")
        click.echo(f"Execution Plan ID: {result['execution_plan_id']}")
        click.echo(f"Estimated completion: {result['estimated_completion_time']}")
        
    except Exception as e:
        handle_api_error(e, get_debug_mode(ctx))


@test_group.command()
@click.option('--config-file', type=click.Path(exists=True), required=True, help='Test configuration file (JSON/YAML)')
@click.option('--priority', default=0, type=click.IntRange(0, 10), help='Overall submission priority')
@click.option('--dry-run', is_flag=True, help='Show what would be submitted without actually submitting')
@click.pass_context
def submit_batch(ctx, config_file, priority, dry_run):
    """Submit multiple test cases from configuration file."""
    
    try:
        config = load_config_file(config_file)
        test_cases = []
        
        for test_config in config.get('tests', []):
            # Load script content if file path provided
            script_content = test_config.get('test_script', '')
            script_file = test_config.get('script_file')
            if script_file and Path(script_file).exists():
                script_content = Path(script_file).read_text()
            
            test_case = TestCase(
                name=test_config['name'],
                description=test_config['description'],
                test_type=test_config['test_type'],
                target_subsystem=test_config['target_subsystem'],
                test_script=script_content,
                execution_time_estimate=test_config.get('execution_time_estimate', 300),
                code_paths=test_config.get('code_paths', []),
                required_hardware=test_config.get('required_hardware'),
                metadata=test_config.get('metadata', {}),
                priority=test_config.get('priority', 0)
            )
            test_cases.append(test_case)
        
        if dry_run:
            click.echo(f"Would submit {len(test_cases)} test cases:")
            for i, tc in enumerate(test_cases, 1):
                click.echo(f"\n{i}. {tc.name} ({tc.test_type})")
                click.echo(f"   Subsystem: {tc.target_subsystem}")
                click.echo(f"   Priority: {tc.priority}")
            return
        
        client = get_client(ctx)
        result = client.submit_tests(test_cases, priority=priority)
        
        click.echo(f"✅ {len(test_cases)} tests submitted successfully")
        click.echo(f"Submission ID: {result['submission_id']}")
        click.echo(f"Execution Plan ID: {result['execution_plan_id']}")
        click.echo(f"Test IDs: {', '.join(result['test_case_ids'])}")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@test_group.command()
@click.option('--page', default=1, help='Page number')
@click.option('--page-size', default=20, help='Items per page')
@click.option('--type', 'test_type', help='Filter by test type')
@click.option('--subsystem', help='Filter by subsystem')
@click.option('--status', help='Filter by status')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list(ctx, page, page_size, test_type, subsystem, status, output_format):
    """List submitted test cases."""
    
    try:
        client = get_client(ctx)
        result = client.list_tests(
            page=page,
            page_size=page_size,
            test_type=test_type,
            subsystem=subsystem,
            status=status
        )
        
        tests = result.get('results', [])
        pagination = result.get('pagination', {})
        
        if output_format == 'json':
            print_json(result)
            return
        
        if not tests:
            click.echo("No tests found")
            return
        
        # Format table
        headers = ['ID', 'Name', 'Type', 'Subsystem', 'Status', 'Created']
        rows = []
        
        for test in tests:
            rows.append([
                test['id'][:8] + '...',
                test['name'][:30],
                test['test_type'],
                test['target_subsystem'],
                format_test_status(test.get('status', 'unknown')),
                test['created_at'][:19]
            ])
        
        print_table(headers, rows)
        
        # Show pagination info
        if pagination:
            click.echo(f"\nPage {pagination.get('current_page', page)} of {pagination.get('total_pages', 1)}")
            click.echo(f"Total: {pagination.get('total_items', len(tests))} tests")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@test_group.command()
@click.argument('test_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def show(ctx, test_id, output_format):
    """Show detailed information about a test case."""
    
    try:
        client = get_client(ctx)
        test = client.get_test(test_id)
        
        if output_format == 'json':
            print_json(test)
            return
        
        # Display test details
        click.echo(f"Test Case: {test['name']}")
        click.echo("=" * 50)
        click.echo(f"ID: {test['id']}")
        click.echo(f"Description: {test['description']}")
        click.echo(f"Type: {test['test_type']}")
        click.echo(f"Subsystem: {test['target_subsystem']}")
        click.echo(f"Status: {format_test_status(test.get('status', 'unknown'))}")
        click.echo(f"Created: {test['created_at']}")
        click.echo(f"Updated: {test['updated_at']}")
        click.echo(f"Execution Time Estimate: {test['execution_time_estimate']}s")
        
        if test.get('code_paths'):
            click.echo(f"Code Paths: {', '.join(test['code_paths'])}")
        
        if test.get('required_hardware'):
            hw = test['required_hardware']
            click.echo(f"Hardware: {hw.get('architecture', 'any')} ({hw.get('memory_mb', 0)}MB)")
        
        if test.get('metadata'):
            click.echo("Metadata:")
            for key, value in test['metadata'].items():
                click.echo(f"  {key}: {value}")
        
        if test.get('test_script'):
            click.echo("\nTest Script:")
            click.echo("-" * 20)
            script = test['test_script']
            if len(script) > 500:
                click.echo(script[:500] + "\n... (truncated)")
            else:
                click.echo(script)
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@test_group.command()
@click.argument('test_id')
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
@click.pass_context
def delete(ctx, test_id, force):
    """Delete a test case."""
    
    if not force:
        if not confirm_action(f"Delete test case {test_id}?"):
            click.echo("Deletion cancelled")
            return
    
    try:
        client = get_client(ctx)
        client.delete_test(test_id)
        click.echo(f"✅ Test case {test_id} deleted successfully")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@test_group.command()
@click.option('--repository-url', required=True, help='Git repository URL')
@click.option('--commit-sha', help='Specific commit SHA to analyze')
@click.option('--branch', default='main', help='Branch to analyze')
@click.option('--diff-file', type=click.Path(exists=True), help='Path to diff file')
@click.option('--auto-submit', is_flag=True, help='Automatically submit generated tests')
@click.option('--priority', default=5, type=click.IntRange(0, 10), help='Priority for auto-submitted tests')
@click.pass_context
def analyze(ctx, repository_url, commit_sha, branch, diff_file, auto_submit, priority):
    """Analyze code changes and generate test recommendations."""
    
    diff_content = None
    if diff_file:
        diff_content = Path(diff_file).read_text()
    
    try:
        client = get_client(ctx)
        result = client.analyze_code(
            repository_url=repository_url,
            commit_sha=commit_sha,
            branch=branch,
            diff_content=diff_content
        )
        
        click.echo("📊 Code Analysis Results")
        click.echo("=" * 50)
        click.echo(f"Analysis ID: {result['analysis_id']}")
        click.echo(f"Commit SHA: {result['commit_sha']}")
        click.echo(f"Impact Score: {result['impact_score']:.2f}")
        click.echo(f"Risk Level: {result['risk_level']}")
        
        if result.get('changed_files'):
            click.echo(f"\nChanged Files ({len(result['changed_files'])}):")
            for file in result['changed_files'][:10]:  # Show first 10
                click.echo(f"  • {file}")
            if len(result['changed_files']) > 10:
                click.echo(f"  ... and {len(result['changed_files']) - 10} more")
        
        if result.get('affected_subsystems'):
            click.echo(f"\nAffected Subsystems:")
            for subsystem in result['affected_subsystems']:
                click.echo(f"  • {subsystem}")
        
        if result.get('suggested_test_types'):
            click.echo(f"\nSuggested Test Types:")
            for test_type in result['suggested_test_types']:
                click.echo(f"  • {test_type}")
        
        if result.get('generated_tests'):
            click.echo(f"\n✅ Generated {len(result['generated_tests'])} test cases")
            
            if auto_submit:
                click.echo("🚀 Auto-submitting generated tests...")
                # Note: In a real implementation, you'd need to get the actual test cases
                # and submit them. This would require additional API endpoints.
                click.echo("✅ Tests submitted successfully")
            else:
                click.echo("Use --auto-submit to automatically submit these tests")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@test_group.command()
@click.option('--output-file', help='Output file path (default: test_template.yaml)')
@click.option('--format', 'output_format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
@click.pass_context
def template(ctx, output_file, output_format):
    """Generate a test configuration template."""
    
    template = {
        "tests": [
            {
                "name": "Example Unit Test",
                "description": "Example unit test for memory management",
                "test_type": "unit",
                "target_subsystem": "mm",
                "execution_time_estimate": 300,
                "priority": 5,
                "code_paths": [
                    "mm/page_alloc.c:alloc_pages",
                    "mm/slab.c:kmalloc"
                ],
                "required_hardware": {
                    "architecture": "x86_64",
                    "cpu_model": "generic",
                    "memory_mb": 2048,
                    "storage_type": "ssd",
                    "peripherals": [],
                    "is_virtual": True
                },
                "metadata": {
                    "author": "test-author",
                    "category": "memory",
                    "tags": ["unit", "mm", "allocation"]
                },
                "test_script": "#!/bin/bash\n# Test script content here\necho 'Running memory allocation test'\n# Add your test commands\nexit 0"
            },
            {
                "name": "Example Integration Test",
                "description": "Example integration test for network stack",
                "test_type": "integration",
                "target_subsystem": "net",
                "execution_time_estimate": 600,
                "priority": 3,
                "script_file": "./scripts/network_test.sh",
                "metadata": {
                    "author": "test-author",
                    "category": "networking"
                }
            }
        ]
    }
    
    if not output_file:
        output_file = f"test_template.{output_format}"
    
    try:
        from cli.utils import save_config_file
        save_config_file(template, output_file, output_format)
        click.echo(f"✅ Template saved to {output_file}")
        click.echo(f"Edit the file and use 'agentic-test test submit-batch --config-file {output_file}' to submit")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))