"""End-to-end integration test runner.

This module provides a comprehensive test runner for executing all end-to-end
integration tests and generating detailed reports.
"""

import pytest
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class TestExecutionResult:
    """Result of test execution."""
    test_name: str
    status: str  # passed, failed, skipped, error
    duration: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class TestSuiteResult:
    """Result of test suite execution."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    pass_rate: float
    test_results: List[TestExecutionResult]
    
    def __post_init__(self):
        if self.total_tests > 0:
            self.pass_rate = (self.passed / self.total_tests) * 100
        else:
            self.pass_rate = 0.0


class EndToEndTestRunner:
    """Comprehensive end-to-end test runner."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize test runner.
        
        Args:
            output_dir: Directory for test outputs and reports
        """
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Test suites to run
        self.test_suites = {
            'end_to_end_workflows': {
                'module': 'tests.integration.test_end_to_end_workflows',
                'description': 'Complete end-to-end workflow tests',
                'tests': [
                    'TestEndToEndWorkflows::test_complete_code_change_to_results_workflow',
                    'TestEndToEndWorkflows::test_multi_hardware_compatibility_testing',
                    'TestEndToEndWorkflows::test_fault_injection_and_recovery_workflow',
                    'TestEndToEndWorkflows::test_ci_cd_integration_workflow',
                    'TestEndToEndWorkflows::test_performance_regression_detection_workflow',
                    'TestEndToEndWorkflows::test_security_testing_workflow'
                ]
            },
            'system_integration': {
                'module': 'tests.integration.test_end_to_end_workflows',
                'description': 'System integration tests',
                'tests': [
                    'TestSystemIntegration::test_api_client_integration',
                    'TestSystemIntegration::test_database_integration',
                    'TestSystemIntegration::test_concurrent_test_execution',
                    'TestSystemIntegration::test_error_handling_and_recovery'
                ]
            },
            'system_workflows': {
                'module': 'tests.integration.test_system_workflows',
                'description': 'System workflow tests',
                'tests': [
                    'TestCodeAnalysisWorkflow::test_git_diff_to_test_generation_workflow',
                    'TestCodeAnalysisWorkflow::test_multi_subsystem_analysis_workflow',
                    'TestTestExecutionWorkflow::test_parallel_execution_across_architectures',
                    'TestTestExecutionWorkflow::test_test_retry_and_failure_handling',
                    'TestTestExecutionWorkflow::test_resource_allocation_and_cleanup',
                    'TestAnalysisWorkflow::test_coverage_analysis_workflow',
                    'TestAnalysisWorkflow::test_failure_analysis_workflow',
                    'TestAnalysisWorkflow::test_performance_regression_analysis_workflow',
                    'TestAnalysisWorkflow::test_security_analysis_workflow',
                    'TestNotificationWorkflow::test_failure_notification_workflow',
                    'TestNotificationWorkflow::test_vcs_status_reporting_workflow'
                ]
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('e2e_test_runner')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self.output_dir / 'test_execution.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def run_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> TestSuiteResult:
        """Run a specific test suite.
        
        Args:
            suite_name: Name of the test suite
            suite_config: Configuration for the test suite
            
        Returns:
            Test suite results
        """
        self.logger.info(f"Starting test suite: {suite_name}")
        self.logger.info(f"Description: {suite_config['description']}")
        
        start_time = time.time()
        test_results = []
        
        for test_name in suite_config['tests']:
            self.logger.info(f"Running test: {test_name}")
            
            test_start_time = time.time()
            
            try:
                # Run individual test using pytest
                result = self._run_individual_test(suite_config['module'], test_name)
                test_duration = time.time() - test_start_time
                
                test_result = TestExecutionResult(
                    test_name=test_name,
                    status=result['status'],
                    duration=test_duration,
                    error_message=result.get('error_message'),
                    details=result.get('details', {})
                )
                
                self.logger.info(f"Test {test_name}: {result['status']} ({test_duration:.2f}s)")
                
            except Exception as e:
                test_duration = time.time() - test_start_time
                test_result = TestExecutionResult(
                    test_name=test_name,
                    status='error',
                    duration=test_duration,
                    error_message=str(e)
                )
                
                self.logger.error(f"Test {test_name} failed with error: {e}")
            
            test_results.append(test_result)
        
        # Calculate suite statistics
        total_duration = time.time() - start_time
        total_tests = len(test_results)
        passed = len([r for r in test_results if r.status == 'passed'])
        failed = len([r for r in test_results if r.status == 'failed'])
        skipped = len([r for r in test_results if r.status == 'skipped'])
        errors = len([r for r in test_results if r.status == 'error'])
        
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=total_duration,
            pass_rate=(passed / total_tests * 100) if total_tests > 0 else 0.0,
            test_results=test_results
        )
        
        self.logger.info(f"Suite {suite_name} completed: {passed}/{total_tests} passed ({suite_result.pass_rate:.1f}%)")
        
        return suite_result
    
    def _run_individual_test(self, module: str, test_name: str) -> Dict[str, Any]:
        """Run an individual test using pytest.
        
        Args:
            module: Module containing the test
            test_name: Name of the test to run
            
        Returns:
            Test result dictionary
        """
        # Construct pytest command
        test_path = f"{module}::{test_name}"
        
        # Run pytest programmatically
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_report_file = f.name
        
        try:
            # Run pytest with JSON report
            cmd = [
                sys.executable, '-m', 'pytest',
                test_path,
                '--tb=short',
                '--json-report',
                f'--json-report-file={json_report_file}',
                '-v'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test
            )
            
            # Parse JSON report
            try:
                with open(json_report_file, 'r') as f:
                    report_data = json.load(f)
                
                if report_data['tests']:
                    test_data = report_data['tests'][0]
                    return {
                        'status': 'passed' if test_data['outcome'] == 'passed' else test_data['outcome'],
                        'error_message': test_data.get('call', {}).get('longrepr') if test_data['outcome'] != 'passed' else None,
                        'details': {
                            'duration': test_data.get('duration', 0),
                            'setup_duration': test_data.get('setup', {}).get('duration', 0),
                            'call_duration': test_data.get('call', {}).get('duration', 0),
                            'teardown_duration': test_data.get('teardown', {}).get('duration', 0)
                        }
                    }
                else:
                    return {
                        'status': 'error',
                        'error_message': 'No test results found in report'
                    }
                    
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                # Fallback to parsing stdout/stderr
                if result.returncode == 0:
                    return {'status': 'passed'}
                else:
                    return {
                        'status': 'failed',
                        'error_message': result.stderr or result.stdout
                    }
        
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'error_message': 'Test execution timed out after 5 minutes'
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'Test execution failed: {str(e)}'
            }
        
        finally:
            # Clean up temporary file
            try:
                Path(json_report_file).unlink()
            except:
                pass
    
    def run_all_suites(self) -> Dict[str, TestSuiteResult]:
        """Run all test suites.
        
        Returns:
            Dictionary of suite results
        """
        self.logger.info("Starting end-to-end integration test execution")
        self.logger.info(f"Output directory: {self.output_dir}")
        
        overall_start_time = time.time()
        suite_results = {}
        
        for suite_name, suite_config in self.test_suites.items():
            try:
                suite_result = self.run_test_suite(suite_name, suite_config)
                suite_results[suite_name] = suite_result
                
                # Save individual suite report
                self._save_suite_report(suite_result)
                
            except Exception as e:
                self.logger.error(f"Failed to run test suite {suite_name}: {e}")
                # Create error result
                suite_results[suite_name] = TestSuiteResult(
                    suite_name=suite_name,
                    total_tests=len(suite_config['tests']),
                    passed=0,
                    failed=0,
                    skipped=0,
                    errors=len(suite_config['tests']),
                    duration=0.0,
                    pass_rate=0.0,
                    test_results=[]
                )
        
        overall_duration = time.time() - overall_start_time
        
        # Generate comprehensive report
        self._generate_comprehensive_report(suite_results, overall_duration)
        
        self.logger.info(f"End-to-end test execution completed in {overall_duration:.2f} seconds")
        
        return suite_results
    
    def _save_suite_report(self, suite_result: TestSuiteResult) -> None:
        """Save individual suite report.
        
        Args:
            suite_result: Suite result to save
        """
        report_file = self.output_dir / f"{suite_result.suite_name}_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(asdict(suite_result), f, indent=2, default=str)
        
        self.logger.info(f"Suite report saved: {report_file}")
    
    def _generate_comprehensive_report(
        self, 
        suite_results: Dict[str, TestSuiteResult], 
        overall_duration: float
    ) -> None:
        """Generate comprehensive test report.
        
        Args:
            suite_results: Results from all test suites
            overall_duration: Total execution duration
        """
        # Calculate overall statistics
        total_tests = sum(suite.total_tests for suite in suite_results.values())
        total_passed = sum(suite.passed for suite in suite_results.values())
        total_failed = sum(suite.failed for suite in suite_results.values())
        total_skipped = sum(suite.skipped for suite in suite_results.values())
        total_errors = sum(suite.errors for suite in suite_results.values())
        overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0.0
        
        # Create comprehensive report
        comprehensive_report = {
            'execution_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_duration': overall_duration,
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
                'errors': total_errors,
                'pass_rate': overall_pass_rate,
                'success': total_failed == 0 and total_errors == 0
            },
            'suite_results': {
                name: asdict(result) for name, result in suite_results.items()
            },
            'failed_tests': [],
            'error_tests': []
        }
        
        # Collect failed and error tests
        for suite_name, suite_result in suite_results.items():
            for test_result in suite_result.test_results:
                if test_result.status == 'failed':
                    comprehensive_report['failed_tests'].append({
                        'suite': suite_name,
                        'test': test_result.test_name,
                        'error_message': test_result.error_message,
                        'duration': test_result.duration
                    })
                elif test_result.status == 'error':
                    comprehensive_report['error_tests'].append({
                        'suite': suite_name,
                        'test': test_result.test_name,
                        'error_message': test_result.error_message,
                        'duration': test_result.duration
                    })
        
        # Save JSON report
        json_report_file = self.output_dir / 'comprehensive_report.json'
        with open(json_report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        # Generate HTML report
        self._generate_html_report(comprehensive_report)
        
        # Generate summary report
        self._generate_summary_report(comprehensive_report)
        
        self.logger.info(f"Comprehensive report saved: {json_report_file}")
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> None:
        """Generate HTML test report.
        
        Args:
            report_data: Comprehensive report data
        """
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>End-to-End Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .suite-header {{ background-color: #e9e9e9; padding: 10px; font-weight: bold; }}
        .test-list {{ padding: 10px; }}
        .test-item {{ margin: 5px 0; padding: 5px; border-radius: 3px; }}
        .passed {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        .error {{ background-color: #f8d7da; }}
        .skipped {{ background-color: #fff3cd; }}
        .stats {{ display: flex; gap: 20px; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        .stat-label {{ font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>End-to-End Integration Test Report</h1>
        <p>Generated: {report_data['execution_summary']['timestamp']}</p>
        <p>Duration: {report_data['execution_summary']['total_duration']:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Execution Summary</h2>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{report_data['execution_summary']['total_tests']}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: green;">{report_data['execution_summary']['passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: red;">{report_data['execution_summary']['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: orange;">{report_data['execution_summary']['errors']}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: blue;">{report_data['execution_summary']['skipped']}</div>
                <div class="stat-label">Skipped</div>
            </div>
            <div class="stat">
                <div class="stat-value">{report_data['execution_summary']['pass_rate']:.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
        </div>
    </div>
    
    <div class="suites">
        <h2>Test Suite Results</h2>
"""
        
        # Add suite details
        for suite_name, suite_data in report_data['suite_results'].items():
            html_content += f"""
        <div class="suite">
            <div class="suite-header">
                {suite_name} - {suite_data['passed']}/{suite_data['total_tests']} passed ({suite_data['pass_rate']:.1f}%)
            </div>
            <div class="test-list">
"""
            
            for test_result in suite_data['test_results']:
                status_class = test_result['status']
                html_content += f"""
                <div class="test-item {status_class}">
                    <strong>{test_result['test_name']}</strong> - {test_result['status']} ({test_result['duration']:.2f}s)
"""
                if test_result.get('error_message'):
                    html_content += f"""
                    <br><small>Error: {test_result['error_message'][:200]}...</small>
"""
                html_content += "</div>"
            
            html_content += """
            </div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        html_report_file = self.output_dir / 'test_report.html'
        with open(html_report_file, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report saved: {html_report_file}")
    
    def _generate_summary_report(self, report_data: Dict[str, Any]) -> None:
        """Generate summary text report.
        
        Args:
            report_data: Comprehensive report data
        """
        summary_content = f"""
End-to-End Integration Test Summary
==================================

Execution Time: {report_data['execution_summary']['timestamp']}
Total Duration: {report_data['execution_summary']['total_duration']:.2f} seconds

Overall Results:
- Total Tests: {report_data['execution_summary']['total_tests']}
- Passed: {report_data['execution_summary']['passed']}
- Failed: {report_data['execution_summary']['failed']}
- Errors: {report_data['execution_summary']['errors']}
- Skipped: {report_data['execution_summary']['skipped']}
- Pass Rate: {report_data['execution_summary']['pass_rate']:.1f}%
- Success: {'YES' if report_data['execution_summary']['success'] else 'NO'}

Suite Breakdown:
"""
        
        for suite_name, suite_data in report_data['suite_results'].items():
            summary_content += f"""
{suite_name}:
  Tests: {suite_data['total_tests']}
  Passed: {suite_data['passed']}
  Failed: {suite_data['failed']}
  Errors: {suite_data['errors']}
  Pass Rate: {suite_data['pass_rate']:.1f}%
  Duration: {suite_data['duration']:.2f}s
"""
        
        if report_data['failed_tests']:
            summary_content += "\nFailed Tests:\n"
            for failed_test in report_data['failed_tests']:
                summary_content += f"- {failed_test['suite']}::{failed_test['test']}\n"
                if failed_test['error_message']:
                    summary_content += f"  Error: {failed_test['error_message'][:100]}...\n"
        
        if report_data['error_tests']:
            summary_content += "\nError Tests:\n"
            for error_test in report_data['error_tests']:
                summary_content += f"- {error_test['suite']}::{error_test['test']}\n"
                if error_test['error_message']:
                    summary_content += f"  Error: {error_test['error_message'][:100]}...\n"
        
        summary_file = self.output_dir / 'test_summary.txt'
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        
        self.logger.info(f"Summary report saved: {summary_file}")
        
        # Also print summary to console
        print(summary_content)


def main():
    """Main entry point for end-to-end test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run end-to-end integration tests')
    parser.add_argument(
        '--output-dir', 
        type=Path, 
        default=Path('test_results'),
        help='Output directory for test results'
    )
    parser.add_argument(
        '--suite',
        choices=['end_to_end_workflows', 'system_integration', 'system_workflows'],
        help='Run specific test suite only'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup test runner
    runner = EndToEndTestRunner(output_dir=args.output_dir)
    
    if args.verbose:
        runner.logger.setLevel(logging.DEBUG)
    
    try:
        if args.suite:
            # Run specific suite
            suite_config = runner.test_suites[args.suite]
            result = runner.run_test_suite(args.suite, suite_config)
            runner._save_suite_report(result)
            
            print(f"\nSuite {args.suite} Results:")
            print(f"Tests: {result.total_tests}")
            print(f"Passed: {result.passed}")
            print(f"Failed: {result.failed}")
            print(f"Errors: {result.errors}")
            print(f"Pass Rate: {result.pass_rate:.1f}%")
            
            return 0 if result.failed == 0 and result.errors == 0 else 1
        else:
            # Run all suites
            results = runner.run_all_suites()
            
            # Determine exit code
            total_failed = sum(suite.failed for suite in results.values())
            total_errors = sum(suite.errors for suite in results.values())
            
            return 0 if total_failed == 0 and total_errors == 0 else 1
    
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())