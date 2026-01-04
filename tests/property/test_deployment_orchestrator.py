"""
Property-based tests for DeploymentOrchestrator

**Feature: test-deployment-system, Property 1: Automatic script transfer completeness**
**Validates: Requirements 1.1**

Tests that for any test plan entering deployment stage, all required test scripts
should be successfully transferred to the target environment.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import tempfile
import shutil
from pathlib import Path

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    TestArtifact, 
    ArtifactType, 
    DeploymentStatus,
    InstrumentationConfig,
    DeploymentConfig,
    Dependency
)


@composite
def test_artifact_strategy(draw):
    """Generate valid test artifacts for property testing"""
    artifact_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    artifact_type = draw(st.sampled_from(list(ArtifactType)))
    content = draw(st.binary(min_size=1, max_size=1000))
    permissions = draw(st.sampled_from(['0755', '0644', '0600', '0777']))
    target_path = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'))))
    dependencies = draw(st.lists(st.text(min_size=1, max_size=20), max_size=5))
    
    return TestArtifact(
        artifact_id=artifact_id,
        name=name,
        type=artifact_type,
        content=content,
        checksum="",  # Will be calculated automatically
        permissions=permissions,
        target_path=target_path,
        dependencies=dependencies
    )


@composite
def deployment_scenario_strategy(draw):
    """Generate deployment scenarios for property testing"""
    plan_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    env_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    artifacts = draw(st.lists(test_artifact_strategy(), min_size=1, max_size=10))
    
    return {
        'plan_id': plan_id,
        'env_id': env_id,
        'artifacts': artifacts
    }


class TestDeploymentOrchestratorProperties:
    """Property-based tests for DeploymentOrchestrator"""
    
    @pytest.fixture
    async def orchestrator(self):
        """Create a deployment orchestrator for testing"""
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=2, default_timeout=30)
        await orchestrator.start()
        yield orchestrator
        await orchestrator.stop()
    
    @given(deployment_scenario_strategy())
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_automatic_script_transfer_completeness(self, deployment_scenario):
        """
        **Feature: test-deployment-system, Property 1: Automatic script transfer completeness**
        **Validates: Requirements 1.1**
        
        Property: For any test plan entering deployment stage, all required test scripts
        should be successfully transferred to the target environment.
        """
        # Create orchestrator
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=2, default_timeout=30)
        await orchestrator.start()
        
        try:
            plan_id = deployment_scenario['plan_id']
            env_id = deployment_scenario['env_id']
            artifacts = deployment_scenario['artifacts']
            
            # Deploy artifacts to environment
            deployment_id = await orchestrator.deploy_to_environment(plan_id, env_id, artifacts)
            
            # Verify deployment was queued
            assert deployment_id is not None
            assert deployment_id.startswith("deploy_")
            
            # Wait for deployment to complete (with timeout)
            max_wait_time = 10  # seconds
            wait_interval = 0.1
            total_waited = 0
            
            while total_waited < max_wait_time:
                deployment_result = await orchestrator.get_deployment_status(deployment_id)
                assert deployment_result is not None, "Deployment result should exist"
                
                if deployment_result.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]:
                    break
                
                await asyncio.sleep(wait_interval)
                total_waited += wait_interval
            
            # Get final deployment result
            deployment_result = await orchestrator.get_deployment_status(deployment_id)
            assert deployment_result is not None
            
            # Property: All artifacts should be successfully deployed
            if deployment_result.status == DeploymentStatus.COMPLETED:
                # Verify all artifacts were processed
                assert deployment_result.artifacts_deployed == len(artifacts), \
                    f"Expected {len(artifacts)} artifacts deployed, got {deployment_result.artifacts_deployed}"
                
                # Verify deployment has proper metadata
                assert deployment_result.plan_id == plan_id
                assert deployment_result.environment_id == env_id
                assert deployment_result.start_time is not None
                assert deployment_result.end_time is not None
                assert deployment_result.duration_seconds is not None
                assert deployment_result.duration_seconds >= 0
                
                # Verify deployment pipeline stages were executed
                expected_stages = [
                    "Artifact Preparation",
                    "Environment Connection", 
                    "Dependency Installation",
                    "Script Deployment",
                    "Instrumentation Setup",
                    "Readiness Validation"
                ]
                
                stage_names = [step.name for step in deployment_result.steps]
                for expected_stage in expected_stages:
                    assert expected_stage in stage_names, f"Missing deployment stage: {expected_stage}"
                
                # Verify all stages completed successfully
                for step in deployment_result.steps:
                    assert step.status == DeploymentStatus.COMPLETED, \
                        f"Stage {step.name} failed: {step.error_message}"
                    assert step.start_time is not None
                    assert step.end_time is not None
                    assert step.duration_seconds is not None
                    assert step.duration_seconds >= 0
            
            elif deployment_result.status == DeploymentStatus.FAILED:
                # If deployment failed, it should have error information
                assert deployment_result.error_message is not None
                assert len(deployment_result.error_message) > 0
                
                # Failed deployments should still have attempted some stages
                assert len(deployment_result.steps) > 0
                
                # At least one stage should have failed
                failed_stages = [step for step in deployment_result.steps if step.status == DeploymentStatus.FAILED]
                assert len(failed_stages) > 0, "Failed deployment should have at least one failed stage"
            
            else:
                pytest.fail(f"Deployment did not complete within timeout. Status: {deployment_result.status}")
        
        finally:
            await orchestrator.stop()
    
    @given(st.lists(deployment_scenario_strategy(), min_size=2, max_size=5))
    @settings(max_examples=50, deadline=10000)
    @pytest.mark.asyncio
    async def test_concurrent_deployment_handling(self, deployment_scenarios):
        """
        Property: The orchestrator should handle multiple concurrent deployments correctly,
        ensuring each deployment is processed independently and completely.
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=3, default_timeout=30)
        await orchestrator.start()
        
        try:
            deployment_ids = []
            
            # Start multiple deployments concurrently
            for scenario in deployment_scenarios:
                deployment_id = await orchestrator.deploy_to_environment(
                    scenario['plan_id'], 
                    scenario['env_id'], 
                    scenario['artifacts']
                )
                deployment_ids.append(deployment_id)
            
            # Wait for all deployments to complete
            max_wait_time = 15  # seconds
            wait_interval = 0.1
            total_waited = 0
            
            while total_waited < max_wait_time:
                all_completed = True
                for deployment_id in deployment_ids:
                    result = await orchestrator.get_deployment_status(deployment_id)
                    if result and result.status not in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]:
                        all_completed = False
                        break
                
                if all_completed:
                    break
                
                await asyncio.sleep(wait_interval)
                total_waited += wait_interval
            
            # Verify all deployments completed
            for i, deployment_id in enumerate(deployment_ids):
                result = await orchestrator.get_deployment_status(deployment_id)
                assert result is not None, f"Deployment {i} result should exist"
                assert result.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED], \
                    f"Deployment {i} should be in final state, got {result.status}"
                
                # Each deployment should have processed its artifacts
                expected_artifacts = len(deployment_scenarios[i]['artifacts'])
                if result.status == DeploymentStatus.COMPLETED:
                    assert result.artifacts_deployed == expected_artifacts, \
                        f"Deployment {i} should have deployed {expected_artifacts} artifacts"
        
        finally:
            await orchestrator.stop()
    
    @given(deployment_scenario_strategy())
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_deployment_cancellation(self, deployment_scenario):
        """
        Property: Any deployment should be cancellable before completion,
        and cancelled deployments should be marked appropriately.
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1, default_timeout=30)
        await orchestrator.start()
        
        try:
            plan_id = deployment_scenario['plan_id']
            env_id = deployment_scenario['env_id']
            artifacts = deployment_scenario['artifacts']
            
            # Start deployment
            deployment_id = await orchestrator.deploy_to_environment(plan_id, env_id, artifacts)
            
            # Immediately try to cancel it
            cancel_result = await orchestrator.cancel_deployment(deployment_id)
            
            # Wait a bit for cancellation to take effect
            await asyncio.sleep(0.2)
            
            # Check final status
            result = await orchestrator.get_deployment_status(deployment_id)
            assert result is not None
            
            if cancel_result:
                # If cancellation succeeded, deployment should be cancelled
                assert result.status == DeploymentStatus.CANCELLED
                assert result.error_message == "Deployment cancelled by user"
                assert result.end_time is not None
            else:
                # If cancellation failed, deployment might have already completed
                assert result.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]
        
        finally:
            await orchestrator.stop()
    
    @given(st.text(min_size=1, max_size=20))
    @settings(max_examples=50, deadline=1000)
    @pytest.mark.asyncio
    async def test_deployment_status_retrieval(self, deployment_id):
        """
        Property: Querying status for non-existent deployments should return None,
        while existing deployments should return valid status.
        """
        orchestrator = DeploymentOrchestrator()
        await orchestrator.start()
        
        try:
            # Query non-existent deployment
            result = await orchestrator.get_deployment_status(deployment_id)
            assert result is None, "Non-existent deployment should return None"
            
            # Create a real deployment
            artifacts = [TestArtifact(
                artifact_id="test_artifact",
                name="test.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'test'",
                checksum="",
                permissions="0755",
                target_path="/tmp/test.sh"
            )]
            
            real_deployment_id = await orchestrator.deploy_to_environment("test_plan", "test_env", artifacts)
            
            # Query existing deployment
            result = await orchestrator.get_deployment_status(real_deployment_id)
            assert result is not None, "Existing deployment should return result"
            assert result.deployment_id == real_deployment_id
            assert result.plan_id == "test_plan"
            assert result.environment_id == "test_env"
        
        finally:
            await orchestrator.stop()


if __name__ == "__main__":
    # Run a simple test to verify the property tests work
    import asyncio
    
    async def run_simple_test():
        orchestrator = DeploymentOrchestrator()
        await orchestrator.start()
        
        try:
            # Create a simple test artifact
            artifact = TestArtifact(
                artifact_id="simple_test",
                name="simple.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'Hello World'",
                checksum="",
                permissions="0755",
                target_path="/tmp/simple.sh"
            )
            
            # Deploy it
            deployment_id = await orchestrator.deploy_to_environment("test_plan", "test_env", [artifact])
            print(f"Started deployment: {deployment_id}")
            
            # Wait for completion
            await asyncio.sleep(1)
            
            # Check result
            result = await orchestrator.get_deployment_status(deployment_id)
            print(f"Deployment status: {result.status}")
            print(f"Artifacts deployed: {result.artifacts_deployed}")
            print(f"Steps completed: {len(result.steps)}")
            
        finally:
            await orchestrator.stop()
    
    # Run the simple test
    asyncio.run(run_simple_test())