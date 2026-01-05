"""
Log Sanitization and Cleanup Module

Provides sensitive information sanitization in logs, automatic cleanup of
temporary files with sensitive data, and secure log storage with access controls.
"""

import os
import re
import json
import logging
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Set, Pattern
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


logger = logging.getLogger(__name__)


@dataclass
class SensitivePattern:
    """Represents a pattern for detecting sensitive information"""
    name: str
    pattern: Pattern[str]
    replacement: str
    description: str
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class TemporaryFile:
    """Represents a temporary file that needs cleanup"""
    file_path: str
    created_at: datetime
    contains_sensitive_data: bool
    cleanup_priority: str = "normal"  # low, normal, high, immediate
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        """Get age of temporary file in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def should_cleanup(self) -> bool:
        """Check if file should be cleaned up based on age and priority"""
        if self.cleanup_priority == "immediate":
            return True
        elif self.cleanup_priority == "high":
            return self.age_seconds > 300  # 5 minutes
        elif self.cleanup_priority == "normal":
            return self.age_seconds > 1800  # 30 minutes
        else:  # low priority
            return self.age_seconds > 3600  # 1 hour


class LogSanitizer:
    """Sanitizes sensitive information from deployment logs"""
    
    def __init__(self):
        """Initialize log sanitizer with predefined sensitive patterns"""
        self.sensitive_patterns = self._create_default_patterns()
        self.custom_patterns: List[SensitivePattern] = []
        self.sanitization_stats = {
            "total_logs_processed": 0,
            "sensitive_items_found": 0,
            "patterns_matched": {}
        }
    
    def _create_default_patterns(self) -> List[SensitivePattern]:
        """Create default patterns for detecting sensitive information"""
        patterns = [
            SensitivePattern(
                name="password",
                pattern=re.compile(r'password["\s]*[:=]["\s]*([^\s"\']+)', re.IGNORECASE),
                replacement=r'password="[REDACTED]"',
                description="Password fields in configuration",
                severity="high"
            ),
            SensitivePattern(
                name="api_key",
                pattern=re.compile(r'api[_-]?key["\s]*[:=]["\s]*([^\s"\']+)', re.IGNORECASE),
                replacement=r'api_key="[REDACTED]"',
                description="API keys and tokens",
                severity="high"
            ),
            SensitivePattern(
                name="secret",
                pattern=re.compile(r'secret["\s]*[:=]["\s]*([^\s"\']+)', re.IGNORECASE),
                replacement=r'secret="[REDACTED]"',
                description="Secret values",
                severity="high"
            ),
            SensitivePattern(
                name="token",
                pattern=re.compile(r'token["\s]*[:=]["\s]*([^\s"\']+)', re.IGNORECASE),
                replacement=r'token="[REDACTED]"',
                description="Authentication tokens",
                severity="high"
            ),
            SensitivePattern(
                name="private_key",
                pattern=re.compile(r'-----BEGIN [A-Z\s]+ PRIVATE KEY-----.*?-----END [A-Z\s]+ PRIVATE KEY-----', re.DOTALL),
                replacement='-----BEGIN PRIVATE KEY-----\n[REDACTED]\n-----END PRIVATE KEY-----',
                description="Private keys",
                severity="critical"
            ),
            SensitivePattern(
                name="ssh_key",
                pattern=re.compile(r'ssh-[a-z0-9]+ [A-Za-z0-9+/=]+', re.IGNORECASE),
                replacement='ssh-rsa [REDACTED]',
                description="SSH public keys",
                severity="medium"
            ),
            SensitivePattern(
                name="ip_address",
                pattern=re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
                replacement='[IP_REDACTED]',
                description="IP addresses",
                severity="low"
            ),
            SensitivePattern(
                name="email",
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement='[EMAIL_REDACTED]',
                description="Email addresses",
                severity="low"
            ),
            SensitivePattern(
                name="url_with_credentials",
                pattern=re.compile(r'https?://[^:]+:[^@]+@[^\s]+', re.IGNORECASE),
                replacement='https://[USER]:[PASS]@[HOST]',
                description="URLs with embedded credentials",
                severity="high"
            )
        ]
        return patterns
    
    def add_custom_pattern(self, pattern: SensitivePattern):
        """
        Add a custom sensitive pattern.
        
        Args:
            pattern: Custom sensitive pattern to add
        """
        self.custom_patterns.append(pattern)
        logger.info(f"Added custom sensitive pattern: {pattern.name}")
    
    def sanitize_log_entry(self, log_entry: str) -> str:
        """
        Sanitize a single log entry by removing sensitive information.
        
        Args:
            log_entry: Log entry to sanitize
            
        Returns:
            Sanitized log entry
        """
        sanitized_entry = log_entry
        patterns_found = []
        
        # Apply all patterns (default + custom)
        all_patterns = self.sensitive_patterns + self.custom_patterns
        
        for pattern in all_patterns:
            matches = pattern.pattern.findall(sanitized_entry)
            if matches:
                patterns_found.append(pattern.name)
                sanitized_entry = pattern.pattern.sub(pattern.replacement, sanitized_entry)
                
                # Update statistics
                self.sanitization_stats["sensitive_items_found"] += len(matches)
                pattern_name = pattern.name
                self.sanitization_stats["patterns_matched"][pattern_name] = \
                    self.sanitization_stats["patterns_matched"].get(pattern_name, 0) + len(matches)
        
        # Add sanitization marker if patterns were found
        if patterns_found:
            timestamp = datetime.now().isoformat()
            sanitized_entry += f" [SANITIZED: {','.join(patterns_found)} at {timestamp}]"
        
        self.sanitization_stats["total_logs_processed"] += 1
        return sanitized_entry
    
    def sanitize_log_file(self, log_file_path: str, output_path: Optional[str] = None) -> str:
        """
        Sanitize an entire log file.
        
        Args:
            log_file_path: Path to log file to sanitize
            output_path: Optional output path. If None, overwrites original file.
            
        Returns:
            Path to sanitized log file
        """
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"Log file not found: {log_file_path}")
        
        output_file = output_path or log_file_path
        temp_file = f"{output_file}.sanitizing"
        
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                with open(temp_file, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        sanitized_line = self.sanitize_log_entry(line.rstrip())
                        outfile.write(sanitized_line + '\n')
            
            # Replace original file with sanitized version
            shutil.move(temp_file, output_file)
            logger.info(f"Sanitized log file: {log_file_path}")
            
            return output_file
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_file):
                os.remove(temp_file)
            logger.error(f"Failed to sanitize log file {log_file_path}: {e}")
            raise
    
    def sanitize_json_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize JSON log data.
        
        Args:
            log_data: JSON log data to sanitize
            
        Returns:
            Sanitized JSON log data
        """
        sanitized_data = {}
        
        for key, value in log_data.items():
            if isinstance(value, str):
                sanitized_data[key] = self.sanitize_log_entry(value)
            elif isinstance(value, dict):
                sanitized_data[key] = self.sanitize_json_log(value)
            elif isinstance(value, list):
                sanitized_data[key] = [
                    self.sanitize_log_entry(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized_data[key] = value
        
        return sanitized_data
    
    def get_sanitization_stats(self) -> Dict[str, Any]:
        """Get sanitization statistics"""
        return self.sanitization_stats.copy()


class TemporaryFileManager:
    """Manages temporary files and ensures secure cleanup"""
    
    def __init__(self, base_temp_dir: Optional[str] = None):
        """
        Initialize temporary file manager.
        
        Args:
            base_temp_dir: Base directory for temporary files
        """
        self.base_temp_dir = Path(base_temp_dir) if base_temp_dir else Path(tempfile.gettempdir())
        self.tracked_files: Dict[str, TemporaryFile] = {}
        self.cleanup_stats = {
            "files_created": 0,
            "files_cleaned": 0,
            "sensitive_files_cleaned": 0,
            "cleanup_failures": 0
        }
    
    def create_temporary_file(self, 
                            content: bytes,
                            suffix: str = ".tmp",
                            contains_sensitive_data: bool = False,
                            cleanup_priority: str = "normal") -> str:
        """
        Create a temporary file with tracking.
        
        Args:
            content: File content
            suffix: File suffix
            contains_sensitive_data: Whether file contains sensitive data
            cleanup_priority: Cleanup priority (immediate, high, normal, low)
            
        Returns:
            Path to created temporary file
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            dir=self.base_temp_dir,
            suffix=suffix,
            delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Track the file
        temp_file_obj = TemporaryFile(
            file_path=temp_path,
            created_at=datetime.now(),
            contains_sensitive_data=contains_sensitive_data,
            cleanup_priority=cleanup_priority,
            metadata={
                "size_bytes": len(content),
                "suffix": suffix
            }
        )
        
        self.tracked_files[temp_path] = temp_file_obj
        self.cleanup_stats["files_created"] += 1
        
        logger.info(f"Created temporary file: {temp_path} (sensitive: {contains_sensitive_data})")
        return temp_path
    
    def mark_file_for_cleanup(self, file_path: str, priority: str = "normal"):
        """
        Mark an existing file for cleanup.
        
        Args:
            file_path: Path to file to track
            priority: Cleanup priority
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found for cleanup tracking: {file_path}")
            return
        
        # Detect if file contains sensitive data
        contains_sensitive = self._detect_sensitive_content(file_path)
        
        temp_file_obj = TemporaryFile(
            file_path=file_path,
            created_at=datetime.now(),
            contains_sensitive_data=contains_sensitive,
            cleanup_priority=priority
        )
        
        self.tracked_files[file_path] = temp_file_obj
        logger.info(f"Marked file for cleanup: {file_path} (sensitive: {contains_sensitive})")
    
    def _detect_sensitive_content(self, file_path: str) -> bool:
        """
        Detect if a file contains sensitive content.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file likely contains sensitive data
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # Read first 1KB
                
            content_lower = content.lower()
            sensitive_keywords = [
                'password', 'secret', 'key', 'token', 'credential',
                'private', 'confidential', 'api_key', 'auth'
            ]
            
            return any(keyword in content_lower for keyword in sensitive_keywords)
            
        except Exception as e:
            logger.warning(f"Could not detect sensitive content in {file_path}: {e}")
            return False
    
    def cleanup_files(self, force_all: bool = False) -> Dict[str, int]:
        """
        Clean up temporary files based on their cleanup criteria.
        
        Args:
            force_all: Force cleanup of all tracked files regardless of age
            
        Returns:
            Cleanup statistics
        """
        cleanup_results = {
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "sensitive_cleaned": 0,
            "skipped": 0
        }
        
        files_to_remove = []
        
        for file_path, temp_file in self.tracked_files.items():
            cleanup_results["attempted"] += 1
            
            # Check if file should be cleaned up
            if not force_all and not temp_file.should_cleanup:
                cleanup_results["skipped"] += 1
                continue
            
            try:
                # Secure deletion for sensitive files
                if temp_file.contains_sensitive_data:
                    self._secure_delete_file(file_path)
                    cleanup_results["sensitive_cleaned"] += 1
                else:
                    # Regular deletion for non-sensitive files
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                cleanup_results["successful"] += 1
                files_to_remove.append(file_path)
                
                logger.info(f"Cleaned up temporary file: {file_path}")
                
            except Exception as e:
                cleanup_results["failed"] += 1
                logger.error(f"Failed to cleanup file {file_path}: {e}")
        
        # Remove cleaned files from tracking
        for file_path in files_to_remove:
            del self.tracked_files[file_path]
        
        # Update statistics
        self.cleanup_stats["files_cleaned"] += cleanup_results["successful"]
        self.cleanup_stats["sensitive_files_cleaned"] += cleanup_results["sensitive_cleaned"]
        self.cleanup_stats["cleanup_failures"] += cleanup_results["failed"]
        
        logger.info(f"Cleanup completed: {cleanup_results}")
        return cleanup_results
    
    def _secure_delete_file(self, file_path: str):
        """
        Securely delete a file by overwriting it before deletion.
        
        Args:
            file_path: Path to file to securely delete
        """
        if not os.path.exists(file_path):
            return
        
        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Overwrite with random data multiple times
            with open(file_path, 'r+b') as f:
                for _ in range(3):  # 3 passes of overwriting
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            os.remove(file_path)
            logger.debug(f"Securely deleted file: {file_path}")
            
        except Exception as e:
            logger.error(f"Secure deletion failed for {file_path}: {e}")
            # Fall back to regular deletion
            try:
                os.remove(file_path)
            except:
                pass
    
    def cleanup_by_age(self, max_age_hours: int = 24):
        """
        Clean up files older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_files = [
            path for path, temp_file in self.tracked_files.items()
            if temp_file.created_at < cutoff_time
        ]
        
        for file_path in old_files:
            try:
                temp_file = self.tracked_files[file_path]
                if temp_file.contains_sensitive_data:
                    self._secure_delete_file(file_path)
                else:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                del self.tracked_files[file_path]
                logger.info(f"Cleaned up old file: {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to cleanup old file {file_path}: {e}")
    
    def get_tracked_files(self) -> Dict[str, TemporaryFile]:
        """Get all currently tracked files"""
        return self.tracked_files.copy()
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics"""
        return self.cleanup_stats.copy()


class SecureLogStorage:
    """Manages secure storage and access control for deployment logs"""
    
    def __init__(self, log_dir: str, sanitizer: LogSanitizer):
        """
        Initialize secure log storage.
        
        Args:
            log_dir: Directory for storing logs
            sanitizer: Log sanitizer instance
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.sanitizer = sanitizer
        
        # Create secure subdirectories
        self.secure_log_dir = self.log_dir / "secure"
        self.sanitized_log_dir = self.log_dir / "sanitized"
        self.secure_log_dir.mkdir(exist_ok=True)
        self.sanitized_log_dir.mkdir(exist_ok=True)
        
        # Set restrictive permissions on secure directory
        os.chmod(self.secure_log_dir, 0o700)  # Owner only
    
    def store_log_entry(self, 
                       deployment_id: str, 
                       log_entry: Dict[str, Any],
                       sanitize: bool = True) -> str:
        """
        Store a log entry with optional sanitization.
        
        Args:
            deployment_id: Deployment identifier
            log_entry: Log entry data
            sanitize: Whether to sanitize the log entry
            
        Returns:
            Path to stored log file
        """
        # Determine storage location based on sanitization
        if sanitize:
            log_file = self.sanitized_log_dir / f"{deployment_id}.log"
            # Sanitize the log entry
            sanitized_entry = self.sanitizer.sanitize_json_log(log_entry)
        else:
            log_file = self.secure_log_dir / f"{deployment_id}.log"
            sanitized_entry = log_entry
        
        # Append to log file
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(sanitized_entry) + "\n")
        
        # Set appropriate permissions
        if sanitize:
            os.chmod(log_file, 0o644)  # Readable by group
        else:
            os.chmod(log_file, 0o600)  # Owner only
        
        return str(log_file)
    
    def get_log_entries(self, 
                       deployment_id: str, 
                       sanitized_only: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve log entries for a deployment.
        
        Args:
            deployment_id: Deployment identifier
            sanitized_only: Whether to return only sanitized logs
            
        Returns:
            List of log entries
        """
        log_dir = self.sanitized_log_dir if sanitized_only else self.secure_log_dir
        log_file = log_dir / f"{deployment_id}.log"
        
        if not log_file.exists():
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read log file {log_file}: {e}")
        
        return entries
    
    def cleanup_old_logs(self, max_age_days: int = 30):
        """
        Clean up old log files.
        
        Args:
            max_age_days: Maximum age in days before cleanup
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        for log_dir in [self.secure_log_dir, self.sanitized_log_dir]:
            for log_file in log_dir.glob("*.log"):
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        log_file.unlink()
                        logger.info(f"Cleaned up old log file: {log_file}")
                except Exception as e:
                    logger.error(f"Failed to cleanup old log {log_file}: {e}")


class DeploymentCleanupManager:
    """Manages cleanup of deployment-related temporary files and resources"""
    
    def __init__(self, 
                 log_sanitizer: LogSanitizer,
                 temp_file_manager: TemporaryFileManager,
                 secure_log_storage: SecureLogStorage):
        """
        Initialize deployment cleanup manager.
        
        Args:
            log_sanitizer: Log sanitizer instance
            temp_file_manager: Temporary file manager instance
            secure_log_storage: Secure log storage instance
        """
        self.log_sanitizer = log_sanitizer
        self.temp_file_manager = temp_file_manager
        self.secure_log_storage = secure_log_storage
    
    async def cleanup_deployment_resources(self, deployment_id: str):
        """
        Clean up all resources associated with a deployment.
        
        Args:
            deployment_id: Deployment identifier
        """
        logger.info(f"Cleaning up resources for deployment {deployment_id}")
        
        try:
            # Clean up temporary files
            temp_cleanup_results = self.temp_file_manager.cleanup_files()
            
            # Clean up old logs
            self.secure_log_storage.cleanup_old_logs()
            
            logger.info(f"Cleanup completed for deployment {deployment_id}: {temp_cleanup_results}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup resources for deployment {deployment_id}: {e}")
    
    async def emergency_cleanup(self):
        """Perform emergency cleanup of all sensitive resources"""
        logger.warning("Performing emergency cleanup of sensitive resources")
        
        try:
            # Force cleanup of all temporary files
            self.temp_file_manager.cleanup_files(force_all=True)
            
            # Clean up very old logs
            self.secure_log_storage.cleanup_old_logs(max_age_days=1)
            
            logger.info("Emergency cleanup completed")
            
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")
    
    def get_cleanup_status(self) -> Dict[str, Any]:
        """Get comprehensive cleanup status"""
        return {
            "sanitization_stats": self.log_sanitizer.get_sanitization_stats(),
            "temp_file_stats": self.temp_file_manager.get_cleanup_stats(),
            "tracked_files": len(self.temp_file_manager.get_tracked_files())
        }