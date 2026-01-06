"""
Secure Temporary File Manager

Provides secure temporary file creation, handling, and automatic cleanup
for sensitive deployment data with comprehensive monitoring and verification.
"""

import logging
import os
import tempfile
import shutil
import hashlib
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
import atexit
import weakref


logger = logging.getLogger(__name__)


@dataclass
class TempFileInfo:
    """Information about a temporary file"""
    file_path: str
    created_at: datetime
    is_sensitive: bool
    security_level: str  # public, internal, confidential, secret
    cleanup_required: bool
    owner_process: Optional[int] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    file_size: int = 0
    checksum: Optional[str] = None
    cleanup_verified: bool = False


class SecureTempFileManager:
    """
    Manages secure temporary files with automatic cleanup and monitoring.
    
    Features:
    - Secure temporary file creation with appropriate permissions
    - Automatic cleanup of sensitive files after deployment
    - Cleanup verification and monitoring
    - Thread-safe operations
    - Process cleanup on exit
    """
    
    def __init__(self, base_temp_dir: Optional[str] = None, 
                 cleanup_timeout_minutes: int = 60,
                 enable_monitoring: bool = True):
        """
        Initialize the secure temporary file manager.
        
        Args:
            base_temp_dir: Base directory for temporary files (uses system temp if None)
            cleanup_timeout_minutes: Maximum time before forced cleanup
            enable_monitoring: Enable background monitoring and cleanup
        """
        self.base_temp_dir = Path(base_temp_dir) if base_temp_dir else Path(tempfile.gettempdir())
        self.cleanup_timeout_minutes = cleanup_timeout_minutes
        self.enable_monitoring = enable_monitoring
        
        # Create secure temp directory
        self.secure_temp_dir = self.base_temp_dir / "aats_secure_temp"
        self.secure_temp_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        
        # File tracking
        self._temp_files: Dict[str, TempFileInfo] = {}
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Statistics
        self._stats = {
            'files_created': 0,
            'files_cleaned': 0,
            'sensitive_files_created': 0,
            'sensitive_files_cleaned': 0,
            'cleanup_failures': 0,
            'verification_failures': 0
        }
        
        # Start monitoring thread
        if self.enable_monitoring:
            self._start_monitoring()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
        
        logger.info(f"SecureTempFileManager initialized with temp_dir={self.secure_temp_dir}")
    
    def create_temp_file(self, 
                        content: Union[str, bytes],
                        suffix: str = "",
                        prefix: str = "aats_",
                        is_sensitive: bool = True,
                        security_level: str = "confidential",
                        permissions: int = 0o600) -> str:
        """
        Create a secure temporary file with specified content.
        
        Args:
            content: Content to write to the file
            suffix: File suffix (e.g., '.txt', '.sh')
            prefix: File prefix
            is_sensitive: Whether the file contains sensitive data
            security_level: Security classification (public, internal, confidential, secret)
            permissions: File permissions (default: owner read/write only)
            
        Returns:
            Path to the created temporary file
        """
        with self._lock:
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix,
                prefix=prefix,
                dir=str(self.secure_temp_dir)
            )
            
            try:
                # Write content
                if isinstance(content, str):
                    content_bytes = content.encode('utf-8')
                else:
                    content_bytes = content
                
                os.write(fd, content_bytes)
                os.close(fd)
                
                # Set secure permissions
                os.chmod(temp_path, permissions)
                
                # Calculate checksum for verification
                checksum = hashlib.sha256(content_bytes).hexdigest()
                
                # Track the file
                file_info = TempFileInfo(
                    file_path=temp_path,
                    created_at=datetime.now(),
                    is_sensitive=is_sensitive,
                    security_level=security_level,
                    cleanup_required=True,
                    owner_process=os.getpid(),
                    file_size=len(content_bytes),
                    checksum=checksum
                )
                
                self._temp_files[temp_path] = file_info
                
                # Update statistics
                self._stats['files_created'] += 1
                if is_sensitive:
                    self._stats['sensitive_files_created'] += 1
                
                logger.info(f"Created temporary file: {temp_path} (sensitive={is_sensitive}, level={security_level})")
                return temp_path
                
            except Exception as e:
                # Clean up on error
                try:
                    os.close(fd)
                    os.unlink(temp_path)
                except:
                    pass
                raise RuntimeError(f"Failed to create temporary file: {e}")
    
    def create_temp_directory(self,
                            prefix: str = "aats_dir_",
                            is_sensitive: bool = True,
                            security_level: str = "confidential",
                            permissions: int = 0o700) -> str:
        """
        Create a secure temporary directory.
        
        Args:
            prefix: Directory prefix
            is_sensitive: Whether the directory will contain sensitive data
            security_level: Security classification
            permissions: Directory permissions (default: owner access only)
            
        Returns:
            Path to the created temporary directory
        """
        with self._lock:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(
                prefix=prefix,
                dir=str(self.secure_temp_dir)
            )
            
            # Set secure permissions
            os.chmod(temp_dir, permissions)
            
            # Track the directory
            dir_info = TempFileInfo(
                file_path=temp_dir,
                created_at=datetime.now(),
                is_sensitive=is_sensitive,
                security_level=security_level,
                cleanup_required=True,
                owner_process=os.getpid()
            )
            
            self._temp_files[temp_dir] = dir_info
            
            logger.info(f"Created temporary directory: {temp_dir} (sensitive={is_sensitive})")
            return temp_dir
    
    @contextmanager
    def temp_file_context(self, 
                         content: Union[str, bytes],
                         suffix: str = "",
                         is_sensitive: bool = True,
                         security_level: str = "confidential"):
        """
        Context manager for temporary files with automatic cleanup.
        
        Args:
            content: Content to write to the file
            suffix: File suffix
            is_sensitive: Whether the file contains sensitive data
            security_level: Security classification
            
        Yields:
            Path to the temporary file
        """
        temp_path = None
        try:
            temp_path = self.create_temp_file(
                content=content,
                suffix=suffix,
                is_sensitive=is_sensitive,
                security_level=security_level
            )
            yield temp_path
        finally:
            if temp_path:
                self.cleanup_file(temp_path)
    
    def access_file(self, file_path: str) -> bool:
        """
        Record file access for monitoring.
        
        Args:
            file_path: Path to the file being accessed
            
        Returns:
            True if file exists and is tracked, False otherwise
        """
        with self._lock:
            if file_path in self._temp_files:
                file_info = self._temp_files[file_path]
                file_info.access_count += 1
                file_info.last_accessed = datetime.now()
                return True
            return False
    
    def cleanup_file(self, file_path: str, verify_cleanup: bool = True) -> bool:
        """
        Clean up a specific temporary file or directory.
        
        Args:
            file_path: Path to the file/directory to clean up
            verify_cleanup: Whether to verify the cleanup was successful
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        with self._lock:
            if file_path not in self._temp_files:
                logger.warning(f"Attempted to cleanup untracked file: {file_path}")
                return False
            
            file_info = self._temp_files[file_path]
            
            try:
                # Perform cleanup based on file type
                if os.path.isfile(file_path):
                    # For sensitive files, overwrite before deletion
                    if file_info.is_sensitive:
                        self._secure_delete_file(file_path)
                    else:
                        os.unlink(file_path)
                elif os.path.isdir(file_path):
                    # For sensitive directories, secure delete all contents
                    if file_info.is_sensitive:
                        self._secure_delete_directory(file_path)
                    else:
                        shutil.rmtree(file_path)
                
                # Verify cleanup if requested
                if verify_cleanup:
                    if os.path.exists(file_path):
                        logger.error(f"Cleanup verification failed: {file_path} still exists")
                        self._stats['verification_failures'] += 1
                        return False
                    else:
                        file_info.cleanup_verified = True
                
                # Update tracking
                del self._temp_files[file_path]
                
                # Update statistics
                self._stats['files_cleaned'] += 1
                if file_info.is_sensitive:
                    self._stats['sensitive_files_cleaned'] += 1
                
                logger.info(f"Successfully cleaned up temporary file: {file_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {file_path}: {e}")
                self._stats['cleanup_failures'] += 1
                return False
    
    def _secure_delete_file(self, file_path: str):
        """
        Securely delete a file by overwriting it multiple times.
        
        Args:
            file_path: Path to the file to securely delete
        """
        try:
            file_size = os.path.getsize(file_path)
            
            # Overwrite with random data multiple times
            with open(file_path, 'r+b') as f:
                for _ in range(3):  # 3 passes of overwriting
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            os.unlink(file_path)
            
        except Exception as e:
            logger.error(f"Secure delete failed for {file_path}: {e}")
            # Fall back to regular deletion
            try:
                os.unlink(file_path)
            except:
                pass
    
    def _secure_delete_directory(self, dir_path: str):
        """
        Securely delete a directory and all its contents.
        
        Args:
            dir_path: Path to the directory to securely delete
        """
        try:
            # Recursively secure delete all files
            for root, dirs, files in os.walk(dir_path, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    self._secure_delete_file(file_path)
                
                # Remove empty directories
                for dir in dirs:
                    dir_path_full = os.path.join(root, dir)
                    try:
                        os.rmdir(dir_path_full)
                    except:
                        pass
            
            # Remove the main directory
            os.rmdir(dir_path)
            
        except Exception as e:
            logger.error(f"Secure directory delete failed for {dir_path}: {e}")
            # Fall back to regular deletion
            try:
                shutil.rmtree(dir_path)
            except:
                pass
    
    def cleanup_expired_files(self) -> int:
        """
        Clean up files that have exceeded the timeout.
        
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        current_time = datetime.now()
        timeout_delta = timedelta(minutes=self.cleanup_timeout_minutes)
        
        with self._lock:
            expired_files = []
            
            for file_path, file_info in self._temp_files.items():
                if current_time - file_info.created_at > timeout_delta:
                    expired_files.append(file_path)
            
            for file_path in expired_files:
                if self.cleanup_file(file_path):
                    cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired temporary files")
        
        return cleaned_count
    
    def cleanup_all(self, force: bool = False) -> int:
        """
        Clean up all tracked temporary files.
        
        Args:
            force: Force cleanup even if files are recently created
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        
        with self._lock:
            file_paths = list(self._temp_files.keys())
            
            for file_path in file_paths:
                if self.cleanup_file(file_path):
                    cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} temporary files")
        return cleaned_count
    
    def _start_monitoring(self):
        """Start the background monitoring thread."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="TempFileCleanupMonitor"
            )
            self._cleanup_thread.start()
            logger.info("Started temporary file monitoring thread")
    
    def _monitoring_loop(self):
        """Background monitoring loop for automatic cleanup."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up expired files
                self.cleanup_expired_files()
                
                # Sleep for monitoring interval (check every 5 minutes)
                if self._shutdown_event.wait(300):  # 5 minutes
                    break
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get temporary file management statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self._lock:
            current_files = len(self._temp_files)
            sensitive_files = sum(1 for info in self._temp_files.values() if info.is_sensitive)
            
            return {
                **self._stats,
                'current_files': current_files,
                'current_sensitive_files': sensitive_files,
                'cleanup_timeout_minutes': self.cleanup_timeout_minutes,
                'monitoring_enabled': self.enable_monitoring
            }
    
    def list_temp_files(self, include_details: bool = False) -> List[Dict[str, Any]]:
        """
        List all currently tracked temporary files.
        
        Args:
            include_details: Whether to include detailed file information
            
        Returns:
            List of file information dictionaries
        """
        with self._lock:
            files = []
            
            for file_path, file_info in self._temp_files.items():
                file_data = {
                    'path': file_path,
                    'is_sensitive': file_info.is_sensitive,
                    'security_level': file_info.security_level,
                    'created_at': file_info.created_at.isoformat(),
                    'exists': os.path.exists(file_path)
                }
                
                if include_details:
                    file_data.update({
                        'file_size': file_info.file_size,
                        'access_count': file_info.access_count,
                        'last_accessed': file_info.last_accessed.isoformat() if file_info.last_accessed else None,
                        'owner_process': file_info.owner_process,
                        'cleanup_verified': file_info.cleanup_verified
                    })
                
                files.append(file_data)
            
            return files
    
    def shutdown(self):
        """Shutdown the temporary file manager and clean up all files."""
        logger.info("Shutting down SecureTempFileManager")
        
        # Signal shutdown to monitoring thread
        self._shutdown_event.set()
        
        # Wait for monitoring thread to finish
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=10)
        
        # Clean up all remaining files
        self.cleanup_all(force=True)
        
        logger.info("SecureTempFileManager shutdown complete")


# Global instance for convenience
_global_temp_manager: Optional[SecureTempFileManager] = None


def get_temp_manager() -> SecureTempFileManager:
    """Get the global temporary file manager instance."""
    global _global_temp_manager
    if _global_temp_manager is None:
        _global_temp_manager = SecureTempFileManager()
    return _global_temp_manager


def create_secure_temp_file(content: Union[str, bytes],
                          suffix: str = "",
                          is_sensitive: bool = True,
                          security_level: str = "confidential") -> str:
    """
    Convenience function to create a secure temporary file.
    
    Args:
        content: Content to write to the file
        suffix: File suffix
        is_sensitive: Whether the file contains sensitive data
        security_level: Security classification
        
    Returns:
        Path to the created temporary file
    """
    return get_temp_manager().create_temp_file(
        content=content,
        suffix=suffix,
        is_sensitive=is_sensitive,
        security_level=security_level
    )


def cleanup_temp_file(file_path: str) -> bool:
    """
    Convenience function to clean up a temporary file.
    
    Args:
        file_path: Path to the file to clean up
        
    Returns:
        True if cleanup was successful, False otherwise
    """
    return get_temp_manager().cleanup_file(file_path)