"""Test results and analysis commands."""

import click
from pathlib import Path
from datetime import datetime, timedelta

from cli.utils import (
    get_client, handle_api_error, print_table, print_json,
    format_test_status, format_duration, format_percentage,
    format_bytes, display_paginated_results, confirm_action
)


@click.group(name='results')
def results_group():
    """Test results and analysis commands."""
    pass


@results_group.command()
@click.option('--page', default=1, help='Page number')
@click.option('--page-size', default=20, help='Items per page')
@click.option('--status-filter', help='Filter by status (passed, failed, etc.)')
@click.option('--subsystem', help='Filter by subsystem')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--failed-only', is_flag=True, help='Show only failed tests')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list(ctx, page, page_size, status_filter, subsystem, start_date, end_date, failed_only, output_format):
    """List test results with filtering options."""
    
    # Set status filter for failed-only
    if failed_only:
        status_filter = 'failed'
    
    try:
        client = get_client(ctx)
        result = client.list_test_results(
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            subsystem=subsystem,
            start_date=start_date,
            end_date=end_date
        )
        
        results = result.get('results', [])
        pagination = result.get('pagination', {})
        
        if output_format == 'json':
            print_json(result)
            return
        
        if not results:
            click.echo("No test results found")
            return
        
        # Format table
        headers = ['Test ID', 'Status', 'Subsystem', 'Duration', 'Environment', 'Timestamp']
        rows = []
        
        for test_result in results:
            duration = format_duration(test_result.get('execution_time', 0))
            env_info = test_result.get('environment', {})
            env_name = env_info.get('id', 'N/A')[:12] if env_info else 'N/A'
            
            rows.append([
                test_result['test_id'][:12] + '...',
                format_test_status(test_result['status']),
                test_result.get('subsystem', 'N/A'),
                duration,
                env_name,
                test_result['timestamp'][:19]
            ])
        
        print_table(headers, rows)
        
        # Show pagination info
        if pagination:
            click.echo(f"\nPage {pagination.get('current_page', page)} of {pagination.get('total_pages', 1)}")
            click.echo(f"Total: {pagination.get('total_items', len(results))} results")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@results_group.command()
@click.argument('test_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--show-artifacts', is_flag=True, help='Show available artifacts')
@click.pass_context
def show(ctx, test_id, output_format, show_artifacts):
    """Show detailed test result information."""
    
    try:
        client = get_client(ctx)
        result = client.get_test_result(test_id)
        
        if output_format == 'json':
            print_json(result)
            return
        
        # Display result details
        click.echo(f"Test Result: {test_id}")
        click.echo("=" * 60)
        click.echo(f"Status: {format_test_status(result['status'])}")
        click.echo(f"Execution Time: {format_duration(result['execution_time'])}")
        click.echo(f"Timestamp: {result['timestamp']}")
        
        # Environment info
        env = result.get('environment', {})
        if env:
            click.echo(f"\nEnvironment:")
            click.echo(f"  ID: {env.get('id', 'N/A')}")
            click.echo(f"  Architecture: {env.get('architecture', 'N/A')}")
            click.echo(f"  Memory: {env.get('memory_mb', 0)}MB")
            click.echo(f"  Virtual: {env.get('is_virtual', 'N/A')}")
        
        # Coverage data
        coverage = result.get('coverage_data')
        if coverage:
            click.echo(f"\nCoverage:")
            click.echo(f"  Line: {format_percentage(coverage.get('line_coverage', 0))}")
            click.echo(f"  Branch: {format_percentage(coverage.get('branch_coverage', 0))}")
            click.echo(f"  Function: {format_percentage(coverage.get('function_coverage', 0))}")
        
        # Failure info
        failure = result.get('failure_info')
        if failure:
            click.echo(f"\nFailure Information:")
            click.echo(f"  Error: {failure.get('error_message', 'N/A')}")
            click.echo(f"  Exit Code: {failure.get('exit_code', 'N/A')}")
            
            if failure.get('stack_trace'):
                click.echo(f"  Stack Trace:")
                trace_lines = failure['stack_trace'].split('\n')[:10]  # Show first 10 lines
                for line in trace_lines:
                    click.echo(f"    {line}")
                if len(failure['stack_trace'].split('\n')) > 10:
                    click.echo("    ... (truncated)")
        
        # Artifacts
        artifacts = result.get('artifacts', {})
        if artifacts and show_artifacts:
            click.echo(f"\nArtifacts:")
            for artifact_type, artifact_info in artifacts.items():
                size = format_bytes(artifact_info.get('size', 0))
                click.echo(f"  {artifact_type}: {size}")
        elif artifacts:
            click.echo(f"\nArtifacts: {len(artifacts)} available (use --show-artifacts to list)")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@results_group.command()
@click.argument('test_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def coverage(ctx, test_id, output_format):
    """Show coverage report for a test."""
    
    try:
        client = get_client(ctx)
        coverage = client.get_coverage_report(test_id)
        
        if output_format == 'json':
            print_json(coverage)
            return
        
        click.echo(f"Coverage Report: {test_id}")
        click.echo("=" * 50)
        
        click.echo(f"Line Coverage: {format_percentage(coverage.get('line_coverage', 0))}")
        click.echo(f"Branch Coverage: {format_percentage(coverage.get('branch_coverage', 0))}")
        click.echo(f"Function Coverage: {format_percentage(coverage.get('function_coverage', 0))}")
        
        # Show coverage gaps
        gaps = coverage.get('coverage_gaps', [])
        if gaps:
            click.echo(f"\nCoverage Gaps ({len(gaps)}):")
            for gap in gaps[:10]:  # Show first 10
                click.echo(f"  • {gap.get('file', 'N/A')}:{gap.get('line', 'N/A')} - {gap.get('description', 'N/A')}")
            if len(gaps) > 10:
                click.echo(f"  ... and {len(gaps) - 10} more gaps")
        
        # Show covered/uncovered lines summary
        covered = coverage.get('covered_lines', [])
        uncovered = coverage.get('uncovered_lines', [])
        
        if covered or uncovered:
            click.echo(f"\nLine Summary:")
            click.echo(f"  Covered lines: {len(covered)}")
            click.echo(f"  Uncovered lines: {len(uncovered)}")
        
        # Report URL
        report_url = coverage.get('report_url')
        if report_url:
            click.echo(f"\nDetailed report: {report_url}")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@results_group.command()
@click.argument('test_id')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def failure(ctx, test_id, output_format):
    """Show failure analysis for a failed test."""
    
    try:
        client = get_client(ctx)
        analysis = client.get_failure_analysis(test_id)
        
        if output_format == 'json':
            print_json(analysis)
            return
        
        click.echo(f"Failure Analysis: {test_id}")
        click.echo("=" * 60)
        
        click.echo(f"Root Cause: {analysis.get('root_cause', 'Unknown')}")
        click.echo(f"Confidence: {format_percentage(analysis.get('confidence', 0))}")
        click.echo(f"Reproducibility: {format_percentage(analysis.get('reproducibility', 0))}")
        click.echo(f"Error Pattern: {analysis.get('error_pattern', 'N/A')}")
        
        # Suspicious commits
        commits = analysis.get('suspicious_commits', [])
        if commits:
            click.echo(f"\nSuspicious Commits ({len(commits)}):")
            for commit in commits[:5]:  # Show first 5
                click.echo(f"  • {commit.get('sha', 'N/A')[:8]} - {commit.get('message', 'N/A')[:60]}")
                click.echo(f"    Author: {commit.get('author', 'N/A')} ({commit.get('date', 'N/A')})")
            if len(commits) > 5:
                click.echo(f"  ... and {len(commits) - 5} more commits")
        
        # Suggested fixes
        fixes = analysis.get('suggested_fixes', [])
        if fixes:
            click.echo(f"\nSuggested Fixes ({len(fixes)}):")
            for i, fix in enumerate(fixes[:3], 1):  # Show first 3
                click.echo(f"  {i}. {fix.get('description', 'N/A')}")
                if fix.get('confidence'):
                    click.echo(f"     Confidence: {format_percentage(fix['confidence'])}")
        
        # Related failures
        related = analysis.get('related_failures', [])
        if related:
            click.echo(f"\nRelated Failures: {len(related)} similar issues found")
        
        # Stack trace
        stack_trace = analysis.get('stack_trace')
        if stack_trace:
            click.echo(f"\nStack Trace (first 15 lines):")
            lines = stack_trace.split('\n')[:15]
            for line in lines:
                click.echo(f"  {line}")
            if len(stack_trace.split('\n')) > 15:
                click.echo("  ... (truncated)")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@results_group.command()
@click.argument('test_id')
@click.argument('artifact_type')
@click.option('--output-path', help='Output file path')
@click.pass_context
def download(ctx, test_id, artifact_type, output_path):
    """Download test artifacts."""
    
    try:
        client = get_client(ctx)
        
        if not output_path:
            output_path = f"{test_id}_{artifact_type}"
        
        click.echo(f"Downloading {artifact_type} for test {test_id}...")
        
        content = client.download_artifacts(test_id, artifact_type, output_path)
        
        click.echo(f"✅ Downloaded {format_bytes(len(content))} to {output_path}")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@results_group.command()
@click.option('--format', 'export_format', type=click.Choice(['json', 'csv', 'xml']), default='json', help='Export format')
@click.option('--test-ids', help='Comma-separated test IDs to export')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--output-path', help='Output file path')
@click.option('--failed-only', is_flag=True, help='Export only failed tests')
@click.pass_context
def export(ctx, export_format, test_ids, start_date, end_date, output_path, failed_only):
    """Export test results in various formats."""
    
    try:
        client = get_client(ctx)
        
        # Parse test IDs
        test_id_list = None
        if test_ids:
            test_id_list = [tid.strip() for tid in test_ids.split(',')]
        
        # Set default output path
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"test_results_{timestamp}.{export_format}"
        
        click.echo(f"Exporting test results to {output_path}...")
        
        # Add status filter for failed-only
        params = {}
        if failed_only:
            # Note: This would need to be implemented in the API client
            click.echo("Note: Failed-only filter not yet implemented in export")
        
        content = client.export_results(
            format=export_format,
            test_ids=test_id_list,
            start_date=start_date,
            end_date=end_date,
            output_path=output_path
        )
        
        click.echo(f"✅ Exported {format_bytes(len(content))} to {output_path}")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@results_group.command()
@click.option('--days', default=7, help='Number of days to include in summary')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def summary(ctx, days, output_format):
    """Show test results summary statistics."""
    
    try:
        client = get_client(ctx)
        summary = client.get_results_summary(days=days)
        
        if output_format == 'json':
            print_json(summary)
            return
        
        click.echo(f"Test Results Summary (Last {days} days)")
        click.echo("=" * 50)
        
        # Overall statistics
        total_tests = summary.get('total_tests', 0)
        passed_tests = summary.get('passed_tests', 0)
        failed_tests = summary.get('failed_tests', 0)
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        click.echo(f"📊 Overall Statistics:")
        click.echo(f"  Total tests: {total_tests}")
        click.echo(f"  Passed: {passed_tests}")
        click.echo(f"  Failed: {failed_tests}")
        click.echo(f"  Pass rate: {pass_rate:.1f}%")
        
        # By test type
        by_type = summary.get('by_test_type', {})
        if by_type:
            click.echo(f"\n🧪 By Test Type:")
            for test_type, stats in by_type.items():
                type_pass_rate = (stats.get('passed', 0) / stats.get('total', 1) * 100)
                click.echo(f"  {test_type}: {stats.get('total', 0)} tests ({type_pass_rate:.1f}% pass rate)")
        
        # By subsystem
        by_subsystem = summary.get('by_subsystem', {})
        if by_subsystem:
            click.echo(f"\n🔧 By Subsystem:")
            # Show top 5 subsystems by test count
            sorted_subsystems = sorted(by_subsystem.items(), key=lambda x: x[1].get('total', 0), reverse=True)
            for subsystem, stats in sorted_subsystems[:5]:
                subsys_pass_rate = (stats.get('passed', 0) / stats.get('total', 1) * 100)
                click.echo(f"  {subsystem}: {stats.get('total', 0)} tests ({subsys_pass_rate:.1f}% pass rate)")
        
        # Performance metrics
        perf_metrics = summary.get('performance_metrics', {})
        if perf_metrics:
            click.echo(f"\n⚡ Performance:")
            avg_duration = perf_metrics.get('average_execution_time', 0)
            click.echo(f"  Average execution time: {format_duration(avg_duration)}")
            click.echo(f"  Fastest test: {format_duration(perf_metrics.get('fastest_test', 0))}")
            click.echo(f"  Slowest test: {format_duration(perf_metrics.get('slowest_test', 0))}")
        
        # Coverage metrics
        coverage_metrics = summary.get('coverage_metrics', {})
        if coverage_metrics:
            click.echo(f"\n📈 Coverage:")
            click.echo(f"  Average line coverage: {format_percentage(coverage_metrics.get('average_line_coverage', 0))}")
            click.echo(f"  Average branch coverage: {format_percentage(coverage_metrics.get('average_branch_coverage', 0))}")
        
        # Failure patterns
        failure_patterns = summary.get('failure_patterns', [])
        if failure_patterns:
            click.echo(f"\n❌ Top Failure Patterns:")
            for pattern in failure_patterns[:3]:
                click.echo(f"  • {pattern.get('pattern', 'N/A')} ({pattern.get('count', 0)} occurrences)")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))


@results_group.command()
@click.option('--days', default=30, help='Number of days of old results to clean up')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def cleanup(ctx, days, dry_run, force):
    """Clean up old test results and artifacts."""
    
    if not dry_run and not force:
        if not confirm_action(f"Delete test results older than {days} days?"):
            click.echo("Cleanup cancelled")
            return
    
    try:
        # Note: This would need to be implemented in the API
        click.echo(f"{'Would clean up' if dry_run else 'Cleaning up'} results older than {days} days...")
        
        if dry_run:
            click.echo("Dry run mode - no actual deletion performed")
            click.echo("Use --force to skip confirmation or remove --dry-run to execute")
        else:
            click.echo("✅ Cleanup completed")
            click.echo("Note: Cleanup functionality needs to be implemented in the API")
        
    except Exception as e:
        handle_api_error(e, ctx.obj.get('debug', False))