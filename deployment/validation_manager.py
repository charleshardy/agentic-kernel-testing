"""
Validation Manager for Test Deployment System

Provides comprehensive validation failure handling, diagnostic information,
and recovery mechanisms for deployment readiness validation.
"""

import asyncio
import logging
import os
import socket
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .models import ValidationResult
from .readiness_manager import ReadinessManager


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation failures"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationCheck:
    """Represents a single validation check"""
    name: str
    description: str
    severity: ValidationSeverity
    required: bool = True
    timeout_seconds: int = 30
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class ValidationFailure:
    """Detailed information about a validation failure"""
    check_name: str
    error_message: str
    severity: ValidationSeverity
    diagnostic_info: Dict[str, Any] = field(default_factory=dict)
    remediation_suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    is_recoverable: bool = True


class ValidationManager:
    """Manages comprehensive validation checks and failure handling"""
    
    def __init__(self):
        """Initialize validation manager"""
        self.validation_checks = self._create_default_checks()
        self.custom_checks: List[ValidationCheck] = []
        self.validation_history: Dict[str, List[ValidationResult]] = {}
        self.failure_recovery_strategies: Dict[str, callable] = {}
        
        # Initialize readiness manager
        self.readiness_manager = ReadinessManager()
        
        # Register default recovery strategies
        self._register_recovery_strategies()
    
    def _create_default_checks(self) -> List[ValidationCheck]:
        """Create default validation checks"""
        return [
            ValidationCheck(
                name="network_connectivity",
                description="Verify network connectivity to required services",
                severity=ValidationSeverity.ERROR,
                required=True,
                timeout_seconds=10
            ),
            ValidationCheck(
                name="disk_space",
                description="Check available disk space for deployment",
                severity=ValidationSeverity.ERROR,
                required=True,
                timeout_seconds=5
            ),
            ValidationCheck(
                name="memory_availability",
                description="Verify sufficient memory for test execution",
                severity=ValidationSeverity.WARNING,
                required=False,
                timeout_seconds=5
            ),
            ValidationCheck(
                name="cpu_availability",
                description="Check CPU resources for test execution",
                severity=ValidationSeverity.WARNING,
                required=False,
                timeout_seconds=5
            ),
            ValidationCheck(
                name="tool_functionality",
                description="Validate required testing tools are functional",
                severity=ValidationSeverity.ERROR,
                required=True,
                timeout_seconds=30
            ),
            ValidationCheck(
                name="environment_permissions",
                description="Verify deployment permissions and access rights",
                severity=ValidationSeverity.ERROR,
                required=True,
                timeout_seconds=10
            ),
            ValidationCheck(
                name="kernel_compatibility",
                description="Check kernel version and configuration compatibility",
                severity=ValidationSeverity.ERROR,
                required=True,
                timeout_seconds=15
            )
        ]
    
    def _register_recovery_strategies(self):
        """Register recovery strategies for common validation failures"""
        self.failure_recovery_strategies = {
            "network_connectivity": self._recover_network_connectivity,
            "disk_space": self._recover_disk_space,
            "memory_availability": self._recover_memory_availability,
            "tool_functionality": self._recover_tool_functionality,
            "environment_permissions": self._recover_environment_permissions
        }
    
    async def validate_environment_readiness(self, 
                                           environment_id: str,
                                           deployment_config: Dict[str, Any] = None) -> ValidationResult:
        """
        Perform comprehensive environment readiness validation.
        
        Args:
            environment_id: Environment identifier
            deployment_config: Optional deployment configuration
            
        Returns:
            ValidationResult with detailed validation information
        """
        logger.info(f"Starting comprehensive validation for environment {environment_id}")
        
        validation_result = ValidationResult(
            environment_id=environment_id,
            is_ready=True,
            checks_performed=[],
            failed_checks=[],
            warnings=[],
            details={},
            timestamp=datetime.now()
        )
        
        # Combine default and custom checks
        all_checks = self.validation_checks + self.custom_checks
        
        # Execute validation checks
        for check in all_checks:
            try:
                logger.debug(f"Executing validation check: {check.name}")
                validation_result.checks_performed.append(check.name)
                
                # Execute the check with timeout
                check_result = await asyncio.wait_for(
                    self._execute_validation_check(check, environment_id, deployment_config),
                    timeout=check.timeout_seconds
                )
                
                # Process check result
                if not check_result["success"]:
                    validation_result.failed_checks.append(check.name)
                    
                    # Create detailed failure information
                    failure = ValidationFailure(
                        check_name=check.name,
                        error_message=check_result.get("error", "Unknown validation error"),
                        severity=check.severity,
                        diagnostic_info=check_result.get("diagnostic_info", {}),
                        remediation_suggestions=check_result.get("remediation_suggestions", []),
                        is_recoverable=check_result.get("is_recoverable", True)
                    )
                    
                    # Store failure details
                    validation_result.details[f"{check.name}_failure"] = failure
                    
                    # Mark as not ready if it's a required check
                    if check.required and check.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                        validation_result.is_ready = False
                    
                    # Add warnings for non-critical failures
                    if check.severity == ValidationSeverity.WARNING:
                        validation_result.warnings.append(f"{check.name}: {failure.error_message}")
                
                else:
                    # Store successful check details
                    validation_result.details[f"{check.name}_success"] = check_result.get("details", {})
                
            except asyncio.TimeoutError:
                logger.error(f"Validation check {check.name} timed out after {check.timeout_seconds}s")
                validation_result.failed_checks.append(check.name)
                validation_result.is_ready = False
                
                failure = ValidationFailure(
                    check_name=check.name,
                    error_message=f"Validation check timed out after {check.timeout_seconds} seconds",
                    severity=ValidationSeverity.ERROR,
                    diagnostic_info={"timeout_seconds": check.timeout_seconds},
                    remediation_suggestions=["Increase timeout value", "Check system performance"],
                    is_recoverable=True
                )
                validation_result.details[f"{check.name}_failure"] = failure
                
            except Exception as e:
                logger.error(f"Validation check {check.name} failed with exception: {e}")
                validation_result.failed_checks.append(check.name)
                validation_result.is_ready = False
                
                failure = ValidationFailure(
                    check_name=check.name,
                    error_message=f"Validation check failed: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    diagnostic_info={"exception": str(e), "exception_type": type(e).__name__},
                    remediation_suggestions=["Check system logs", "Verify environment configuration"],
                    is_recoverable=False
                )
                validation_result.details[f"{check.name}_failure"] = failure
        
        # Store validation history
        if environment_id not in self.validation_history:
            self.validation_history[environment_id] = []
        self.validation_history[environment_id].append(validation_result)
        
        # Keep only last 10 validation results per environment
        if len(self.validation_history[environment_id]) > 10:
            self.validation_history[environment_id] = self.validation_history[environment_id][-10:]
        
        logger.info(f"Validation completed for {environment_id}: ready={validation_result.is_ready}, "
                   f"success_rate={validation_result.success_rate:.1f}%")
        
        # Update environment readiness state
        await self.readiness_manager.update_environment_readiness(
            environment_id, validation_result
        )
        
        return validation_result
    
    async def _execute_validation_check(self, 
                                      check: ValidationCheck,
                                      environment_id: str,
                                      deployment_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific validation check"""
        
        if check.name == "network_connectivity":
            return await self._check_network_connectivity(environment_id, deployment_config)
        elif check.name == "disk_space":
            return await self._check_disk_space(environment_id, deployment_config)
        elif check.name == "memory_availability":
            return await self._check_memory_availability(environment_id, deployment_config)
        elif check.name == "cpu_availability":
            return await self._check_cpu_availability(environment_id, deployment_config)
        elif check.name == "tool_functionality":
            return await self._check_tool_functionality(environment_id, deployment_config)
        elif check.name == "environment_permissions":
            return await self._check_environment_permissions(environment_id, deployment_config)
        elif check.name == "kernel_compatibility":
            return await self._check_kernel_compatibility(environment_id, deployment_config)
        else:
            return {
                "success": False,
                "error": f"Unknown validation check: {check.name}",
                "is_recoverable": False
            }
    
    async def _check_network_connectivity(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check comprehensive network connectivity"""
        try:
            # Test connectivity to multiple services and protocols
            test_hosts = [
                ("8.8.8.8", 53, "tcp", "Google DNS TCP"),
                ("8.8.8.8", 53, "udp", "Google DNS UDP"),
                ("1.1.1.1", 53, "tcp", "Cloudflare DNS TCP"),
                ("1.1.1.1", 53, "udp", "Cloudflare DNS UDP"),
                ("github.com", 443, "tcp", "GitHub HTTPS"),
                ("pypi.org", 443, "tcp", "PyPI HTTPS"),
            ]
            
            # Add custom hosts from config if provided
            if config and "test_hosts" in config:
                for host_config in config["test_hosts"]:
                    test_hosts.append((
                        host_config["host"],
                        host_config["port"],
                        host_config.get("protocol", "tcp"),
                        host_config.get("description", f"{host_config['host']}:{host_config['port']}")
                    ))
            
            connectivity_results = []
            dns_resolution_results = []
            
            # Test DNS resolution
            dns_test_domains = ["google.com", "github.com", "pypi.org"]
            for domain in dns_test_domains:
                try:
                    import socket
                    start_time = datetime.now()
                    addr_info = socket.getaddrinfo(domain, None)
                    resolution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    dns_resolution_results.append({
                        "domain": domain,
                        "resolved": True,
                        "addresses": [info[4][0] for info in addr_info[:3]],  # First 3 addresses
                        "resolution_time_ms": resolution_time
                    })
                except Exception as e:
                    dns_resolution_results.append({
                        "domain": domain,
                        "resolved": False,
                        "error": str(e)
                    })
            
            # Test network connectivity
            for host, port, protocol, description in test_hosts:
                try:
                    start_time = datetime.now()
                    
                    if protocol.lower() == "tcp":
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(5)
                        result = sock.connect_ex((host, port))
                        sock.close()
                        connected = result == 0
                    elif protocol.lower() == "udp":
                        # For UDP, we'll try to send a simple packet
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.settimeout(5)
                        try:
                            sock.sendto(b"test", (host, port))
                            connected = True
                        except Exception:
                            connected = False
                        finally:
                            sock.close()
                    else:
                        connected = False
                    
                    connection_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    connectivity_results.append({
                        "host": host,
                        "port": port,
                        "protocol": protocol,
                        "description": description,
                        "connected": connected,
                        "connection_time_ms": connection_time if connected else None
                    })
                except Exception as e:
                    connectivity_results.append({
                        "host": host,
                        "port": port,
                        "protocol": protocol,
                        "description": description,
                        "connected": False,
                        "error": str(e)
                    })
            
            # Analyze results
            successful_connections = [r for r in connectivity_results if r["connected"]]
            successful_dns_resolutions = [r for r in dns_resolution_results if r["resolved"]]
            
            # Check network interface information
            network_interfaces = []
            try:
                if PSUTIL_AVAILABLE:
                    for interface, addrs in psutil.net_if_addrs().items():
                        interface_info = {
                            "name": interface,
                            "addresses": []
                        }
                        for addr in addrs:
                            if addr.family == socket.AF_INET:  # IPv4
                                interface_info["addresses"].append({
                                    "type": "IPv4",
                                    "address": addr.address,
                                    "netmask": addr.netmask
                                })
                            elif addr.family == socket.AF_INET6:  # IPv6
                                interface_info["addresses"].append({
                                    "type": "IPv6",
                                    "address": addr.address
                                })
                        if interface_info["addresses"]:
                            network_interfaces.append(interface_info)
            except Exception as e:
                logger.warning(f"Could not get network interface information: {e}")
            
            # Determine overall success
            dns_success_rate = len(successful_dns_resolutions) / len(dns_resolution_results) if dns_resolution_results else 0
            connectivity_success_rate = len(successful_connections) / len(connectivity_results) if connectivity_results else 0
            
            # Require at least 50% success rate for both DNS and connectivity
            overall_success = dns_success_rate >= 0.5 and connectivity_success_rate >= 0.5
            
            if overall_success:
                return {
                    "success": True,
                    "details": {
                        "connectivity_results": connectivity_results,
                        "dns_resolution_results": dns_resolution_results,
                        "network_interfaces": network_interfaces,
                        "successful_connections": len(successful_connections),
                        "total_connections_tested": len(connectivity_results),
                        "connectivity_success_rate": connectivity_success_rate,
                        "dns_success_rate": dns_success_rate
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Network connectivity insufficient: {connectivity_success_rate:.1%} connectivity, {dns_success_rate:.1%} DNS resolution",
                    "diagnostic_info": {
                        "connectivity_results": connectivity_results,
                        "dns_resolution_results": dns_resolution_results,
                        "network_interfaces": network_interfaces,
                        "connectivity_success_rate": connectivity_success_rate,
                        "dns_success_rate": dns_success_rate
                    },
                    "remediation_suggestions": [
                        "Check network configuration",
                        "Verify firewall settings",
                        "Test DNS resolution",
                        "Check network interface status",
                        "Verify routing configuration"
                    ],
                    "is_recoverable": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Network connectivity check failed: {e}",
                "diagnostic_info": {"exception": str(e)},
                "remediation_suggestions": ["Check network interface status"],
                "is_recoverable": True
            }
    
    async def _check_disk_space(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check available disk space across multiple mount points"""
        try:
            if not PSUTIL_AVAILABLE:
                return {
                    "success": True,
                    "warning": "psutil not available, disk space check skipped",
                    "details": {"psutil_available": False}
                }
            
            # Get disk usage for all mount points
            disk_usage_results = []
            overall_critical = False
            overall_warning = False
            
            # Define thresholds
            critical_threshold = 95  # 95% used
            warning_threshold = 85   # 85% used
            min_free_gb = 1.0       # Minimum 1GB free
            
            # Check specific paths if provided in config
            paths_to_check = ['/']  # Always check root
            if config and "disk_paths" in config:
                paths_to_check.extend(config["disk_paths"])
            
            # Also check common deployment paths
            common_paths = ['/tmp', '/var', '/home']
            for path in common_paths:
                if os.path.exists(path) and path not in paths_to_check:
                    paths_to_check.append(path)
            
            for path in paths_to_check:
                try:
                    if not os.path.exists(path):
                        continue
                        
                    disk_usage = psutil.disk_usage(path)
                    
                    # Calculate percentages
                    used_percent = (disk_usage.used / disk_usage.total) * 100
                    free_gb = disk_usage.free / (1024**3)  # Convert to GB
                    total_gb = disk_usage.total / (1024**3)
                    used_gb = disk_usage.used / (1024**3)
                    
                    # Determine status
                    is_critical = used_percent >= critical_threshold or free_gb < min_free_gb
                    is_warning = used_percent >= warning_threshold
                    
                    if is_critical:
                        overall_critical = True
                    elif is_warning:
                        overall_warning = True
                    
                    disk_usage_results.append({
                        "path": path,
                        "total_gb": round(total_gb, 2),
                        "used_gb": round(used_gb, 2),
                        "free_gb": round(free_gb, 2),
                        "used_percent": round(used_percent, 1),
                        "status": "critical" if is_critical else ("warning" if is_warning else "ok"),
                        "is_critical": is_critical,
                        "is_warning": is_warning
                    })
                    
                except Exception as e:
                    disk_usage_results.append({
                        "path": path,
                        "error": str(e),
                        "status": "error"
                    })
            
            # Check for additional disk information
            disk_io_counters = None
            try:
                disk_io_counters = psutil.disk_io_counters()
                if disk_io_counters:
                    disk_io_info = {
                        "read_count": disk_io_counters.read_count,
                        "write_count": disk_io_counters.write_count,
                        "read_bytes": disk_io_counters.read_bytes,
                        "write_bytes": disk_io_counters.write_bytes,
                        "read_time": disk_io_counters.read_time,
                        "write_time": disk_io_counters.write_time
                    }
                else:
                    disk_io_info = {"available": False}
            except Exception as e:
                disk_io_info = {"error": str(e)}
            
            if overall_critical:
                critical_paths = [r for r in disk_usage_results if r.get("is_critical", False)]
                return {
                    "success": False,
                    "error": f"Critical disk space issues on {len(critical_paths)} path(s)",
                    "diagnostic_info": {
                        "disk_usage_results": disk_usage_results,
                        "disk_io_info": disk_io_info,
                        "critical_paths": [r["path"] for r in critical_paths],
                        "thresholds": {
                            "critical_percent": critical_threshold,
                            "warning_percent": warning_threshold,
                            "min_free_gb": min_free_gb
                        }
                    },
                    "remediation_suggestions": [
                        "Clean up temporary files",
                        "Remove old log files",
                        "Increase disk space allocation",
                        "Move large files to other locations",
                        "Check for large files consuming space"
                    ],
                    "is_recoverable": True
                }
            elif overall_warning:
                warning_paths = [r for r in disk_usage_results if r.get("is_warning", False)]
                return {
                    "success": True,
                    "warning": f"Disk space warnings on {len(warning_paths)} path(s)",
                    "details": {
                        "disk_usage_results": disk_usage_results,
                        "disk_io_info": disk_io_info,
                        "warning_paths": [r["path"] for r in warning_paths],
                        "thresholds": {
                            "critical_percent": critical_threshold,
                            "warning_percent": warning_threshold,
                            "min_free_gb": min_free_gb
                        }
                    }
                }
            else:
                return {
                    "success": True,
                    "details": {
                        "disk_usage_results": disk_usage_results,
                        "disk_io_info": disk_io_info,
                        "thresholds": {
                            "critical_percent": critical_threshold,
                            "warning_percent": warning_threshold,
                            "min_free_gb": min_free_gb
                        }
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Disk space check failed: {e}",
                "diagnostic_info": {"exception": str(e)},
                "remediation_suggestions": ["Check filesystem permissions"],
                "is_recoverable": False
            }
    
    async def _check_memory_availability(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check available memory"""
        try:
            if not PSUTIL_AVAILABLE:
                return {
                    "success": True,
                    "warning": "psutil not available, memory check skipped",
                    "details": {"psutil_available": False}
                }
            
            memory = psutil.virtual_memory()
            
            # Calculate percentages and GB
            used_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            # Define thresholds
            critical_threshold = 95  # 95% used
            warning_threshold = 85   # 85% used
            min_available_gb = 0.5   # Minimum 500MB available
            
            if used_percent >= critical_threshold or available_gb < min_available_gb:
                return {
                    "success": False,
                    "error": f"Insufficient memory: {used_percent:.1f}% used, {available_gb:.1f}GB available",
                    "diagnostic_info": {
                        "total_gb": memory.total / (1024**3),
                        "used_gb": memory.used / (1024**3),
                        "available_gb": available_gb,
                        "used_percent": used_percent
                    },
                    "remediation_suggestions": [
                        "Close unnecessary applications",
                        "Increase memory allocation",
                        "Check for memory leaks"
                    ],
                    "is_recoverable": True
                }
            elif used_percent >= warning_threshold:
                return {
                    "success": True,
                    "warning": f"Memory usage warning: {used_percent:.1f}% used",
                    "details": {
                        "total_gb": memory.total / (1024**3),
                        "used_gb": memory.used / (1024**3),
                        "available_gb": available_gb,
                        "used_percent": used_percent
                    }
                }
            else:
                return {
                    "success": True,
                    "details": {
                        "total_gb": memory.total / (1024**3),
                        "used_gb": memory.used / (1024**3),
                        "available_gb": available_gb,
                        "used_percent": used_percent
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Memory check failed: {e}",
                "diagnostic_info": {"exception": str(e)},
                "remediation_suggestions": ["Check system memory status"],
                "is_recoverable": False
            }
    
    async def _check_cpu_availability(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check CPU availability"""
        try:
            if not PSUTIL_AVAILABLE:
                return {
                    "success": True,
                    "warning": "psutil not available, CPU check skipped",
                    "details": {"psutil_available": False}
                }
            
            # Get CPU usage over a short period
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            # Define thresholds
            critical_threshold = 95  # 95% CPU usage
            warning_threshold = 85   # 85% CPU usage
            
            if cpu_percent >= critical_threshold:
                return {
                    "success": False,
                    "error": f"High CPU usage: {cpu_percent:.1f}%",
                    "diagnostic_info": {
                        "cpu_percent": cpu_percent,
                        "cpu_count": cpu_count,
                        "load_avg_1min": load_avg[0],
                        "load_avg_5min": load_avg[1],
                        "load_avg_15min": load_avg[2]
                    },
                    "remediation_suggestions": [
                        "Check for high CPU processes",
                        "Reduce concurrent operations",
                        "Increase CPU allocation"
                    ],
                    "is_recoverable": True
                }
            elif cpu_percent >= warning_threshold:
                return {
                    "success": True,
                    "warning": f"High CPU usage: {cpu_percent:.1f}%",
                    "details": {
                        "cpu_percent": cpu_percent,
                        "cpu_count": cpu_count,
                        "load_avg_1min": load_avg[0]
                    }
                }
            else:
                return {
                    "success": True,
                    "details": {
                        "cpu_percent": cpu_percent,
                        "cpu_count": cpu_count,
                        "load_avg_1min": load_avg[0]
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"CPU check failed: {e}",
                "diagnostic_info": {"exception": str(e)},
                "remediation_suggestions": ["Check system CPU status"],
                "is_recoverable": False
            }
    
    async def _check_tool_functionality(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check functionality of required testing tools comprehensively"""
        try:
            # Define comprehensive tool set
            tools_to_check = [
                # Core Python tools
                {"name": "python3", "command": ["python3", "--version"], "required": True, "category": "python"},
                {"name": "pip", "command": ["python3", "-m", "pip", "--version"], "required": True, "category": "python"},
                {"name": "pytest", "command": ["python3", "-m", "pytest", "--version"], "required": True, "category": "testing"},
                
                # Version control
                {"name": "git", "command": ["git", "--version"], "required": False, "category": "vcs"},
                
                # System tools
                {"name": "ssh", "command": ["ssh", "-V"], "required": False, "category": "system"},
                {"name": "curl", "command": ["curl", "--version"], "required": False, "category": "network"},
                {"name": "wget", "command": ["wget", "--version"], "required": False, "category": "network"},
                
                # Kernel development tools (if available)
                {"name": "gcc", "command": ["gcc", "--version"], "required": False, "category": "development"},
                {"name": "make", "command": ["make", "--version"], "required": False, "category": "development"},
                
                # Performance and debugging tools
                {"name": "perf", "command": ["perf", "--version"], "required": False, "category": "performance"},
                {"name": "gdb", "command": ["gdb", "--version"], "required": False, "category": "debugging"},
                
                # Container tools (if available)
                {"name": "docker", "command": ["docker", "--version"], "required": False, "category": "container"},
            ]
            
            # Add custom tools from config if provided
            if config and "additional_tools" in config:
                for tool_config in config["additional_tools"]:
                    tools_to_check.append({
                        "name": tool_config["name"],
                        "command": tool_config["command"],
                        "required": tool_config.get("required", False),
                        "category": tool_config.get("category", "custom")
                    })
            
            tool_results = []
            category_results = {}
            all_required_available = True
            
            for tool in tools_to_check:
                try:
                    # Run tool version check with timeout
                    start_time = datetime.now()
                    result = subprocess.run(
                        tool["command"],
                        capture_output=True,
                        text=True,
                        timeout=15  # Increased timeout for some tools
                    )
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    if result.returncode == 0:
                        # Extract version information
                        version_output = result.stdout.strip() or result.stderr.strip()
                        version_lines = version_output.split('\n')
                        version_info = version_lines[0] if version_lines else "Unknown version"
                        
                        tool_result = {
                            "name": tool["name"],
                            "available": True,
                            "version": version_info,
                            "full_output": version_output,
                            "required": tool["required"],
                            "category": tool["category"],
                            "execution_time_ms": execution_time
                        }
                        
                        # Additional functionality tests for critical tools
                        if tool["name"] == "python3":
                            # Test Python module imports
                            try:
                                import_test = subprocess.run(
                                    ["python3", "-c", "import sys, os, json, subprocess; print('Core modules OK')"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                tool_result["module_test"] = {
                                    "success": import_test.returncode == 0,
                                    "output": import_test.stdout.strip()
                                }
                            except Exception as e:
                                tool_result["module_test"] = {
                                    "success": False,
                                    "error": str(e)
                                }
                        
                        elif tool["name"] == "git":
                            # Test git configuration
                            try:
                                git_config_test = subprocess.run(
                                    ["git", "config", "--list"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                tool_result["config_test"] = {
                                    "success": git_config_test.returncode == 0,
                                    "has_user_config": "user.name" in git_config_test.stdout
                                }
                            except Exception as e:
                                tool_result["config_test"] = {
                                    "success": False,
                                    "error": str(e)
                                }
                        
                        tool_results.append(tool_result)
                    else:
                        tool_results.append({
                            "name": tool["name"],
                            "available": False,
                            "error": result.stderr.strip() or "Command failed",
                            "return_code": result.returncode,
                            "required": tool["required"],
                            "category": tool["category"],
                            "execution_time_ms": execution_time
                        })
                        
                        if tool["required"]:
                            all_required_available = False
                            
                except subprocess.TimeoutExpired:
                    tool_results.append({
                        "name": tool["name"],
                        "available": False,
                        "error": "Command timed out",
                        "required": tool["required"],
                        "category": tool["category"]
                    })
                    
                    if tool["required"]:
                        all_required_available = False
                        
                except Exception as e:
                    tool_results.append({
                        "name": tool["name"],
                        "available": False,
                        "error": str(e),
                        "required": tool["required"],
                        "category": tool["category"]
                    })
                    
                    if tool["required"]:
                        all_required_available = False
            
            # Organize results by category
            for result in tool_results:
                category = result["category"]
                if category not in category_results:
                    category_results[category] = {
                        "available": [],
                        "unavailable": [],
                        "required_missing": []
                    }
                
                if result["available"]:
                    category_results[category]["available"].append(result["name"])
                else:
                    category_results[category]["unavailable"].append(result["name"])
                    if result["required"]:
                        category_results[category]["required_missing"].append(result["name"])
            
            # Calculate statistics
            total_tools = len(tool_results)
            available_tools = len([r for r in tool_results if r["available"]])
            required_tools = len([r for r in tool_results if r["required"]])
            available_required = len([r for r in tool_results if r["required"] and r["available"]])
            
            availability_rate = (available_tools / total_tools) * 100 if total_tools > 0 else 0
            required_availability_rate = (available_required / required_tools) * 100 if required_tools > 0 else 100
            
            if all_required_available:
                return {
                    "success": True,
                    "details": {
                        "tool_results": tool_results,
                        "category_results": category_results,
                        "statistics": {
                            "total_tools": total_tools,
                            "available_tools": available_tools,
                            "required_tools": required_tools,
                            "available_required": available_required,
                            "availability_rate": availability_rate,
                            "required_availability_rate": required_availability_rate
                        }
                    }
                }
            else:
                failed_required_tools = [
                    t["name"] for t in tool_results 
                    if t["required"] and not t["available"]
                ]
                
                return {
                    "success": False,
                    "error": f"Required tools not available: {', '.join(failed_required_tools)}",
                    "diagnostic_info": {
                        "tool_results": tool_results,
                        "category_results": category_results,
                        "failed_required_tools": failed_required_tools,
                        "statistics": {
                            "total_tools": total_tools,
                            "available_tools": available_tools,
                            "required_tools": required_tools,
                            "available_required": available_required,
                            "availability_rate": availability_rate,
                            "required_availability_rate": required_availability_rate
                        }
                    },
                    "remediation_suggestions": [
                        "Install missing required tools",
                        "Check PATH environment variable",
                        "Verify tool permissions",
                        "Update package manager repositories",
                        f"Install tools by category: {', '.join(set(r['category'] for r in tool_results if r['required'] and not r['available']))}"
                    ],
                    "is_recoverable": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool functionality check failed: {e}",
                "diagnostic_info": {"exception": str(e)},
                "remediation_suggestions": ["Check tool installation"],
                "is_recoverable": True
            }
    
    async def _check_environment_permissions(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check environment permissions and access rights"""
        try:
            import os
            import tempfile
            
            permission_checks = []
            
            # Check write permissions in temp directory
            try:
                with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                    tmp_file.write(b"test")
                    tmp_file.flush()
                permission_checks.append({
                    "check": "temp_directory_write",
                    "success": True,
                    "path": tempfile.gettempdir()
                })
            except Exception as e:
                permission_checks.append({
                    "check": "temp_directory_write",
                    "success": False,
                    "error": str(e),
                    "path": tempfile.gettempdir()
                })
            
            # Check current directory permissions
            try:
                current_dir = os.getcwd()
                test_file = os.path.join(current_dir, ".deployment_test")
                
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                
                permission_checks.append({
                    "check": "current_directory_write",
                    "success": True,
                    "path": current_dir
                })
            except Exception as e:
                permission_checks.append({
                    "check": "current_directory_write",
                    "success": False,
                    "error": str(e),
                    "path": current_dir
                })
            
            # Check if all permission checks passed
            failed_checks = [c for c in permission_checks if not c["success"]]
            
            if not failed_checks:
                return {
                    "success": True,
                    "details": {"permission_checks": permission_checks}
                }
            else:
                return {
                    "success": False,
                    "error": f"Permission checks failed: {len(failed_checks)} of {len(permission_checks)}",
                    "diagnostic_info": {"permission_checks": permission_checks},
                    "remediation_suggestions": [
                        "Check file system permissions",
                        "Verify user access rights",
                        "Check directory ownership"
                    ],
                    "is_recoverable": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Permission check failed: {e}",
                "diagnostic_info": {"exception": str(e)},
                "remediation_suggestions": ["Check system permissions"],
                "is_recoverable": False
            }
    
    async def _check_kernel_compatibility(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check kernel version and configuration compatibility"""
        try:
            import platform
            
            # Get kernel information
            kernel_version = platform.release()
            system_info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
            
            # Define minimum kernel requirements (example)
            min_kernel_version = "3.10"  # Minimum supported kernel version
            
            # Simple version comparison (for demonstration)
            try:
                current_version_parts = kernel_version.split('.')[:2]
                current_major = int(current_version_parts[0])
                current_minor = int(current_version_parts[1]) if len(current_version_parts) > 1 else 0
                
                min_version_parts = min_kernel_version.split('.')
                min_major = int(min_version_parts[0])
                min_minor = int(min_version_parts[1]) if len(min_version_parts) > 1 else 0
                
                is_compatible = (current_major > min_major) or \
                               (current_major == min_major and current_minor >= min_minor)
                
                if is_compatible:
                    return {
                        "success": True,
                        "details": {
                            "system_info": system_info,
                            "kernel_version": kernel_version,
                            "min_required": min_kernel_version,
                            "compatible": True
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Kernel version {kernel_version} is below minimum required {min_kernel_version}",
                        "diagnostic_info": {
                            "system_info": system_info,
                            "kernel_version": kernel_version,
                            "min_required": min_kernel_version
                        },
                        "remediation_suggestions": [
                            "Update kernel to supported version",
                            "Check kernel configuration",
                            "Verify system compatibility"
                        ],
                        "is_recoverable": False
                    }
                    
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Unable to parse kernel version: {kernel_version}",
                    "diagnostic_info": {
                        "system_info": system_info,
                        "parse_error": str(e)
                    },
                    "remediation_suggestions": ["Check kernel version format"],
                    "is_recoverable": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Kernel compatibility check failed: {e}",
                "diagnostic_info": {"exception": str(e)},
                "remediation_suggestions": ["Check system information"],
                "is_recoverable": False
            }
    
    async def attempt_failure_recovery(self, 
                                     environment_id: str, 
                                     validation_result: ValidationResult) -> ValidationResult:
        """
        Attempt to recover from validation failures.
        
        Args:
            environment_id: Environment identifier
            validation_result: Failed validation result
            
        Returns:
            Updated validation result after recovery attempts
        """
        if not validation_result.has_failures:
            return validation_result
        
        logger.info(f"Attempting recovery for {len(validation_result.failed_checks)} failed checks")
        
        recovery_results = {}
        
        for failed_check in validation_result.failed_checks:
            if failed_check in self.failure_recovery_strategies:
                try:
                    logger.info(f"Attempting recovery for {failed_check}")
                    
                    failure_info = validation_result.details.get(f"{failed_check}_failure")
                    recovery_result = await self.failure_recovery_strategies[failed_check](
                        environment_id, failure_info
                    )
                    
                    recovery_results[failed_check] = recovery_result
                    
                    if recovery_result.get("success", False):
                        logger.info(f"Recovery successful for {failed_check}")
                    else:
                        logger.warning(f"Recovery failed for {failed_check}: {recovery_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Recovery attempt failed for {failed_check}: {e}")
                    recovery_results[failed_check] = {
                        "success": False,
                        "error": f"Recovery attempt failed: {e}"
                    }
            else:
                logger.info(f"No recovery strategy available for {failed_check}")
                recovery_results[failed_check] = {
                    "success": False,
                    "error": "No recovery strategy available"
                }
        
        # Store recovery results
        validation_result.details["recovery_attempts"] = recovery_results
        
        return validation_result
    
    async def _recover_network_connectivity(self, environment_id: str, failure_info: ValidationFailure) -> Dict[str, Any]:
        """Attempt to recover network connectivity"""
        # This is a placeholder - in a real implementation, this might:
        # - Restart network services
        # - Reset network configuration
        # - Switch to alternative network interfaces
        await asyncio.sleep(1)  # Simulate recovery attempt
        
        return {
            "success": False,
            "error": "Network recovery not implemented",
            "attempted_actions": ["network_service_restart", "dns_flush"]
        }
    
    async def _recover_disk_space(self, environment_id: str, failure_info: ValidationFailure) -> Dict[str, Any]:
        """Attempt to recover disk space"""
        # This is a placeholder - in a real implementation, this might:
        # - Clean temporary files
        # - Compress log files
        # - Remove old deployment artifacts
        await asyncio.sleep(1)  # Simulate recovery attempt
        
        return {
            "success": False,
            "error": "Disk space recovery not implemented",
            "attempted_actions": ["temp_file_cleanup", "log_compression"]
        }
    
    async def _recover_memory_availability(self, environment_id: str, failure_info: ValidationFailure) -> Dict[str, Any]:
        """Attempt to recover memory availability"""
        # This is a placeholder - in a real implementation, this might:
        # - Clear caches
        # - Terminate non-essential processes
        # - Trigger garbage collection
        await asyncio.sleep(1)  # Simulate recovery attempt
        
        return {
            "success": False,
            "error": "Memory recovery not implemented",
            "attempted_actions": ["cache_clear", "gc_trigger"]
        }
    
    async def _recover_tool_functionality(self, environment_id: str, failure_info: ValidationFailure) -> Dict[str, Any]:
        """Attempt to recover tool functionality"""
        # This is a placeholder - in a real implementation, this might:
        # - Reinstall missing tools
        # - Update PATH environment
        # - Fix tool permissions
        await asyncio.sleep(1)  # Simulate recovery attempt
        
        return {
            "success": False,
            "error": "Tool recovery not implemented",
            "attempted_actions": ["tool_reinstall", "path_update"]
        }
    
    async def _recover_environment_permissions(self, environment_id: str, failure_info: ValidationFailure) -> Dict[str, Any]:
        """Attempt to recover environment permissions"""
        # This is a placeholder - in a real implementation, this might:
        # - Fix file permissions
        # - Change directory ownership
        # - Update access rights
        await asyncio.sleep(1)  # Simulate recovery attempt
        
        return {
            "success": False,
            "error": "Permission recovery not implemented",
            "attempted_actions": ["permission_fix", "ownership_update"]
        }
    
    def add_custom_validation_check(self, check: ValidationCheck):
        """Add a custom validation check"""
        self.custom_checks.append(check)
        logger.info(f"Added custom validation check: {check.name}")
    
    def get_validation_history(self, environment_id: str) -> List[ValidationResult]:
        """Get validation history for an environment"""
        return self.validation_history.get(environment_id, [])
    
    def get_readiness_statistics(self) -> Dict[str, Any]:
        """Get validation statistics across all environments"""
        total_validations = sum(len(history) for history in self.validation_history.values())
        
        if total_validations == 0:
            return {
                "total_validations": 0,
                "success_rate": 0.0,
                "common_failures": [],
                "environments_validated": 0
            }
        
        successful_validations = 0
        all_failures = []
        
        for history in self.validation_history.values():
            for result in history:
                if result.is_ready:
                    successful_validations += 1
                all_failures.extend(result.failed_checks)
        
        # Count failure frequencies
        failure_counts = {}
        for failure in all_failures:
            failure_counts[failure] = failure_counts.get(failure, 0) + 1
        
        # Sort by frequency
        common_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_validations": total_validations,
            "success_rate": (successful_validations / total_validations) * 100.0,
            "common_failures": common_failures[:5],  # Top 5 most common failures
            "environments_validated": len(self.validation_history)
        }
    
    def get_environment_readiness_state(self, environment_id: str):
        """Get current readiness state for an environment"""
        return self.readiness_manager.get_environment_readiness(environment_id)
    
    def get_all_environment_readiness_states(self):
        """Get readiness states for all environments"""
        return self.readiness_manager.get_all_environment_readiness()
    
    def get_ready_environments(self) -> List[str]:
        """Get list of environment IDs that are ready for test execution"""
        return self.readiness_manager.get_ready_environments()
    
    def get_not_ready_environments(self) -> List[str]:
        """Get list of environment IDs that are not ready for test execution"""
        return self.readiness_manager.get_not_ready_environments()
    
    async def mark_environment_maintenance(self, environment_id: str, maintenance_mode: bool, reason: str = None):
        """Mark environment as in maintenance mode"""
        await self.readiness_manager.mark_environment_maintenance(environment_id, maintenance_mode, reason)
    
    def subscribe_to_readiness_notifications(self, callback: callable):
        """Subscribe to readiness notifications"""
        self.readiness_manager.subscribe_to_notifications(callback)
    
    def get_recent_readiness_notifications(self, environment_id: str = None, hours: int = 24):
        """Get recent readiness notifications"""
        return self.readiness_manager.get_recent_notifications(environment_id, hours=hours)