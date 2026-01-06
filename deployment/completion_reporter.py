"""
Deployment Completion Reporter

Generates comprehensive deployment completion reports with performance metrics,
resource usage analysis, and detailed summaries for successful and failed deployments.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from .models import DeploymentResult, DeploymentStatus, DeploymentStep


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for deployment analysis"""
    artifact_transfer_time_seconds: float = 0.0
    dependency_installation_time_seconds: float = 0.0
    validation_time_seconds: float = 0.0
    average_step_duration_seconds: float = 0.0
    throughput_artifacts_per_minute: float = 0.0
    network_latency_ms: float = 0.0
    disk_io_operations: int = 0
    memory_peak_usage_mb: float = 0.0


@dataclass
class ResourceUsage:
    """Resource usage statistics during deployment"""
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_usage_mb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_received: int = 0
    temporary_files_created: int = 0
    temporary_files_cleaned: int = 0


@dataclass
class ValidationResults:
    """Validation results summary"""
    checks_passed: int = 0
    checks_failed: int = 0
    checks_total: int = 0
    success_rate_percent: float = 0.0
    critical_issues: int = 0
    warnings: int = 0


@dataclass
class StepDetail:
    """Detailed information about a deployment step"""
    step_name: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    artifacts_processed: Optional[int] = None
    bytes_transferred: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class DeploymentSummary:
    """Comprehensive deployment completion summary"""
    deployment_id: str
    plan_id: str
    environment_id: str
    status: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    artifacts_deployed: int
    dependencies_installed: int
    steps_completed: int
    steps_total: int
    retry_count: int
    error_message: Optional[str] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    step_details: Optional[List[StepDetail]] = None
    resource_usage: Optional[ResourceUsage] = None
    validation_results: Optional[ValidationResults] = None


class DeploymentCompletionReporter:
    """
    Generates comprehensive deployment completion reports with performance analysis,
    resource usage statistics, and detailed summaries.
    """
    
    def __init__(self, reports_dir: str = "./deployment_reports"):
        """
        Initialize the completion reporter.
        
        Args:
            reports_dir: Directory to store generated reports
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DeploymentCompletionReporter initialized with reports_dir={reports_dir}")
    
    def generate_completion_report(self, 
                                 deployment_result: DeploymentResult,
                                 deployment_steps: List[DeploymentStep],
                                 performance_data: Optional[Dict[str, Any]] = None,
                                 resource_data: Optional[Dict[str, Any]] = None) -> DeploymentSummary:
        """
        Generate a comprehensive deployment completion report.
        
        Args:
            deployment_result: The completed deployment result
            deployment_steps: List of deployment steps with details
            performance_data: Optional performance metrics data
            resource_data: Optional resource usage data
            
        Returns:
            DeploymentSummary with comprehensive completion information
        """
        logger.info(f"Generating completion report for deployment {deployment_result.deployment_id}")
        
        # Calculate basic metrics
        total_duration = self._calculate_total_duration(deployment_result)
        steps_completed = len([step for step in deployment_steps if step.status == DeploymentStatus.COMPLETED])
        
        # Generate performance metrics
        performance_metrics = self._analyze_performance_metrics(
            deployment_steps, total_duration, deployment_result.artifacts_deployed, performance_data
        )
        
        # Generate step details
        step_details = self._extract_step_details(deployment_steps)
        
        # Generate resource usage analysis
        resource_usage = self._analyze_resource_usage(deployment_steps, resource_data)
        
        # Generate validation results if available
        validation_results = self._extract_validation_results(deployment_steps)
        
        # Create comprehensive summary
        summary = DeploymentSummary(
            deployment_id=deployment_result.deployment_id,
            plan_id=deployment_result.plan_id,
            environment_id=deployment_result.environment_id,
            status=deployment_result.status.value,
            start_time=deployment_result.start_time.isoformat(),
            end_time=deployment_result.end_time.isoformat() if deployment_result.end_time else datetime.now().isoformat(),
            total_duration_seconds=total_duration,
            artifacts_deployed=deployment_result.artifacts_deployed,
            dependencies_installed=deployment_result.dependencies_installed,
            steps_completed=steps_completed,
            steps_total=len(deployment_steps),
            retry_count=deployment_result.retry_count,
            error_message=deployment_result.error_message,
            performance_metrics=performance_metrics,
            step_details=step_details,
            resource_usage=resource_usage,
            validation_results=validation_results
        )
        
        # Save report to file
        self._save_report_to_file(summary)
        
        logger.info(f"Completion report generated for deployment {deployment_result.deployment_id}")
        return summary
    
    def _calculate_total_duration(self, deployment_result: DeploymentResult) -> float:
        """Calculate total deployment duration in seconds"""
        if deployment_result.end_time and deployment_result.start_time:
            return (deployment_result.end_time - deployment_result.start_time).total_seconds()
        return 0.0
    
    def _analyze_performance_metrics(self, 
                                   deployment_steps: List[DeploymentStep],
                                   total_duration: float,
                                   artifacts_deployed: int,
                                   performance_data: Optional[Dict[str, Any]]) -> PerformanceMetrics:
        """Analyze performance metrics from deployment steps and additional data"""
        
        # Extract timing from steps
        artifact_transfer_time = 0.0
        dependency_installation_time = 0.0
        validation_time = 0.0
        
        step_durations = []
        
        for step in deployment_steps:
            if step.duration_seconds:
                step_durations.append(step.duration_seconds)
                
                # Categorize step timing
                step_name_lower = step.name.lower()
                if 'artifact' in step_name_lower or 'deploy' in step_name_lower:
                    artifact_transfer_time += step.duration_seconds
                elif 'dependency' in step_name_lower or 'install' in step_name_lower:
                    dependency_installation_time += step.duration_seconds
                elif 'validation' in step_name_lower or 'readiness' in step_name_lower:
                    validation_time += step.duration_seconds
        
        # Calculate averages
        average_step_duration = sum(step_durations) / len(step_durations) if step_durations else 0.0
        
        # Calculate throughput
        throughput_artifacts_per_minute = 0.0
        if total_duration > 0 and artifacts_deployed > 0:
            throughput_artifacts_per_minute = (artifacts_deployed / total_duration) * 60
        
        # Extract additional metrics from performance data
        network_latency_ms = 0.0
        disk_io_operations = 0
        memory_peak_usage_mb = 0.0
        
        if performance_data:
            network_latency_ms = performance_data.get('network_latency_ms', 0.0)
            disk_io_operations = performance_data.get('disk_io_operations', 0)
            memory_peak_usage_mb = performance_data.get('memory_peak_usage_mb', 0.0)
        
        return PerformanceMetrics(
            artifact_transfer_time_seconds=artifact_transfer_time,
            dependency_installation_time_seconds=dependency_installation_time,
            validation_time_seconds=validation_time,
            average_step_duration_seconds=average_step_duration,
            throughput_artifacts_per_minute=throughput_artifacts_per_minute,
            network_latency_ms=network_latency_ms,
            disk_io_operations=disk_io_operations,
            memory_peak_usage_mb=memory_peak_usage_mb
        )
    
    def _extract_step_details(self, deployment_steps: List[DeploymentStep]) -> List[StepDetail]:
        """Extract detailed information from deployment steps"""
        step_details = []
        
        for step in deployment_steps:
            detail = StepDetail(
                step_name=step.name,
                status=step.status.value,
                start_time=step.start_time.isoformat(),
                end_time=step.end_time.isoformat() if step.end_time else None,
                duration_seconds=step.duration_seconds or 0.0,
                error_message=step.error_message
            )
            
            # Extract additional details from step details
            if hasattr(step, 'details') and step.details:
                detail.artifacts_processed = step.details.get('artifacts_processed')
                detail.bytes_transferred = step.details.get('bytes_transferred')
            
            step_details.append(detail)
        
        return step_details
    
    def _analyze_resource_usage(self, 
                              deployment_steps: List[DeploymentStep],
                              resource_data: Optional[Dict[str, Any]]) -> ResourceUsage:
        """Analyze resource usage during deployment"""
        
        # Initialize with defaults
        resource_usage = ResourceUsage()
        
        # Extract from resource data if available
        if resource_data:
            resource_usage.cpu_usage_percent = resource_data.get('cpu_usage_percent', 0.0)
            resource_usage.memory_usage_mb = resource_data.get('memory_usage_mb', 0.0)
            resource_usage.disk_usage_mb = resource_data.get('disk_usage_mb', 0.0)
            resource_usage.network_bytes_sent = resource_data.get('network_bytes_sent', 0)
            resource_usage.network_bytes_received = resource_data.get('network_bytes_received', 0)
            resource_usage.temporary_files_created = resource_data.get('temporary_files_created', 0)
            resource_usage.temporary_files_cleaned = resource_data.get('temporary_files_cleaned', 0)
        
        # Aggregate from step details if available
        for step in deployment_steps:
            if hasattr(step, 'details') and step.details:
                step_details = step.details
                
                # Accumulate network usage
                if 'bytes_transferred' in step_details:
                    resource_usage.network_bytes_sent += step_details['bytes_transferred']
                
                # Count temporary files
                if 'temp_files_created' in step_details:
                    resource_usage.temporary_files_created += step_details['temp_files_created']
                
                if 'temp_files_cleaned' in step_details:
                    resource_usage.temporary_files_cleaned += step_details['temp_files_cleaned']
        
        return resource_usage
    
    def _extract_validation_results(self, deployment_steps: List[DeploymentStep]) -> Optional[ValidationResults]:
        """Extract validation results from deployment steps"""
        
        # Find validation step
        validation_step = None
        for step in deployment_steps:
            if 'validation' in step.name.lower() or 'readiness' in step.name.lower():
                validation_step = step
                break
        
        if not validation_step or not hasattr(validation_step, 'details') or not validation_step.details:
            return None
        
        details = validation_step.details
        
        # Extract validation metrics
        checks_passed = details.get('checks_passed', 0)
        checks_failed = details.get('checks_failed', 0)
        checks_total = checks_passed + checks_failed
        
        success_rate_percent = 0.0
        if checks_total > 0:
            success_rate_percent = (checks_passed / checks_total) * 100
        
        critical_issues = details.get('critical_issues', 0)
        warnings = details.get('warnings', 0)
        
        return ValidationResults(
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            checks_total=checks_total,
            success_rate_percent=success_rate_percent,
            critical_issues=critical_issues,
            warnings=warnings
        )
    
    def _save_report_to_file(self, summary: DeploymentSummary):
        """Save deployment report to JSON file"""
        try:
            report_file = self.reports_dir / f"deployment_report_{summary.deployment_id}.json"
            
            # Convert to dictionary for JSON serialization
            report_data = asdict(summary)
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Deployment report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save deployment report: {e}")
    
    def get_deployment_report(self, deployment_id: str) -> Optional[DeploymentSummary]:
        """Retrieve a previously generated deployment report"""
        try:
            report_file = self.reports_dir / f"deployment_report_{deployment_id}.json"
            
            if not report_file.exists():
                logger.warning(f"Report file not found for deployment {deployment_id}")
                return None
            
            with open(report_file, 'r') as f:
                report_data = json.load(f)
            
            # Convert back to DeploymentSummary
            # Handle nested objects
            if report_data.get('performance_metrics'):
                report_data['performance_metrics'] = PerformanceMetrics(**report_data['performance_metrics'])
            
            if report_data.get('resource_usage'):
                report_data['resource_usage'] = ResourceUsage(**report_data['resource_usage'])
            
            if report_data.get('validation_results'):
                report_data['validation_results'] = ValidationResults(**report_data['validation_results'])
            
            if report_data.get('step_details'):
                report_data['step_details'] = [StepDetail(**step) for step in report_data['step_details']]
            
            return DeploymentSummary(**report_data)
            
        except Exception as e:
            logger.error(f"Failed to load deployment report for {deployment_id}: {e}")
            return None
    
    def list_deployment_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List available deployment reports with basic information"""
        reports = []
        
        try:
            report_files = list(self.reports_dir.glob("deployment_report_*.json"))
            report_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            for report_file in report_files[:limit]:
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    
                    reports.append({
                        'deployment_id': report_data['deployment_id'],
                        'status': report_data['status'],
                        'environment_id': report_data['environment_id'],
                        'start_time': report_data['start_time'],
                        'end_time': report_data['end_time'],
                        'total_duration_seconds': report_data['total_duration_seconds'],
                        'artifacts_deployed': report_data['artifacts_deployed'],
                        'file_path': str(report_file)
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to read report file {report_file}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to list deployment reports: {e}")
        
        return reports
    
    def generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics across all deployment reports"""
        reports = self.list_deployment_reports(limit=1000)  # Get more for statistics
        
        if not reports:
            return {}
        
        total_deployments = len(reports)
        successful_deployments = len([r for r in reports if r['status'] == 'completed'])
        failed_deployments = len([r for r in reports if r['status'] == 'failed'])
        cancelled_deployments = len([r for r in reports if r['status'] == 'cancelled'])
        
        # Calculate averages
        durations = [r['total_duration_seconds'] for r in reports if r['total_duration_seconds'] > 0]
        average_duration = sum(durations) / len(durations) if durations else 0.0
        
        artifacts = [r['artifacts_deployed'] for r in reports]
        average_artifacts = sum(artifacts) / len(artifacts) if artifacts else 0.0
        
        return {
            'total_deployments': total_deployments,
            'successful_deployments': successful_deployments,
            'failed_deployments': failed_deployments,
            'cancelled_deployments': cancelled_deployments,
            'success_rate_percent': (successful_deployments / total_deployments) * 100 if total_deployments > 0 else 0.0,
            'average_duration_seconds': average_duration,
            'average_artifacts_deployed': average_artifacts,
            'generated_at': datetime.now().isoformat()
        }