"""
Property-based tests for log sanitization functionality

**Feature: test-deployment-system, Property 28: Log sanitization**

Tests that sensitive information is properly sanitized from deployment logs
according to Requirements 6.3.
"""

import pytest
import tempfile
import shutil
import json
from datetime import datetime
from typing import Dict, List, Any
from hypothesis import given, strategies as st, settings

from deployment.log_sanitizer import LogSanitizer, SecureLogStorage, TemporaryFileManager
from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    DeploymentPlan, DeploymentResult, DeploymentStatus, TestArtifact, 
    ArtifactType, DeploymentConfig, Priority
)


class TestLogSanitizationProperties:
    """Property-based tests for log sanitization"""
    
    @given(
        sensitive_passwords=st.lists(st.text(min_size=8, max_size=20), min_size=1, max_size=5),
        sensitive_api_keys=st.lists(st.text(min_size=16, max_size=64), min_size=1, max_size=3),
        sensitive_tokens=st.lists(st.text(min_size=20, max_size=100), min_size=1, max_size=3),
        log_message_count=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=50, deadline=5000)
    async def test_log_sanitization_completeness(self, 
                                                sensitive_passwords: List[str],
                                                sensitive_api_keys: List[str], 
                                                sensitive_tokens: List[str],
                                                log_message_count: int):
        """
        **Feature: test-deployment-system, Property 28: Log sanitization**
        **Validates: Requirements 6.3**
        
        Property: Log sanitization completeness
        For any deployment log creation containing sensitive information,
        all sensitive data should be sanitized and replaced with redaction markers.
        
        Validates that:
        1. All sensitive patterns are detected and sanitized
        2. Original sensitive data is not present in sanitized logs
        3. Redaction markers are properly inserted
        4. Log structure and non-sensitive data remain intact
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create log sanitizer
            sanitizer = LogSanitizer()
            secure_storage = SecureLogStorage(temp_dir, sanitizer)
            
            # Generate log entries with embedded sensitive data
            log_entries = []
            all_sensitive_data = set()
            
            for i in range(log_message_count):
                # Create log entry with sensitive data
                password = sensitive_passwords[i % len(sensitive_passwords)]
                api_key = sensitive_api_keys[i % len(sensitive_api_keys)]
                token = sensitive_tokens[i % len(sensitive_tokens)]
                
                all_sensitive_data.update([password, api_key, token])
                
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "event": f"deployment_step_{i}",
                    "deployment_id": f"test_deployment_{i}",
                    "message": f"Processing with password={password} and api_key={api_key}",
                    "config": f"auth_token={token}",
                    "details": {
                        "credentials": f"secret={password}",
                        "api_config": f"api_key={api_key}"
                    }
                }
                log_entries.append(log_entry)
            
            # Store and sanitize log entries
            deployment_id = "sanitization_test"
            for entry in log_entries:
                secure_storage.store_log_entry(deployment_id, entry, sanitize=True)
            
            # Retrieve sanitized logs
            sanitized_logs = secure_storage.get_log_entries(deployment_id, sanitized_only=True)
            
            # Verify sanitization completeness
            assert len(sanitized_logs) == len(log_entries), \
                f"Expected {len(log_entries)} sanitized logs, got {len(sanitized_logs)}"
            
            # Check that all sensitive data has been sanitized
            for log_entry in sanitized_logs:
                log_str = json.dumps(log_entry)
                
                # Verify no sensitive data remains
                for sensitive_item in all_sensitive_data:
                    assert sensitive_item not in log_str, \
                        f"Sensitive data '{sensitive_item}' found in sanitized log: {log_str}"
                
                # Verify redaction markers are present
                assert "[REDACTED]" in log_str, \
                    f"No redaction markers found in sanitized log: {log_str}"
                
                # Verify sanitization markers are present
                assert "[SANITIZED:" in log_str, \
                    f"No sanitization markers found in log: {log_str}"
            
            # Verify log structure integrity
            for i, sanitized_entry in enumerate(sanitized_logs):
                original_entry = log_entries[i]
                
                # Non-sensitive fields should remain unchanged
                assert sanitized_entry["timestamp"] == original_entry["timestamp"]
                assert sanitized_entry["event"] == original_entry["event"]
                assert sanitized_entry["deployment_id"] == original_entry["deployment_id"]
                
                # Sensitive fields should be sanitized but structure preserved
                assert "message" in sanitized_entry
                assert "config" in sanitized_entry
                assert "details" in sanitized_entry
                assert isinstance(sanitized_entry["details"], dict)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        mixed_content=st.lists(
            st.one_of(
                st.text(min_size=10, max_size=50),  # Regular text
                st.text(min_size=8, max_size=20).map(lambda x: f"password={x}"),  # Password
                st.text(min_size=16, max_size=32).map(lambda x: f"api_key={x}"),  # API key
                st.text(min_size=20, max_size=40).map(lambda x: f"secret={x}"),   # Secret
            ),
            min_size=5, max_size=15
        ),
        deployment_count=st.integers(min_value=3, max_value=8)
    )
    @settings(max_examples=40, deadline=6000)
    async def test_sanitization_pattern_detection(self, 
                                                 mixed_content: List[str],
                                                 deployment_count: int):
        """
        **Feature: test-deployment-system, Property 28: Log sanitization**
        **Validates: Requirements 6.3**
        
        Property: Sanitization pattern detection accuracy
        For any log content with mixed sensitive and non-sensitive data,
        only sensitive patterns should be sanitized while preserving non-sensitive content.
        
        Validates that:
        1. Sensitive patterns are accurately detected
        2. Non-sensitive content remains unchanged
        3. Pattern detection works across different content structures
        4. False positives are minimized
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            orchestrator = DeploymentOrchestrator(
                max_concurrent_deployments=1,
                log_dir=temp_dir,
                enable_security=False
            )
            
            await orchestrator.start()
            
            # Track what should and shouldn't be sanitized
            sensitive_patterns = []
            non_sensitive_content = []
            
            for content in mixed_content:
                if any(pattern in content.lower() for pattern in ['password=', 'api_key=', 'secret=']):
                    sensitive_patterns.append(content)
                else:
                    non_sensitive_content.append(content)
            
            # Create deployment logs with mixed content
            for i in range(deployment_count):
                deployment_id = f"pattern_test_{i}"
                
                # Create log entry with mixed content
                log_message = " | ".join(mixed_content)
                
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "event": "deployment_test",
                    "deployment_id": deployment_id,
                    "message": log_message,
                    "mixed_data": mixed_content
                }
                
                # Store with sanitization
                orchestrator.secure_log_storage.store_log_entry(
                    deployment_id, log_entry, sanitize=True
                )
            
            # Verify pattern detection accuracy
            for i in range(deployment_count):
                deployment_id = f"pattern_test_{i}"
                sanitized_logs = orchestrator.secure_log_storage.get_log_entries(
                    deployment_id, sanitized_only=True
                )
                
                assert len(sanitized_logs) == 1, f"Expected 1 log entry, got {len(sanitized_logs)}"
                
                sanitized_entry = sanitized_logs[0]
                sanitized_str = json.dumps(sanitized_entry)
                
                # Check that sensitive patterns were sanitized
                for sensitive_content in sensitive_patterns:
                    # Extract the sensitive value (after =)
                    if '=' in sensitive_content:
                        sensitive_value = sensitive_content.split('=', 1)[1]
                        assert sensitive_value not in sanitized_str, \
                            f"Sensitive value '{sensitive_value}' not sanitized in: {sanitized_str}"
                
                # Check that non-sensitive content is preserved
                for non_sensitive in non_sensitive_content:
                    # Non-sensitive content should still be present
                    assert non_sensitive in sanitized_str, \
                        f"Non-sensitive content '{non_sensitive}' was incorrectly sanitized: {sanitized_str}"
                
                # If there were sensitive patterns, redaction markers should be present
                if sensitive_patterns:
                    assert "[REDACTED]" in sanitized_str, \
                        f"Expected redaction markers for sensitive content: {sanitized_str}"
            
        finally:
            await orchestrator.stop()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        log_formats=st.lists(
            st.one_of(
                st.dictionaries(
                    st.just("type"), st.just("json")
                ).flatmap(lambda _: st.dictionaries(
                    st.text(min_size=3, max_size=10),
                    st.one_of(
                        st.text(min_size=5, max_size=30),
                        st.text(min_size=8, max_size=20).map(lambda x: f"password={x}")
                    )
                ).map(lambda data: {"type": "json", "data": data})),
                st.text(min_size=20, max_size=100).map(lambda data: {"type": "string", "data": data})
            ),
            min_size=3, max_size=10
        ),
        concurrent_deployments=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=30, deadline=8000)
    async def test_sanitization_format_preservation(self, 
                                                   log_formats: List[Dict[str, Any]],
                                                   concurrent_deployments: int):
        """
        **Feature: test-deployment-system, Property 28: Log sanitization**
        **Validates: Requirements 6.3**
        
        Property: Log format preservation during sanitization
        For any log format (JSON, string, nested structures), sanitization should
        preserve the original format while removing sensitive content.
        
        Validates that:
        1. JSON structure is preserved after sanitization
        2. String logs maintain readability
        3. Nested data structures remain intact
        4. Sanitization works consistently across different formats
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            sanitizer = LogSanitizer()
            
            # Test different log formats
            for format_spec in log_formats:
                if format_spec["type"] == "json":
                    # Test JSON log sanitization
                    original_data = format_spec["data"]
                    sanitized_data = sanitizer.sanitize_json_log(original_data)
                    
                    # Verify structure preservation
                    assert isinstance(sanitized_data, dict), \
                        "JSON log should remain a dictionary after sanitization"
                    
                    assert set(sanitized_data.keys()) == set(original_data.keys()), \
                        "JSON keys should be preserved during sanitization"
                    
                    # Check for sensitive data removal
                    sanitized_str = json.dumps(sanitized_data)
                    for key, value in original_data.items():
                        if isinstance(value, str) and "password=" in value:
                            password_value = value.split("password=")[1]
                            assert password_value not in sanitized_str, \
                                f"Password value '{password_value}' not sanitized"
                
                elif format_spec["type"] == "string":
                    # Test string log sanitization
                    original_string = format_spec["data"]
                    sanitized_string = sanitizer.sanitize_log_entry(original_string)
                    
                    # Verify it's still a string
                    assert isinstance(sanitized_string, str), \
                        "String log should remain a string after sanitization"
                    
                    # Verify length is reasonable (not empty unless original was empty)
                    if original_string.strip():
                        assert sanitized_string.strip(), \
                            "Non-empty string should not become empty after sanitization"
            
            # Test concurrent sanitization to ensure thread safety
            import asyncio
            
            async def sanitize_concurrently(deployment_index: int):
                """Helper to test concurrent sanitization"""
                test_data = {
                    "deployment_id": f"concurrent_{deployment_index}",
                    "password": f"secret_{deployment_index}",
                    "api_key": f"key_{deployment_index}",
                    "message": f"Processing deployment {deployment_index} with sensitive data"
                }
                
                sanitized = sanitizer.sanitize_json_log(test_data)
                
                # Verify sanitization worked
                sanitized_str = json.dumps(sanitized)
                assert f"secret_{deployment_index}" not in sanitized_str
                assert f"key_{deployment_index}" not in sanitized_str
                assert "[REDACTED]" in sanitized_str
                
                return sanitized
            
            # Run concurrent sanitization tasks
            tasks = [
                sanitize_concurrently(i) for i in range(concurrent_deployments)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all concurrent operations succeeded
            assert len(results) == concurrent_deployments, \
                f"Expected {concurrent_deployments} results, got {len(results)}"
            
            for result in results:
                assert isinstance(result, dict), "Each result should be a dictionary"
                assert "deployment_id" in result, "Deployment ID should be preserved"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        sensitive_data_types=st.lists(
            st.one_of(
                st.text(min_size=8, max_size=20).map(lambda x: ("password", x)),
                st.text(min_size=16, max_size=40).map(lambda x: ("api_key", x)),
                st.text(min_size=20, max_size=50).map(lambda x: ("secret", x)),
                st.text(min_size=10, max_size=30).map(lambda x: ("token", x)),
                st.text(min_size=5, max_size=15).map(lambda x: ("private_key", f"-----BEGIN PRIVATE KEY-----\n{x}\n-----END PRIVATE KEY-----"))
            ),
            min_size=3, max_size=8
        ),
        log_entry_count=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=35, deadline=7000)
    async def test_comprehensive_sensitive_pattern_coverage(self, 
                                                          sensitive_data_types: List[tuple],
                                                          log_entry_count: int):
        """
        **Feature: test-deployment-system, Property 28: Log sanitization**
        **Validates: Requirements 6.3**
        
        Property: Comprehensive sensitive pattern coverage
        For any type of sensitive information (passwords, keys, tokens, certificates),
        the sanitization system should detect and sanitize all patterns.
        
        Validates that:
        1. All types of sensitive patterns are detected
        2. Different sensitive data formats are handled
        3. Sanitization statistics are accurately tracked
        4. No sensitive data leaks through unrecognized patterns
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            orchestrator = DeploymentOrchestrator(
                max_concurrent_deployments=1,
                log_dir=temp_dir,
                enable_security=False
            )
            
            await orchestrator.start()
            
            # Track all sensitive values for verification
            all_sensitive_values = set()
            pattern_counts = {}
            
            # Generate log entries with various sensitive data types
            for i in range(log_entry_count):
                deployment_id = f"comprehensive_test_{i}"
                
                # Select sensitive data for this log entry
                selected_data = sensitive_data_types[i % len(sensitive_data_types)]
                pattern_type, sensitive_value = selected_data
                
                all_sensitive_values.add(sensitive_value)
                pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
                
                # Create log entry with the sensitive data
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "event": "comprehensive_test",
                    "deployment_id": deployment_id,
                    "message": f"Processing with {pattern_type}={sensitive_value}",
                    "config": {
                        pattern_type: sensitive_value,
                        "other_data": f"non_sensitive_value_{i}"
                    }
                }
                
                # Store with sanitization
                orchestrator.secure_log_storage.store_log_entry(
                    deployment_id, log_entry, sanitize=True
                )
            
            # Verify comprehensive sanitization
            for i in range(log_entry_count):
                deployment_id = f"comprehensive_test_{i}"
                sanitized_logs = orchestrator.secure_log_storage.get_log_entries(
                    deployment_id, sanitized_only=True
                )
                
                assert len(sanitized_logs) == 1, f"Expected 1 log entry for {deployment_id}"
                
                sanitized_entry = sanitized_logs[0]
                sanitized_str = json.dumps(sanitized_entry)
                
                # Verify no sensitive values remain
                for sensitive_value in all_sensitive_values:
                    # Handle multi-line private keys specially
                    if "-----BEGIN PRIVATE KEY-----" in sensitive_value:
                        # Check that the key content is sanitized
                        key_lines = sensitive_value.split('\n')
                        for line in key_lines[1:-1]:  # Skip header/footer
                            if line.strip():
                                assert line not in sanitized_str, \
                                    f"Private key content '{line}' not sanitized"
                    else:
                        assert sensitive_value not in sanitized_str, \
                            f"Sensitive value '{sensitive_value}' not sanitized in: {sanitized_str}"
                
                # Verify redaction markers are present
                assert "[REDACTED]" in sanitized_str, \
                    f"No redaction markers found in: {sanitized_str}"
            
            # Verify sanitization statistics
            sanitization_stats = orchestrator.log_sanitizer.get_sanitization_stats()
            
            assert sanitization_stats["total_logs_processed"] >= log_entry_count, \
                f"Expected at least {log_entry_count} logs processed, got {sanitization_stats['total_logs_processed']}"
            
            assert sanitization_stats["sensitive_items_found"] > 0, \
                "Should have found sensitive items to sanitize"
            
            # Verify pattern matching statistics
            patterns_matched = sanitization_stats["patterns_matched"]
            assert len(patterns_matched) > 0, "Should have matched some patterns"
            
            # Check that different pattern types were detected
            detected_patterns = set(patterns_matched.keys())
            expected_patterns = set(pattern_type for pattern_type, _ in sensitive_data_types)
            
            # At least some of the expected patterns should be detected
            common_patterns = detected_patterns.intersection(expected_patterns)
            assert len(common_patterns) > 0, \
                f"Expected to detect patterns {expected_patterns}, but only found {detected_patterns}"
            
        finally:
            await orchestrator.stop()
            shutil.rmtree(temp_dir, ignore_errors=True)


# Synchronous test wrappers for pytest compatibility
def test_log_sanitization_completeness_sync():
    """Sync wrapper for log sanitization completeness test"""
    import asyncio
    from hypothesis import given, strategies as st, settings
    
    @given(
        sensitive_passwords=st.lists(st.text(min_size=8, max_size=20), min_size=1, max_size=5),
        sensitive_api_keys=st.lists(st.text(min_size=16, max_size=64), min_size=1, max_size=3),
        sensitive_tokens=st.lists(st.text(min_size=20, max_size=100), min_size=1, max_size=3),
        log_message_count=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=10, deadline=5000)
    def run_test(sensitive_passwords, sensitive_api_keys, sensitive_tokens, log_message_count):
        test_instance = TestLogSanitizationProperties()
        asyncio.run(test_instance.test_log_sanitization_completeness(
            sensitive_passwords, sensitive_api_keys, sensitive_tokens, log_message_count
        ))
    
    run_test()

def test_sanitization_pattern_detection_sync():
    """Sync wrapper for pattern detection test"""
    import asyncio
    from hypothesis import given, strategies as st, settings
    
    @given(
        mixed_content=st.lists(
            st.one_of(
                st.text(min_size=10, max_size=50),  # Regular text
                st.text(min_size=8, max_size=20).map(lambda x: f"password={x}"),  # Password
                st.text(min_size=16, max_size=32).map(lambda x: f"api_key={x}"),  # API key
                st.text(min_size=20, max_size=40).map(lambda x: f"secret={x}"),   # Secret
            ),
            min_size=5, max_size=15
        ),
        deployment_count=st.integers(min_value=3, max_value=8)
    )
    @settings(max_examples=10, deadline=6000)
    def run_test(mixed_content, deployment_count):
        test_instance = TestLogSanitizationProperties()
        asyncio.run(test_instance.test_sanitization_pattern_detection(
            mixed_content, deployment_count
        ))
    
    run_test()

def test_sanitization_format_preservation_sync():
    """Sync wrapper for format preservation test"""
    import asyncio
    from hypothesis import given, strategies as st, settings
    
    @given(
        log_formats=st.lists(
            st.one_of(
                st.dictionaries(
                    st.just("type"), st.just("json")
                ).flatmap(lambda _: st.dictionaries(
                    st.text(min_size=3, max_size=10),
                    st.one_of(
                        st.text(min_size=5, max_size=30),
                        st.text(min_size=8, max_size=20).map(lambda x: f"password={x}")
                    )
                ).map(lambda data: {"type": "json", "data": data})),
                st.text(min_size=20, max_size=100).map(lambda data: {"type": "string", "data": data})
            ),
            min_size=3, max_size=10
        ),
        concurrent_deployments=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=8, deadline=8000)
    def run_test(log_formats, concurrent_deployments):
        test_instance = TestLogSanitizationProperties()
        asyncio.run(test_instance.test_sanitization_format_preservation(
            log_formats, concurrent_deployments
        ))
    
    run_test()

def test_comprehensive_sensitive_pattern_coverage_sync():
    """Sync wrapper for comprehensive pattern coverage test"""
    import asyncio
    from hypothesis import given, strategies as st, settings
    
    @given(
        sensitive_data_types=st.lists(
            st.one_of(
                st.text(min_size=8, max_size=20).map(lambda x: ("password", x)),
                st.text(min_size=16, max_size=40).map(lambda x: ("api_key", x)),
                st.text(min_size=20, max_size=50).map(lambda x: ("secret", x)),
                st.text(min_size=10, max_size=30).map(lambda x: ("token", x)),
                st.text(min_size=5, max_size=15).map(lambda x: ("private_key", f"-----BEGIN PRIVATE KEY-----\n{x}\n-----END PRIVATE KEY-----"))
            ),
            min_size=3, max_size=8
        ),
        log_entry_count=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=8, deadline=7000)
    def run_test(sensitive_data_types, log_entry_count):
        test_instance = TestLogSanitizationProperties()
        asyncio.run(test_instance.test_comprehensive_sensitive_pattern_coverage(
            sensitive_data_types, log_entry_count
        ))
    
    run_test()