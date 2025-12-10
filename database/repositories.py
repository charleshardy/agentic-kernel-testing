"""Data access layer with repository pattern."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from ai_generator.models import (
    TestCase, TestResult, Environment, CoverageData, 
    FailureAnalysis, CodeAnalysis, TestType, TestStatus,
    RiskLevel, EnvironmentStatus
)
from .models import (
    TestCaseModel, TestResultModel, EnvironmentModel, 
    CoverageDataModel, FailureAnalysisModel, CodeAnalysisModel,
    HardwareConfigModel, PerformanceBaselineModel, SecurityIssueModel
)


class BaseRepository(ABC):
    """Base repository with common operations."""
    
    def __init__(self, session: Session):
        self.session = session


class HardwareConfigRepository(BaseRepository):
    """Repository for hardware configurations."""
    
    def create(self, config: HardwareConfigModel) -> HardwareConfigModel:
        """Create a new hardware configuration."""
        self.session.add(config)
        self.session.flush()
        return config
    
    def get_by_id(self, config_id: int) -> Optional[HardwareConfigModel]:
        """Get hardware configuration by ID."""
        return self.session.query(HardwareConfigModel).filter(
            HardwareConfigModel.id == config_id
        ).first()
    
    def get_by_specs(self, architecture: str, cpu_model: str, memory_mb: int) -> Optional[HardwareConfigModel]:
        """Get hardware configuration by specifications."""
        return self.session.query(HardwareConfigModel).filter(
            and_(
                HardwareConfigModel.architecture == architecture,
                HardwareConfigModel.cpu_model == cpu_model,
                HardwareConfigModel.memory_mb == memory_mb
            )
        ).first()
    
    def list_all(self) -> List[HardwareConfigModel]:
        """List all hardware configurations."""
        return self.session.query(HardwareConfigModel).all()
    
    def list_virtual(self) -> List[HardwareConfigModel]:
        """List virtual hardware configurations."""
        return self.session.query(HardwareConfigModel).filter(
            HardwareConfigModel.is_virtual == True
        ).all()
    
    def list_physical(self) -> List[HardwareConfigModel]:
        """List physical hardware configurations."""
        return self.session.query(HardwareConfigModel).filter(
            HardwareConfigModel.is_virtual == False
        ).all()


class TestCaseRepository(BaseRepository):
    """Repository for test cases."""
    
    def create(self, test_case: TestCase) -> TestCaseModel:
        """Create a new test case."""
        # Find or create hardware config if needed
        hardware_config_id = None
        if test_case.required_hardware:
            hw_repo = HardwareConfigRepository(self.session)
            hw_config = hw_repo.get_by_specs(
                test_case.required_hardware.architecture,
                test_case.required_hardware.cpu_model,
                test_case.required_hardware.memory_mb
            )
            if not hw_config:
                hw_config = hw_repo.create(
                    HardwareConfigModel.from_domain_model(test_case.required_hardware)
                )
            hardware_config_id = hw_config.id
        
        test_case_model = TestCaseModel.from_domain_model(test_case, hardware_config_id)
        self.session.add(test_case_model)
        self.session.flush()
        return test_case_model
    
    def get_by_id(self, test_id: str) -> Optional[TestCaseModel]:
        """Get test case by ID."""
        return self.session.query(TestCaseModel).filter(
            TestCaseModel.id == test_id
        ).first()
    
    def list_by_subsystem(self, subsystem: str) -> List[TestCaseModel]:
        """List test cases by target subsystem."""
        return self.session.query(TestCaseModel).filter(
            TestCaseModel.target_subsystem == subsystem
        ).all()
    
    def list_by_type(self, test_type: TestType) -> List[TestCaseModel]:
        """List test cases by type."""
        return self.session.query(TestCaseModel).filter(
            TestCaseModel.test_type == test_type
        ).all()
    
    def list_recent(self, days: int = 7) -> List[TestCaseModel]:
        """List recently created test cases."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.session.query(TestCaseModel).filter(
            TestCaseModel.created_at >= cutoff
        ).order_by(desc(TestCaseModel.created_at)).all()
    
    def search(self, query: str) -> List[TestCaseModel]:
        """Search test cases by name or description."""
        search_pattern = f"%{query}%"
        return self.session.query(TestCaseModel).filter(
            or_(
                TestCaseModel.name.ilike(search_pattern),
                TestCaseModel.description.ilike(search_pattern)
            )
        ).all()
    
    def update(self, test_case: TestCase) -> Optional[TestCaseModel]:
        """Update an existing test case."""
        test_case_model = self.get_by_id(test_case.id)
        if not test_case_model:
            return None
        
        # Update fields
        test_case_model.name = test_case.name
        test_case_model.description = test_case.description
        test_case_model.test_type = test_case.test_type
        test_case_model.target_subsystem = test_case.target_subsystem
        test_case_model.code_paths = test_case.code_paths
        test_case_model.execution_time_estimate = test_case.execution_time_estimate
        test_case_model.test_script = test_case.test_script
        test_case_model.expected_outcome = test_case.expected_outcome.to_dict() if test_case.expected_outcome else None
        test_case_model.metadata = test_case.metadata
        test_case_model.updated_at = datetime.utcnow()
        
        return test_case_model
    
    def delete(self, test_id: str) -> bool:
        """Delete a test case."""
        test_case = self.get_by_id(test_id)
        if test_case:
            self.session.delete(test_case)
            return True
        return False


class EnvironmentRepository(BaseRepository):
    """Repository for test environments."""
    
    def create(self, environment: Environment) -> EnvironmentModel:
        """Create a new environment."""
        # Find or create hardware config
        hw_repo = HardwareConfigRepository(self.session)
        hw_config = hw_repo.get_by_specs(
            environment.config.architecture,
            environment.config.cpu_model,
            environment.config.memory_mb
        )
        if not hw_config:
            hw_config = hw_repo.create(
                HardwareConfigModel.from_domain_model(environment.config)
            )
        
        env_model = EnvironmentModel.from_domain_model(environment, hw_config.id)
        self.session.add(env_model)
        self.session.flush()
        return env_model
    
    def get_by_id(self, env_id: str) -> Optional[EnvironmentModel]:
        """Get environment by ID."""
        return self.session.query(EnvironmentModel).filter(
            EnvironmentModel.id == env_id
        ).first()
    
    def list_by_status(self, status: EnvironmentStatus) -> List[EnvironmentModel]:
        """List environments by status."""
        return self.session.query(EnvironmentModel).filter(
            EnvironmentModel.status == status
        ).all()
    
    def list_idle(self) -> List[EnvironmentModel]:
        """List idle environments."""
        return self.list_by_status(EnvironmentStatus.IDLE)
    
    def list_busy(self) -> List[EnvironmentModel]:
        """List busy environments."""
        return self.list_by_status(EnvironmentStatus.BUSY)
    
    def list_stale(self, hours: int = 24) -> List[EnvironmentModel]:
        """List environments not used recently."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(EnvironmentModel).filter(
            EnvironmentModel.last_used < cutoff
        ).all()
    
    def update_status(self, env_id: str, status: EnvironmentStatus) -> bool:
        """Update environment status."""
        env = self.get_by_id(env_id)
        if env:
            env.status = status
            env.last_used = datetime.utcnow()
            return True
        return False
    
    def update_last_used(self, env_id: str) -> bool:
        """Update last used timestamp."""
        env = self.get_by_id(env_id)
        if env:
            env.last_used = datetime.utcnow()
            return True
        return False


class TestResultRepository(BaseRepository):
    """Repository for test results."""
    
    def create(self, test_result: TestResult) -> TestResultModel:
        """Create a new test result."""
        result_model = TestResultModel.from_domain_model(test_result)
        self.session.add(result_model)
        self.session.flush()
        
        # Add coverage data if present
        if test_result.coverage_data:
            coverage_model = CoverageDataModel.from_domain_model(
                test_result.coverage_data, result_model.id
            )
            self.session.add(coverage_model)
        
        return result_model
    
    def get_by_id(self, result_id: int) -> Optional[TestResultModel]:
        """Get test result by ID."""
        return self.session.query(TestResultModel).filter(
            TestResultModel.id == result_id
        ).first()
    
    def list_by_test_case(self, test_case_id: str) -> List[TestResultModel]:
        """List results for a specific test case."""
        return self.session.query(TestResultModel).filter(
            TestResultModel.test_case_id == test_case_id
        ).order_by(desc(TestResultModel.timestamp)).all()
    
    def list_by_status(self, status: TestStatus) -> List[TestResultModel]:
        """List results by status."""
        return self.session.query(TestResultModel).filter(
            TestResultModel.status == status
        ).all()
    
    def list_failures(self) -> List[TestResultModel]:
        """List failed test results."""
        return self.list_by_status(TestStatus.FAILED)
    
    def list_recent(self, hours: int = 24) -> List[TestResultModel]:
        """List recent test results."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(TestResultModel).filter(
            TestResultModel.timestamp >= cutoff
        ).order_by(desc(TestResultModel.timestamp)).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get test result statistics."""
        total = self.session.query(TestResultModel).count()
        passed = self.session.query(TestResultModel).filter(
            TestResultModel.status == TestStatus.PASSED
        ).count()
        failed = self.session.query(TestResultModel).filter(
            TestResultModel.status == TestStatus.FAILED
        ).count()
        
        avg_execution_time = self.session.query(
            func.avg(TestResultModel.execution_time)
        ).scalar() or 0.0
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0.0,
            'avg_execution_time': float(avg_execution_time)
        }


class CoverageRepository(BaseRepository):
    """Repository for coverage data."""
    
    def get_by_test_result(self, test_result_id: int) -> Optional[CoverageDataModel]:
        """Get coverage data for a test result."""
        return self.session.query(CoverageDataModel).filter(
            CoverageDataModel.test_result_id == test_result_id
        ).first()
    
    def get_aggregate_coverage(self, test_case_ids: List[str] = None) -> Dict[str, float]:
        """Get aggregate coverage metrics."""
        query = self.session.query(
            func.avg(CoverageDataModel.line_coverage).label('avg_line'),
            func.avg(CoverageDataModel.branch_coverage).label('avg_branch'),
            func.avg(CoverageDataModel.function_coverage).label('avg_function')
        )
        
        if test_case_ids:
            query = query.join(TestResultModel).filter(
                TestResultModel.test_case_id.in_(test_case_ids)
            )
        
        result = query.first()
        return {
            'line_coverage': float(result.avg_line or 0.0),
            'branch_coverage': float(result.avg_branch or 0.0),
            'function_coverage': float(result.avg_function or 0.0)
        }
    
    def get_coverage_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get coverage trend over time."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = self.session.query(
            func.date(TestResultModel.timestamp).label('date'),
            func.avg(CoverageDataModel.line_coverage).label('avg_line'),
            func.avg(CoverageDataModel.branch_coverage).label('avg_branch'),
            func.avg(CoverageDataModel.function_coverage).label('avg_function')
        ).join(TestResultModel).filter(
            TestResultModel.timestamp >= cutoff
        ).group_by(
            func.date(TestResultModel.timestamp)
        ).order_by(asc('date')).all()
        
        return [
            {
                'date': result.date.isoformat(),
                'line_coverage': float(result.avg_line or 0.0),
                'branch_coverage': float(result.avg_branch or 0.0),
                'function_coverage': float(result.avg_function or 0.0)
            }
            for result in results
        ]


class CodeAnalysisRepository(BaseRepository):
    """Repository for code analysis results."""
    
    def create(self, analysis: CodeAnalysis, commit_sha: str) -> CodeAnalysisModel:
        """Create a new code analysis."""
        analysis_model = CodeAnalysisModel.from_domain_model(analysis, commit_sha)
        self.session.add(analysis_model)
        self.session.flush()
        return analysis_model
    
    def get_by_commit(self, commit_sha: str) -> Optional[CodeAnalysisModel]:
        """Get analysis by commit SHA."""
        return self.session.query(CodeAnalysisModel).filter(
            CodeAnalysisModel.commit_sha == commit_sha
        ).first()
    
    def list_by_risk_level(self, risk_level: RiskLevel) -> List[CodeAnalysisModel]:
        """List analyses by risk level."""
        return self.session.query(CodeAnalysisModel).filter(
            CodeAnalysisModel.risk_level == risk_level
        ).order_by(desc(CodeAnalysisModel.created_at)).all()
    
    def list_high_impact(self, threshold: float = 0.7) -> List[CodeAnalysisModel]:
        """List high-impact analyses."""
        return self.session.query(CodeAnalysisModel).filter(
            CodeAnalysisModel.impact_score >= threshold
        ).order_by(desc(CodeAnalysisModel.impact_score)).all()


class FailureRepository(BaseRepository):
    """Repository for failure analyses."""
    
    def create(self, analysis: FailureAnalysis, test_result_id: int) -> FailureAnalysisModel:
        """Create a new failure analysis."""
        analysis_model = FailureAnalysisModel.from_domain_model(analysis, test_result_id)
        self.session.add(analysis_model)
        self.session.flush()
        return analysis_model
    
    def get_by_failure_id(self, failure_id: str) -> Optional[FailureAnalysisModel]:
        """Get analysis by failure ID."""
        return self.session.query(FailureAnalysisModel).filter(
            FailureAnalysisModel.failure_id == failure_id
        ).first()
    
    def list_by_pattern(self, error_pattern: str) -> List[FailureAnalysisModel]:
        """List failures with similar error patterns."""
        search_pattern = f"%{error_pattern}%"
        return self.session.query(FailureAnalysisModel).filter(
            FailureAnalysisModel.error_pattern.ilike(search_pattern)
        ).all()
    
    def list_high_confidence(self, threshold: float = 0.8) -> List[FailureAnalysisModel]:
        """List high-confidence failure analyses."""
        return self.session.query(FailureAnalysisModel).filter(
            FailureAnalysisModel.confidence >= threshold
        ).order_by(desc(FailureAnalysisModel.confidence)).all()
    
    def get_related_failures(self, failure_id: str) -> List[FailureAnalysisModel]:
        """Get failures related to a specific failure."""
        failure = self.get_by_failure_id(failure_id)
        if not failure or not failure.related_failures:
            return []
        
        return self.session.query(FailureAnalysisModel).filter(
            FailureAnalysisModel.failure_id.in_(failure.related_failures)
        ).all()


class PerformanceRepository(BaseRepository):
    """Repository for performance data."""
    
    def create_baseline(self, kernel_version: str, hardware_config_id: int,
                       benchmark_name: str, metric_name: str, value: float, unit: str,
                       metadata: Dict[str, Any] = None) -> PerformanceBaselineModel:
        """Create a performance baseline."""
        baseline = PerformanceBaselineModel(
            kernel_version=kernel_version,
            hardware_config_id=hardware_config_id,
            benchmark_name=benchmark_name,
            metric_name=metric_name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        self.session.add(baseline)
        self.session.flush()
        return baseline
    
    def get_baseline(self, kernel_version: str, hardware_config_id: int,
                    benchmark_name: str, metric_name: str) -> Optional[PerformanceBaselineModel]:
        """Get performance baseline."""
        return self.session.query(PerformanceBaselineModel).filter(
            and_(
                PerformanceBaselineModel.kernel_version == kernel_version,
                PerformanceBaselineModel.hardware_config_id == hardware_config_id,
                PerformanceBaselineModel.benchmark_name == benchmark_name,
                PerformanceBaselineModel.metric_name == metric_name
            )
        ).first()
    
    def list_baselines_for_kernel(self, kernel_version: str) -> List[PerformanceBaselineModel]:
        """List all baselines for a kernel version."""
        return self.session.query(PerformanceBaselineModel).filter(
            PerformanceBaselineModel.kernel_version == kernel_version
        ).all()


class SecurityRepository(BaseRepository):
    """Repository for security issues."""
    
    def create_issue(self, issue_id: str, issue_type: str, severity: str,
                    exploitability: str, description: str, location: Dict[str, Any],
                    test_result_id: int = None, cvss_score: float = None,
                    proof_of_concept: str = None, remediation: str = None,
                    metadata: Dict[str, Any] = None) -> SecurityIssueModel:
        """Create a security issue."""
        issue = SecurityIssueModel(
            issue_id=issue_id,
            test_result_id=test_result_id,
            issue_type=issue_type,
            severity=severity,
            exploitability=exploitability,
            cvss_score=cvss_score,
            description=description,
            location=location,
            proof_of_concept=proof_of_concept,
            remediation=remediation,
            metadata=metadata or {}
        )
        self.session.add(issue)
        self.session.flush()
        return issue
    
    def get_by_issue_id(self, issue_id: str) -> Optional[SecurityIssueModel]:
        """Get security issue by ID."""
        return self.session.query(SecurityIssueModel).filter(
            SecurityIssueModel.issue_id == issue_id
        ).first()
    
    def list_by_severity(self, severity: str) -> List[SecurityIssueModel]:
        """List issues by severity."""
        return self.session.query(SecurityIssueModel).filter(
            SecurityIssueModel.severity == severity
        ).order_by(desc(SecurityIssueModel.created_at)).all()
    
    def list_critical_issues(self) -> List[SecurityIssueModel]:
        """List critical security issues."""
        return self.list_by_severity("critical")
    
    def get_security_summary(self) -> Dict[str, int]:
        """Get security issue summary by severity."""
        results = self.session.query(
            SecurityIssueModel.severity,
            func.count(SecurityIssueModel.id).label('count')
        ).group_by(SecurityIssueModel.severity).all()
        
        return {result.severity: result.count for result in results}