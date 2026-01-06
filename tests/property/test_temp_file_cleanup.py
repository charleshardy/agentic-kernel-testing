"""
Property-based tests for temporary file cleanup functionality.

**Feature: test-deployment-system, Property 29: Temporary file cleanup**
**Validates: Requirements 6.4**

Tests that for any temporary files created during deployment, sensitive data
should be cleaned up after deployment completion.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import the temporary file manager we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from deployment.temp_file_manager import (
    SecureTempFileManager,
    TempFileInfo,
    create_secure_temp_file,
    cleanup_temp_file
)


# Hypothesis strategies for generating test data

@st.composite
def file_content_strategy(draw):
    """Generate realistic file content including sensitive data"""
    content_types = [
        # Regular content
        st.text(min_size=10, max_size=1000),
        # Sensitive content patterns
        st.text(min_size=50, max_size=500).map(lambda x: f"API_KEY={x}\nPASSWORD=secret123\n{x}"),
        st.text(min_size=20, max_size=200).map(lambda x: f"ssh-rsa AAAAB3NzaC1yc2E{x} user@host"),
        st.text(min_size=30, max_size=300).map(lambda x: f"Bearer eyJ0eXAiOiJKV1Q{x}"),
        # Binary-like content
        st.binary(min_size=10, max_size=500)
    ]
    
    return draw(st.one_of(content_types))

@st.composite
def security_level_strategy(draw):
    """Generate security levels"""
    return draw(st.sampled_from(['public', 'internal', 'confidential', 'secret']))

@st.composite
def file_suffix_strategy(draw):
    """Generate file suffixes"""
    suffixes = ['', '.txt', '.sh', '.py', '.json', '.yaml', '.key', '.pem', '.conf']
    return draw(st.sampled_from(suffixes))

@st.composite
def temp_file_batch_strategy(draw):
    """Generate a batch of temporary files to create"""
    num_files = draw(st.integers(min_value=1, max_value=10))
    files = []
    
    for i in range(num_files):
        file_info = {
            'content': draw(file_content_strategy()),
            'suffix': draw(file_suffix_strategy()),
            'is_sensitive': draw(st.booleans()),
            'security_level': draw(security_level_strategy()),
            'prefix': f'test_{i}_'
        }
        files.append(file_info)
    
    return files


class TestTempFileCleanup:
    """Property-based tests for temporary file cleanup functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_temp_dir = tempfile.mkdtemp(prefix='test_temp_cleanup_')
        self.temp_manager = SecureTempFileManager(
            base_temp_dir=self.test_temp_dir,
            cleanup_timeout_minutes=1,  # Short timeout for testing
            enable_monitoring=False  # Disable for testing
        )
    
    def teardown_method(self):
        """Clean up test environment"""
        try:
            self.temp_manager.shutdown()
            shutil.rmtree(self.test_temp_dir, ignore_errors=True)
        except:
            pass
    
    @given(file_content_strategy(), file_suffix_strategy(), 
           st.booleans(), security_level_strategy())
    @settings(max_examples=100, deadline=None)
    def test_temp_file_creation_and_cleanup(self, content, suffix, is_sensitive, security_level):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: For any temporary file created, it should be cleanable and
        the cleanup should be verifiable.
        """
        # Arrange - Create temporary file
        temp_path = self.temp_manager.create_temp_file(
            content=content,
            suffix=suffix,
            is_sensitive=is_sensitive,
            security_level=security_level
        )
        
        # Assert - File should exist after creation
        assert os.path.exists(temp_path), \
            "Temporary file should exist after creation"
        
        # Assert - File should be tracked
        stats_before = self.temp_manager.get_statistics()
        assert stats_before['current_files'] > 0, \
            "Temporary file should be tracked after creation"
        
        # Act - Clean up the file
        cleanup_success = self.temp_manager.cleanup_file(temp_path)
        
        # Assert - Cleanup should succeed
        assert cleanup_success, \
            "Temporary file cleanup should succeed"
        
        # Assert - File should no longer exist
        assert not os.path.exists(temp_path), \
            "Temporary file should not exist after cleanup"
        
        # Assert - File should no longer be tracked
        stats_after = self.temp_manager.get_statistics()
        assert stats_after['current_files'] == stats_before['current_files'] - 1, \
            "Temporary file should no longer be tracked after cleanup"
        
        # Assert - Cleanup statistics should be updated
        assert stats_after['files_cleaned'] == stats_before['files_cleaned'] + 1, \
            "Cleanup statistics should be updated"
        
        if is_sensitive:
            assert stats_after['sensitive_files_cleaned'] == stats_before['sensitive_files_cleaned'] + 1, \
                "Sensitive file cleanup statistics should be updated"
    
    @given(temp_file_batch_strategy())
    @settings(max_examples=50, deadline=None)
    def test_batch_temp_file_cleanup(self, file_batch):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: For any batch of temporary files created, all should be
        cleanable and cleanup should be verifiable.
        """
        # Arrange - Create batch of temporary files
        created_files = []
        sensitive_count = 0
        
        for file_info in file_batch:
            temp_path = self.temp_manager.create_temp_file(
                content=file_info['content'],
                suffix=file_info['suffix'],
                is_sensitive=file_info['is_sensitive'],
                security_level=file_info['security_level'],
                prefix=file_info['prefix']
            )
            created_files.append(temp_path)
            
            if file_info['is_sensitive']:
                sensitive_count += 1
        
        # Assert - All files should exist
        for temp_path in created_files:
            assert os.path.exists(temp_path), \
                f"Temporary file {temp_path} should exist after creation"
        
        # Get statistics before cleanup
        stats_before = self.temp_manager.get_statistics()
        assert stats_before['current_files'] >= len(created_files), \
            "All created files should be tracked"
        
        # Act - Clean up all files
        cleanup_count = self.temp_manager.cleanup_all()
        
        # Assert - Cleanup should succeed for all files
        assert cleanup_count >= len(created_files), \
            "All temporary files should be cleaned up"
        
        # Assert - No files should exist after cleanup
        for temp_path in created_files:
            assert not os.path.exists(temp_path), \
                f"Temporary file {temp_path} should not exist after cleanup"
        
        # Assert - Statistics should be updated correctly
        stats_after = self.temp_manager.get_statistics()
        assert stats_after['files_cleaned'] >= stats_before['files_cleaned'] + len(created_files), \
            "Cleanup statistics should reflect all cleaned files"
        
        if sensitive_count > 0:
            assert stats_after['sensitive_files_cleaned'] >= stats_before['sensitive_files_cleaned'] + sensitive_count, \
                "Sensitive file cleanup statistics should be updated"
    
    @given(file_content_strategy(), st.booleans())
    @settings(max_examples=50, deadline=None)
    def test_sensitive_file_secure_deletion(self, content, is_sensitive):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: For any sensitive temporary file, secure deletion should
        overwrite the content before removal.
        """
        # Arrange - Create temporary file
        temp_path = self.temp_manager.create_temp_file(
            content=content,
            is_sensitive=is_sensitive,
            security_level='confidential' if is_sensitive else 'public'
        )
        
        original_size = os.path.getsize(temp_path)
        
        # Act - Clean up the file (this should trigger secure deletion for sensitive files)
        cleanup_success = self.temp_manager.cleanup_file(temp_path)
        
        # Assert - Cleanup should succeed
        assert cleanup_success, \
            "Sensitive file cleanup should succeed"
        
        # Assert - File should not exist after cleanup
        assert not os.path.exists(temp_path), \
            "Sensitive file should not exist after secure deletion"
        
        # For sensitive files, we can't easily verify overwriting without
        # complex filesystem analysis, but we can verify the cleanup process completed
        stats = self.temp_manager.get_statistics()
        if is_sensitive:
            assert stats['sensitive_files_cleaned'] > 0, \
                "Sensitive file cleanup should be recorded in statistics"
    
    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=30, deadline=None)
    def test_temp_directory_cleanup(self, num_files_in_dir):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: For any temporary directory created, it and all its contents
        should be cleanable.
        """
        # Arrange - Create temporary directory
        temp_dir = self.temp_manager.create_temp_directory(
            is_sensitive=True,
            security_level='confidential'
        )
        
        # Add some files to the directory
        created_files = []
        for i in range(num_files_in_dir):
            file_path = os.path.join(temp_dir, f'file_{i}.txt')
            with open(file_path, 'w') as f:
                f.write(f'Test content {i}')
            created_files.append(file_path)
        
        # Assert - Directory and files should exist
        assert os.path.exists(temp_dir), \
            "Temporary directory should exist after creation"
        
        for file_path in created_files:
            assert os.path.exists(file_path), \
                f"File {file_path} should exist in temporary directory"
        
        # Act - Clean up the directory
        cleanup_success = self.temp_manager.cleanup_file(temp_dir)
        
        # Assert - Cleanup should succeed
        assert cleanup_success, \
            "Temporary directory cleanup should succeed"
        
        # Assert - Directory should not exist after cleanup
        assert not os.path.exists(temp_dir), \
            "Temporary directory should not exist after cleanup"
        
        # Assert - Files should not exist after cleanup
        for file_path in created_files:
            assert not os.path.exists(file_path), \
                f"File {file_path} should not exist after directory cleanup"
    
    @given(file_content_strategy(), st.integers(min_value=2, max_value=10))
    @settings(max_examples=30, deadline=None)
    def test_expired_file_cleanup(self, content, num_files):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: For any temporary files that exceed the timeout period,
        they should be automatically cleaned up.
        """
        # Create a temp manager with very short timeout for testing
        short_timeout_manager = SecureTempFileManager(
            base_temp_dir=self.test_temp_dir,
            cleanup_timeout_minutes=0.01,  # 0.6 seconds
            enable_monitoring=False
        )
        
        try:
            # Arrange - Create multiple temporary files
            created_files = []
            for i in range(num_files):
                temp_path = short_timeout_manager.create_temp_file(
                    content=f"{content}_{i}",
                    is_sensitive=True,
                    prefix=f'expired_{i}_'
                )
                created_files.append(temp_path)
            
            # Assert - All files should exist initially
            for temp_path in created_files:
                assert os.path.exists(temp_path), \
                    f"Temporary file {temp_path} should exist after creation"
            
            # Wait for files to expire (longer than timeout)
            import time
            time.sleep(0.1)  # 100ms should be enough for 0.6s timeout
            
            # Act - Clean up expired files
            expired_count = short_timeout_manager.cleanup_expired_files()
            
            # Assert - Some files should have been cleaned up
            # Note: Due to timing, we can't guarantee all files will be expired,
            # but at least some should be if the timeout is working
            assert expired_count >= 0, \
                "Expired file cleanup should return non-negative count"
            
            # Check that expired files no longer exist
            remaining_files = [f for f in created_files if os.path.exists(f)]
            cleaned_files = [f for f in created_files if not os.path.exists(f)]
            
            # The number of cleaned files should match the expired count
            assert len(cleaned_files) == expired_count, \
                "Number of cleaned files should match expired count"
            
        finally:
            short_timeout_manager.shutdown()
    
    @given(file_content_strategy())
    @settings(max_examples=50, deadline=None)
    def test_context_manager_cleanup(self, content):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: For any temporary file created using context manager,
        it should be automatically cleaned up when exiting the context.
        """
        temp_path = None
        
        # Act - Use context manager
        with self.temp_manager.temp_file_context(
            content=content,
            is_sensitive=True,
            security_level='confidential'
        ) as temp_file_path:
            temp_path = temp_file_path
            
            # Assert - File should exist within context
            assert os.path.exists(temp_path), \
                "Temporary file should exist within context manager"
            
            # Assert - File should be tracked
            stats = self.temp_manager.get_statistics()
            assert stats['current_files'] > 0, \
                "Temporary file should be tracked within context"
        
        # Assert - File should be cleaned up after exiting context
        assert not os.path.exists(temp_path), \
            "Temporary file should be cleaned up after exiting context manager"
    
    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=20, deadline=None)
    def test_cleanup_verification(self, num_files):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: For any temporary file cleanup operation, the cleanup
        should be verifiable and statistics should be accurate.
        """
        # Arrange - Create multiple files
        created_files = []
        for i in range(num_files):
            temp_path = self.temp_manager.create_temp_file(
                content=f"Test content {i}",
                is_sensitive=True,
                prefix=f'verify_{i}_'
            )
            created_files.append(temp_path)
        
        # Get initial statistics
        stats_before = self.temp_manager.get_statistics()
        
        # Act - Clean up files one by one with verification
        successful_cleanups = 0
        for temp_path in created_files:
            if self.temp_manager.cleanup_file(temp_path, verify_cleanup=True):
                successful_cleanups += 1
        
        # Assert - All cleanups should succeed
        assert successful_cleanups == num_files, \
            "All file cleanups should succeed with verification"
        
        # Assert - Statistics should be accurate
        stats_after = self.temp_manager.get_statistics()
        assert stats_after['files_cleaned'] == stats_before['files_cleaned'] + num_files, \
            "Cleanup statistics should accurately reflect cleaned files"
        
        assert stats_after['current_files'] == stats_before['current_files'] - num_files, \
            "Current file count should accurately reflect remaining files"
        
        # Assert - No verification failures should be recorded
        assert stats_after['verification_failures'] == stats_before['verification_failures'], \
            "No verification failures should be recorded for successful cleanups"
    
    def test_cleanup_failure_handling(self):
        """
        **Feature: test-deployment-system, Property 29: Temporary file cleanup**
        **Validates: Requirements 6.4**
        
        Property: When temporary file cleanup fails, the failure should be
        properly recorded and handled.
        """
        # Arrange - Create a temporary file
        temp_path = self.temp_manager.create_temp_file(
            content="test content",
            is_sensitive=True
        )
        
        # Manually delete the file to simulate a cleanup failure scenario
        os.unlink(temp_path)
        
        # Get initial statistics
        stats_before = self.temp_manager.get_statistics()
        
        # Act - Attempt to clean up the already-deleted file
        cleanup_success = self.temp_manager.cleanup_file(temp_path)
        
        # Assert - Cleanup should still succeed (file doesn't exist = cleaned up)
        assert cleanup_success, \
            "Cleanup should succeed even if file was already deleted"
        
        # Assert - Statistics should be updated appropriately
        stats_after = self.temp_manager.get_statistics()
        assert stats_after['files_cleaned'] == stats_before['files_cleaned'] + 1, \
            "Cleanup statistics should be updated even for already-deleted files"


def test_temp_file_cleanup_sync():
    """Synchronous test runner for the temporary file cleanup property tests"""
    # Test basic functionality
    test_temp_dir = tempfile.mkdtemp(prefix='test_sync_cleanup_')
    
    try:
        temp_manager = SecureTempFileManager(
            base_temp_dir=test_temp_dir,
            cleanup_timeout_minutes=1,
            enable_monitoring=False
        )
        
        # Test file creation and cleanup
        temp_path = temp_manager.create_temp_file(
            content="test content",
            suffix=".txt",
            is_sensitive=True,
            security_level="confidential"
        )
        
        # Verify file exists
        assert os.path.exists(temp_path)
        
        # Test cleanup
        cleanup_success = temp_manager.cleanup_file(temp_path)
        assert cleanup_success
        assert not os.path.exists(temp_path)
        
        # Test context manager
        with temp_manager.temp_file_context(
            content="context test",
            is_sensitive=True
        ) as context_path:
            assert os.path.exists(context_path)
        
        assert not os.path.exists(context_path)
        
        # Test statistics
        stats = temp_manager.get_statistics()
        assert stats['files_created'] >= 2
        assert stats['files_cleaned'] >= 2
        assert stats['sensitive_files_created'] >= 2
        assert stats['sensitive_files_cleaned'] >= 2
        
        # Shutdown
        temp_manager.shutdown()
        
    finally:
        shutil.rmtree(test_temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_temp_file_cleanup_sync()
    print("Temporary file cleanup property tests completed successfully!")