"""Specification management CLI commands.

Provides commands for managing test specifications:
- Create, list, show, validate, export specifications
- Parse and validate requirements
- Generate properties and tests
- Run property tests
- Generate traceability reports
"""

import click
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.utils import get_client, handle_api_error, format_table


@click.group(name='spec')
def spec_group():
    """Manage test specifications.
    
    Commands for creating, managing, and working with test specifications
    that define requirements, properties, and property-based tests.
    
    Examples:
        # Create a new specification
        agentic-test spec create "Memory Management Tests"
        
        # List all specifications
        agentic-test spec list
        
        # Show specification details
        agentic-test spec show <spec-id>
        
        # Validate a specification
        agentic-test spec validate <spec-id>
        
        # Export specification
        agentic-test spec export <spec-id> --format markdown
    """
    pass


@spec_group.command('create')
@click.argument('name')
@click.option('--description', '-d', default='', help='Specification description')
@click.option('--template', '-t', help='Template to use (basic, kernel, bsp)')
@click.option('--output', '-o', help='Output file path for specification')
@click.pass_context
def create_spec(ctx, name, description, template, output):
    """Create a new test specification.
    
    NAME is the name for the new specification.
    
    Examples:
        agentic-test spec create "Memory Tests" -d "Tests for memory subsystem"
        agentic-test spec create "Driver Tests" --template kernel
    """
    try:
        client = get_client(ctx)
        
        # Prepare request data
        data = {
            'name': name,
            'description': description,
        }
        
        # Add template-based glossary if specified
        if template:
            data['glossary'] = _get_template_glossary(template)
            data['metadata'] = {'template': template}
        
        response = client.post('/specifications', json=data)
        
        if response.get('success'):
            spec_data = response.get('data', {})
            spec_id = spec_data.get('id', 'unknown')
            
            click.echo(f"✅ Created specification: {name}")
            click.echo(f"   ID: {spec_id}")
            
            if output:
                # Export to file
                export_response = client.post(
                    f'/specifications/{spec_id}/export',
                    json={'format': 'yaml'}
                )
                if export_response.get('success'):
                    content = export_response.get('data', {}).get('content', '')
                    Path(output).write_text(content)
                    click.echo(f"   Saved to: {output}")
        else:
            click.echo(f"❌ Failed to create specification: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@spec_group.command('list')
@click.option('--search', '-s', help='Search in name and description')
@click.option('--page', default=1, help='Page number')
@click.option('--page-size', default=20, help='Items per page')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def list_specs(ctx, search, page, page_size, as_json):
    """List all test specifications.
    
    Examples:
        agentic-test spec list
        agentic-test spec list --search "memory"
        agentic-test spec list --json
    """
    try:
        client = get_client(ctx)
        
        params = {'page': page, 'page_size': page_size}
        if search:
            params['search'] = search
        
        response = client.get('/specifications', params=params)
        
        if response.get('success'):
            data = response.get('data', {})
            specs = data.get('specifications', [])
            pagination = data.get('pagination', {})
            
            if as_json:
                click.echo(json.dumps(specs, indent=2))
            else:
                if not specs:
                    click.echo("No specifications found.")
                    return
                
                # Format as table
                headers = ['ID', 'Name', 'Requirements', 'Properties', 'Tests', 'Updated']
                rows = []
                for spec in specs:
                    rows.append([
                        spec.get('id', ''),
                        spec.get('name', '')[:30],
                        str(len(spec.get('requirements', []))),
                        str(len(spec.get('properties', []))),
                        str(len(spec.get('tests', []))),
                        spec.get('updated_at', '')[:10],
                    ])
                
                click.echo(format_table(headers, rows))
                
                # Show pagination info
                total = pagination.get('total_items', 0)
                total_pages = pagination.get('total_pages', 1)
                click.echo(f"\nPage {page}/{total_pages} ({total} total)")
        else:
            click.echo(f"❌ Failed to list specifications: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@spec_group.command('show')
@click.argument('spec_id')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def show_spec(ctx, spec_id, as_json):
    """Show specification details.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test spec show spec_abc123
        agentic-test spec show spec_abc123 --json
    """
    try:
        client = get_client(ctx)
        response = client.get(f'/specifications/{spec_id}')
        
        if response.get('success'):
            spec = response.get('data', {})
            
            if as_json:
                click.echo(json.dumps(spec, indent=2))
            else:
                _display_specification(spec)
        else:
            click.echo(f"❌ Specification not found: {spec_id}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@spec_group.command('validate')
@click.argument('spec_id')
@click.pass_context
def validate_spec(ctx, spec_id):
    """Validate a specification for completeness and correctness.
    
    SPEC_ID is the specification identifier.
    
    Checks:
    - All requirements follow EARS patterns
    - No undefined terms in requirements
    - All properties have requirement links
    - All tests have property links
    
    Examples:
        agentic-test spec validate spec_abc123
    """
    try:
        client = get_client(ctx)
        response = client.get(f'/specifications/{spec_id}')
        
        if not response.get('success'):
            click.echo(f"❌ Specification not found: {spec_id}", err=True)
            return
        
        spec = response.get('data', {})
        issues = []
        warnings = []
        
        # Check requirements
        requirements = spec.get('requirements', [])
        for req in requirements:
            # Validate each requirement
            val_response = client.post('/specifications/requirements/validate', json={
                'text': req.get('text', ''),
                'glossary': spec.get('glossary', {})
            })
            if val_response.get('success'):
                val_data = val_response.get('data', {})
                if not val_data.get('is_valid'):
                    for issue in val_data.get('issues', []):
                        issues.append(f"Requirement {req.get('id')}: {issue}")
                for warning in val_data.get('suggestions', []):
                    warnings.append(f"Requirement {req.get('id')}: {warning}")
        
        # Check properties have requirement links
        properties = spec.get('properties', [])
        for prop in properties:
            if not prop.get('requirement_ids'):
                issues.append(f"Property {prop.get('id')}: No requirement links")
        
        # Check tests have property links
        tests = spec.get('tests', [])
        for test in tests:
            if not test.get('property_id'):
                issues.append(f"Test {test.get('id')}: No property link")
        
        # Display results
        if not issues and not warnings:
            click.echo("✅ Specification is valid")
        else:
            if issues:
                click.echo("❌ Validation Issues:")
                for issue in issues:
                    click.echo(f"   - {issue}")
            if warnings:
                click.echo("\n⚠️  Warnings:")
                for warning in warnings:
                    click.echo(f"   - {warning}")
        
        # Summary
        click.echo(f"\nSummary:")
        click.echo(f"  Requirements: {len(requirements)}")
        click.echo(f"  Properties: {len(properties)}")
        click.echo(f"  Tests: {len(tests)}")
        click.echo(f"  Issues: {len(issues)}")
        click.echo(f"  Warnings: {len(warnings)}")
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@spec_group.command('export')
@click.argument('spec_id')
@click.option('--format', '-f', 'fmt', default='yaml',
              type=click.Choice(['yaml', 'json', 'markdown', 'html']),
              help='Export format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def export_spec(ctx, spec_id, fmt, output):
    """Export a specification to a file.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test spec export spec_abc123 --format markdown
        agentic-test spec export spec_abc123 -f yaml -o spec.yaml
    """
    try:
        client = get_client(ctx)
        response = client.post(f'/specifications/{spec_id}/export', json={'format': fmt})
        
        if response.get('success'):
            content = response.get('data', {}).get('content', '')
            
            if output:
                Path(output).write_text(content)
                click.echo(f"✅ Exported to: {output}")
            else:
                click.echo(content)
        else:
            click.echo(f"❌ Failed to export: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@spec_group.command('delete')
@click.argument('spec_id')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_spec(ctx, spec_id, yes):
    """Delete a specification.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test spec delete spec_abc123
        agentic-test spec delete spec_abc123 --yes
    """
    if not yes:
        if not click.confirm(f"Delete specification {spec_id}?"):
            click.echo("Cancelled.")
            return
    
    try:
        client = get_client(ctx)
        response = client.delete(f'/specifications/{spec_id}')
        
        if response.get('success'):
            click.echo(f"✅ Deleted specification: {spec_id}")
        else:
            click.echo(f"❌ Failed to delete: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


# Helper functions

def _get_template_glossary(template: str) -> dict:
    """Get glossary for a template."""
    templates = {
        'basic': {
            'System': 'The software system under test',
            'User': 'A human user of the system',
        },
        'kernel': {
            'Kernel': 'The Linux kernel under test',
            'Driver': 'A kernel device driver',
            'Subsystem': 'A kernel subsystem (mm, fs, net, etc.)',
            'Process': 'A running process in the system',
            'Memory': 'System memory resources',
        },
        'bsp': {
            'BSP': 'Board Support Package under test',
            'Board': 'The target hardware board',
            'Bootloader': 'The system bootloader',
            'Device_Tree': 'Hardware device tree configuration',
            'Peripheral': 'A hardware peripheral device',
        },
    }
    return templates.get(template, templates['basic'])


def _display_specification(spec: dict) -> None:
    """Display specification details."""
    click.echo(f"\n{'='*60}")
    click.echo(f"Specification: {spec.get('name', 'Unknown')}")
    click.echo(f"{'='*60}")
    click.echo(f"ID: {spec.get('id', '')}")
    click.echo(f"Version: {spec.get('version', '1.0.0')}")
    click.echo(f"Created: {spec.get('created_at', '')}")
    click.echo(f"Updated: {spec.get('updated_at', '')}")
    
    if spec.get('description'):
        click.echo(f"\nDescription:\n  {spec.get('description')}")
    
    # Requirements
    requirements = spec.get('requirements', [])
    click.echo(f"\nRequirements ({len(requirements)}):")
    for req in requirements[:5]:
        click.echo(f"  - [{req.get('id')}] {req.get('text', '')[:60]}...")
    if len(requirements) > 5:
        click.echo(f"  ... and {len(requirements) - 5} more")
    
    # Properties
    properties = spec.get('properties', [])
    click.echo(f"\nProperties ({len(properties)}):")
    for prop in properties[:5]:
        click.echo(f"  - [{prop.get('id')}] {prop.get('name', '')}")
    if len(properties) > 5:
        click.echo(f"  ... and {len(properties) - 5} more")
    
    # Tests
    tests = spec.get('tests', [])
    click.echo(f"\nTests ({len(tests)}):")
    for test in tests[:5]:
        click.echo(f"  - [{test.get('id')}] {test.get('name', '')}")
    if len(tests) > 5:
        click.echo(f"  ... and {len(tests) - 5} more")
    
    # Glossary
    glossary = spec.get('glossary', {})
    if glossary:
        click.echo(f"\nGlossary ({len(glossary)} terms):")
        for term, definition in list(glossary.items())[:5]:
            click.echo(f"  - {term}: {definition[:40]}...")
    
    click.echo(f"\n{'='*60}")



# ============================================================================
# Requirement Commands
# ============================================================================

@click.group(name='req')
def req_group():
    """Manage requirements within specifications.
    
    Commands for parsing, validating, and managing EARS-formatted requirements.
    
    Examples:
        # Parse a requirement
        agentic-test req parse "WHEN user logs in, THE System SHALL authenticate"
        
        # Add requirement to specification
        agentic-test req add <spec-id> "WHEN..."
        
        # Validate requirements
        agentic-test req validate <spec-id>
    """
    pass


@req_group.command('parse')
@click.argument('text')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def parse_requirement(ctx, text, as_json):
    """Parse an EARS-formatted requirement.
    
    TEXT is the EARS-formatted requirement text.
    
    Examples:
        agentic-test req parse "WHEN user logs in, THE System SHALL authenticate"
        agentic-test req parse "WHILE system is running, THE Monitor SHALL track metrics"
    """
    try:
        client = get_client(ctx)
        response = client.post('/specifications/requirements/parse', json={'text': text})
        
        if response.get('success'):
            data = response.get('data', {})
            parsed = data.get('parsed_requirement', {})
            
            if as_json:
                click.echo(json.dumps(parsed, indent=2))
            else:
                click.echo(f"\n✅ Parsed Requirement:")
                click.echo(f"   Pattern: {parsed.get('pattern', 'unknown')}")
                if parsed.get('trigger'):
                    click.echo(f"   Trigger: {parsed.get('trigger')}")
                if parsed.get('state'):
                    click.echo(f"   State: {parsed.get('state')}")
                click.echo(f"   System: {parsed.get('system', '')}")
                click.echo(f"   Response: {parsed.get('response', '')}")
        else:
            click.echo(f"❌ Failed to parse: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@req_group.command('add')
@click.argument('spec_id')
@click.argument('text')
@click.pass_context
def add_requirement(ctx, spec_id, text):
    """Add a requirement to a specification.
    
    SPEC_ID is the specification identifier.
    TEXT is the EARS-formatted requirement text.
    
    Examples:
        agentic-test req add spec_abc123 "WHEN user logs in, THE System SHALL authenticate"
    """
    try:
        client = get_client(ctx)
        response = client.post(f'/specifications/{spec_id}/requirements', json={'text': text})
        
        if response.get('success'):
            data = response.get('data', {})
            req = data.get('requirement', {})
            validation = data.get('validation', {})
            
            click.echo(f"✅ Added requirement: {req.get('id')}")
            
            if not validation.get('is_valid'):
                click.echo("\n⚠️  Validation warnings:")
                for issue in validation.get('issues', []):
                    click.echo(f"   - {issue}")
        else:
            click.echo(f"❌ Failed to add requirement: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@req_group.command('validate')
@click.argument('spec_id')
@click.pass_context
def validate_requirements(ctx, spec_id):
    """Validate all requirements in a specification.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test req validate spec_abc123
    """
    try:
        client = get_client(ctx)
        
        # Get specification
        spec_response = client.get(f'/specifications/{spec_id}')
        if not spec_response.get('success'):
            click.echo(f"❌ Specification not found: {spec_id}", err=True)
            return
        
        spec = spec_response.get('data', {})
        requirements = spec.get('requirements', [])
        glossary = spec.get('glossary', {})
        
        if not requirements:
            click.echo("No requirements to validate.")
            return
        
        valid_count = 0
        invalid_count = 0
        
        click.echo(f"\nValidating {len(requirements)} requirements...\n")
        
        for req in requirements:
            response = client.post('/specifications/requirements/validate', json={
                'text': req.get('text', ''),
                'glossary': glossary
            })
            
            if response.get('success'):
                data = response.get('data', {})
                is_valid = data.get('is_valid', False)
                
                if is_valid:
                    valid_count += 1
                    click.echo(f"  ✅ {req.get('id')}")
                else:
                    invalid_count += 1
                    click.echo(f"  ❌ {req.get('id')}")
                    for issue in data.get('issues', []):
                        click.echo(f"     - {issue}")
        
        click.echo(f"\nSummary: {valid_count} valid, {invalid_count} invalid")
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))



# ============================================================================
# Generation Commands
# ============================================================================

@click.group(name='generate')
def generate_group():
    """Generate properties and tests from specifications.
    
    Commands for generating correctness properties and property-based tests.
    
    Examples:
        # Generate properties from requirements
        agentic-test generate properties <spec-id>
        
        # Generate tests from properties
        agentic-test generate tests <spec-id> --output tests/property/
    """
    pass


@generate_group.command('properties')
@click.argument('spec_id')
@click.option('--requirement', '-r', 'req_id', help='Generate for specific requirement')
@click.pass_context
def generate_properties(ctx, spec_id, req_id):
    """Generate correctness properties from requirements.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test generate properties spec_abc123
        agentic-test generate properties spec_abc123 -r req_001
    """
    try:
        client = get_client(ctx)
        
        data = {}
        if req_id:
            data['requirement_id'] = req_id
        
        response = client.post(f'/specifications/{spec_id}/properties/generate', json=data)
        
        if response.get('success'):
            result = response.get('data', {})
            properties = result.get('properties', [])
            
            click.echo(f"✅ Generated {len(properties)} properties")
            
            for prop in properties:
                click.echo(f"\n  [{prop.get('id')}] {prop.get('name')}")
                click.echo(f"     Pattern: {prop.get('pattern')}")
                click.echo(f"     Validates: {', '.join(prop.get('requirement_ids', []))}")
        else:
            click.echo(f"❌ Failed to generate properties: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@generate_group.command('tests')
@click.argument('spec_id')
@click.option('--property', '-p', 'prop_ids', multiple=True, help='Generate for specific properties')
@click.option('--output', '-o', help='Output directory for test files')
@click.option('--iterations', '-i', default=100, help='Number of test iterations')
@click.pass_context
def generate_tests(ctx, spec_id, prop_ids, output, iterations):
    """Generate property-based tests from properties.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test generate tests spec_abc123
        agentic-test generate tests spec_abc123 --output tests/property/
        agentic-test generate tests spec_abc123 -p prop_001 -p prop_002
    """
    try:
        client = get_client(ctx)
        
        data = {'iterations': iterations}
        if prop_ids:
            data['property_ids'] = list(prop_ids)
        if output:
            data['output_path'] = output
        
        response = client.post(f'/specifications/{spec_id}/tests/generate', json=data)
        
        if response.get('success'):
            result = response.get('data', {})
            tests = result.get('tests', [])
            output_path = result.get('output_path')
            
            click.echo(f"✅ Generated {len(tests)} tests")
            
            for test in tests:
                click.echo(f"\n  [{test.get('id')}] {test.get('name')}")
                click.echo(f"     Property: {test.get('property_id')}")
                click.echo(f"     Iterations: {test.get('iterations')}")
            
            if output_path:
                click.echo(f"\n  Output: {output_path}")
        else:
            click.echo(f"❌ Failed to generate tests: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


# ============================================================================
# Execution Commands
# ============================================================================

@click.group(name='run')
def run_group():
    """Execute property-based tests.
    
    Commands for running property tests and viewing results.
    
    Examples:
        # Run all tests for a specification
        agentic-test run spec <spec-id>
        
        # Run specific test
        agentic-test run test <test-id>
    """
    pass


@run_group.command('spec')
@click.argument('spec_id')
@click.option('--iterations', '-i', default=100, help='Number of test iterations')
@click.option('--parallel/--sequential', default=True, help='Run tests in parallel')
@click.option('--timeout', '-t', default=300, help='Test timeout in seconds')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def run_spec(ctx, spec_id, iterations, parallel, timeout, verbose):
    """Run all property tests for a specification.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test run spec spec_abc123
        agentic-test run spec spec_abc123 --iterations 500 --verbose
    """
    try:
        client = get_client(ctx)
        
        click.echo(f"Running tests for specification {spec_id}...")
        click.echo(f"  Iterations: {iterations}")
        click.echo(f"  Parallel: {parallel}")
        click.echo(f"  Timeout: {timeout}s")
        click.echo()
        
        response = client.post('/specifications/tests/execute', 
            params={'spec_id': spec_id},
            json={
                'iterations': iterations,
                'parallel': parallel,
                'timeout_seconds': timeout,
            }
        )
        
        if response.get('success'):
            result = response.get('data', {})
            results = result.get('results', [])
            summary = result.get('summary', {})
            
            # Display results
            for r in results:
                status = "✅ PASS" if r.get('passed') else "❌ FAIL"
                click.echo(f"  {status} {r.get('test_id')}")
                
                if verbose and not r.get('passed'):
                    if r.get('error_message'):
                        click.echo(f"       Error: {r.get('error_message')[:100]}...")
                    if r.get('counter_example'):
                        click.echo(f"       Counter-example: {r.get('counter_example')}")
            
            # Summary
            click.echo(f"\n{'='*50}")
            click.echo(f"Results: {summary.get('passed', 0)}/{summary.get('total', 0)} passed")
            click.echo(f"Pass rate: {summary.get('pass_rate', 0)*100:.1f}%")
        else:
            click.echo(f"❌ Failed to run tests: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@run_group.command('test')
@click.argument('test_id')
@click.option('--spec-id', required=True, help='Specification ID')
@click.option('--iterations', '-i', default=100, help='Number of test iterations')
@click.pass_context
def run_test(ctx, test_id, spec_id, iterations):
    """Run a single property test.
    
    TEST_ID is the test identifier.
    
    Examples:
        agentic-test run test test_001 --spec-id spec_abc123
    """
    try:
        client = get_client(ctx)
        
        click.echo(f"Running test {test_id}...")
        
        response = client.post('/specifications/tests/execute',
            params={'spec_id': spec_id},
            json={
                'test_ids': [test_id],
                'iterations': iterations,
            }
        )
        
        if response.get('success'):
            results = response.get('data', {}).get('results', [])
            
            if results:
                r = results[0]
                if r.get('passed'):
                    click.echo(f"\n✅ PASSED ({r.get('iterations_run')} iterations)")
                else:
                    click.echo(f"\n❌ FAILED")
                    if r.get('error_message'):
                        click.echo(f"   Error: {r.get('error_message')}")
                    if r.get('counter_example'):
                        click.echo(f"   Counter-example: {r.get('counter_example')}")
                    if r.get('shrunk_example'):
                        click.echo(f"   Shrunk example: {r.get('shrunk_example')}")
        else:
            click.echo(f"❌ Failed to run test: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


# ============================================================================
# Reporting Commands
# ============================================================================

@click.group(name='report')
def report_group():
    """Generate reports for specifications.
    
    Commands for generating coverage and traceability reports.
    
    Examples:
        # Coverage report
        agentic-test report coverage <spec-id>
        
        # Traceability report
        agentic-test report traceability <spec-id>
        
        # Failures report
        agentic-test report failures <spec-id>
    """
    pass


@report_group.command('coverage')
@click.argument('spec_id')
@click.option('--format', '-f', 'fmt', default='text',
              type=click.Choice(['text', 'json', 'markdown']),
              help='Output format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def report_coverage(ctx, spec_id, fmt, output):
    """Generate a coverage report for a specification.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test report coverage spec_abc123
        agentic-test report coverage spec_abc123 --format markdown -o coverage.md
    """
    try:
        client = get_client(ctx)
        response = client.get(f'/specifications/traceability/matrix/{spec_id}')
        
        if response.get('success'):
            matrix = response.get('data', {})
            
            if fmt == 'json':
                content = json.dumps(matrix, indent=2)
            elif fmt == 'markdown':
                content = _format_coverage_markdown(matrix)
            else:
                content = _format_coverage_text(matrix)
            
            if output:
                Path(output).write_text(content)
                click.echo(f"✅ Report saved to: {output}")
            else:
                click.echo(content)
        else:
            click.echo(f"❌ Failed to generate report: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@report_group.command('traceability')
@click.argument('spec_id')
@click.option('--format', '-f', 'fmt', default='json',
              type=click.Choice(['json', 'markdown', 'html']),
              help='Output format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def report_traceability(ctx, spec_id, fmt, output):
    """Generate a traceability report for a specification.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test report traceability spec_abc123
        agentic-test report traceability spec_abc123 --format html -o report.html
    """
    try:
        client = get_client(ctx)
        response = client.get(f'/specifications/{spec_id}/traceability/report',
                             params={'format': fmt})
        
        if response.get('success'):
            data = response.get('data', {})
            
            if fmt in ['markdown', 'html']:
                content = data.get('content', '')
            else:
                content = json.dumps(data, indent=2)
            
            if output:
                Path(output).write_text(content)
                click.echo(f"✅ Report saved to: {output}")
            else:
                click.echo(content)
        else:
            click.echo(f"❌ Failed to generate report: {response.get('message')}", err=True)
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@report_group.command('failures')
@click.argument('spec_id')
@click.pass_context
def report_failures(ctx, spec_id):
    """Show failed tests and their counter-examples.
    
    SPEC_ID is the specification identifier.
    
    Examples:
        agentic-test report failures spec_abc123
    """
    try:
        client = get_client(ctx)
        
        # Get specification tests
        response = client.get(f'/specifications/{spec_id}/tests')
        
        if not response.get('success'):
            click.echo(f"❌ Failed to get tests: {response.get('message')}", err=True)
            return
        
        tests = response.get('data', {}).get('tests', [])
        
        if not tests:
            click.echo("No tests found.")
            return
        
        # Get results for each test
        failures = []
        for test in tests:
            results_response = client.get(
                f'/specifications/{spec_id}/tests/{test.get("id")}/results',
                params={'limit': 1}
            )
            if results_response.get('success'):
                results = results_response.get('data', {}).get('results', [])
                if results and not results[0].get('passed'):
                    failures.append({
                        'test': test,
                        'result': results[0]
                    })
        
        if not failures:
            click.echo("✅ No failures found!")
            return
        
        click.echo(f"\n❌ {len(failures)} Failed Tests:\n")
        
        for f in failures:
            test = f['test']
            result = f['result']
            
            click.echo(f"  Test: {test.get('name')}")
            click.echo(f"  ID: {test.get('id')}")
            click.echo(f"  Property: {test.get('property_id')}")
            click.echo(f"  Requirements: {', '.join(test.get('requirement_ids', []))}")
            
            if result.get('error_message'):
                click.echo(f"  Error: {result.get('error_message')[:200]}")
            if result.get('counter_example'):
                click.echo(f"  Counter-example: {result.get('counter_example')}")
            if result.get('shrunk_example'):
                click.echo(f"  Shrunk: {result.get('shrunk_example')}")
            
            click.echo()
            
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


def _format_coverage_text(matrix: dict) -> str:
    """Format coverage matrix as text."""
    lines = [
        "=" * 60,
        "Coverage Report",
        "=" * 60,
        f"Specification: {matrix.get('spec_id', 'Unknown')}",
        f"Coverage: {matrix.get('coverage_percentage', 0):.1f}%",
        "",
        "Requirements:",
        "-" * 40,
    ]
    
    coverage = matrix.get('coverage', {})
    for req_id in matrix.get('requirements', []):
        tests = coverage.get(req_id, [])
        status = "✓" if tests else "✗"
        lines.append(f"  {status} {req_id}: {len(tests)} test(s)")
    
    untested = matrix.get('untested', [])
    if untested:
        lines.extend([
            "",
            f"Untested Requirements ({len(untested)}):",
            "-" * 40,
        ])
        for req_id in untested:
            lines.append(f"  - {req_id}")
    
    orphaned = matrix.get('orphaned_tests', [])
    if orphaned:
        lines.extend([
            "",
            f"Orphaned Tests ({len(orphaned)}):",
            "-" * 40,
        ])
        for test_id in orphaned:
            lines.append(f"  - {test_id}")
    
    lines.append("=" * 60)
    return '\n'.join(lines)


def _format_coverage_markdown(matrix: dict) -> str:
    """Format coverage matrix as markdown."""
    lines = [
        "# Coverage Report",
        "",
        f"**Specification:** {matrix.get('spec_id', 'Unknown')}",
        f"**Coverage:** {matrix.get('coverage_percentage', 0):.1f}%",
        "",
        "## Requirements Coverage",
        "",
        "| Requirement | Tests | Status |",
        "|-------------|-------|--------|",
    ]
    
    coverage = matrix.get('coverage', {})
    for req_id in matrix.get('requirements', []):
        tests = coverage.get(req_id, [])
        status = "✅" if tests else "❌"
        test_list = ", ".join(tests[:3])
        if len(tests) > 3:
            test_list += f" (+{len(tests) - 3})"
        lines.append(f"| {req_id} | {test_list or 'None'} | {status} |")
    
    untested = matrix.get('untested', [])
    if untested:
        lines.extend([
            "",
            "## Untested Requirements",
            "",
        ])
        for req_id in untested:
            lines.append(f"- {req_id}")
    
    return '\n'.join(lines)
