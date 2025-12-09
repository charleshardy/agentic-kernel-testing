"""Kernel fuzzing system with Syzkaller integration.

This module provides:
- Syzkaller integration for kernel fuzzing
- Fuzzing strategy generation for different interfaces
- Fuzzing campaign management
- Crash detection and capture
- Crash input minimization
"""

import subprocess
import json
import tempfile
import shutil
import time
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FuzzingTarget(str, Enum):
    """Types of fuzzing targets."""
    SYSCALL = "syscall"
    IOCTL = "ioctl"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    DEVICE_DRIVER = "device_driver"
    CUSTOM = "custom"


class CrashSeverity(str, Enum):
    """Severity levels for crashes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FuzzingStrategy:
    """Strategy for fuzzing a specific interface."""
    target_type: FuzzingTarget
    target_name: str
    syscalls: List[str] = field(default_factory=list)
    enable_coverage: bool = True
    enable_comparisons: bool = True
    enable_fault_injection: bool = False
    max_execution_time: int = 3600  # seconds
    max_crashes: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrashInfo:
    """Information about a discovered crash."""
    crash_id: str
    title: str
    severity: CrashSeverity
    crash_type: str  # e.g., "kernel BUG", "KASAN", "general protection fault"
    reproducer: Optional[str] = None
    minimized_reproducer: Optional[str] = None
    crash_log: str = ""
    stack_trace: Optional[str] = None
    affected_function: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "crash_id": self.crash_id,
            "title": self.title,
            "severity": self.severity.value,
            "crash_type": self.crash_type,
            "reproducer": self.reproducer,
            "minimized_reproducer": self.minimized_reproducer,
            "crash_log": self.crash_log,
            "stack_trace": self.stack_trace,
            "affected_function": self.affected_function,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class FuzzingCampaign:
    """A fuzzing campaign tracking execution and results."""
    campaign_id: str
    strategy: FuzzingStrategy
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, stopped, error
    total_executions: int = 0
    crashes_found: int = 0
    unique_crashes: int = 0
    coverage_percentage: float = 0.0
    crashes: List[CrashInfo] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "campaign_id": self.campaign_id,
            "strategy": {
                "target_type": self.strategy.target_type.value,
                "target_name": self.strategy.target_name,
                "syscalls": self.strategy.syscalls
            },
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "total_executions": self.total_executions,
            "crashes_found": self.crashes_found,
            "unique_crashes": self.unique_crashes,
            "coverage_percentage": self.coverage_percentage,
            "crashes": [c.to_dict() for c in self.crashes]
        }



class FuzzingStrategyGenerator:
    """Generator for fuzzing strategies targeting different interfaces."""
    
    # Common syscalls for different subsystems
    SYSCALL_GROUPS = {
        "filesystem": [
            "open", "read", "write", "close", "stat", "fstat", "lstat",
            "mkdir", "rmdir", "unlink", "rename", "link", "symlink",
            "readlink", "chmod", "chown", "truncate", "ftruncate"
        ],
        "network": [
            "socket", "bind", "connect", "listen", "accept", "send",
            "recv", "sendto", "recvfrom", "sendmsg", "recvmsg",
            "setsockopt", "getsockopt", "shutdown"
        ],
        "process": [
            "fork", "vfork", "clone", "execve", "exit", "wait4",
            "kill", "getpid", "getppid", "getuid", "setuid",
            "getgid", "setgid", "setpgid", "getpgid"
        ],
        "memory": [
            "mmap", "munmap", "mprotect", "madvise", "mlock",
            "munlock", "brk", "sbrk", "mremap", "msync"
        ],
        "ipc": [
            "pipe", "pipe2", "msgget", "msgsnd", "msgrcv",
            "semget", "semop", "shmget", "shmat", "shmdt"
        ]
    }
    
    def generate_syscall_strategy(
        self,
        syscall_group: str = "all"
    ) -> FuzzingStrategy:
        """Generate strategy for syscall fuzzing.
        
        Args:
            syscall_group: Group of syscalls to fuzz (filesystem, network, etc.)
            
        Returns:
            Fuzzing strategy
        """
        if syscall_group == "all":
            syscalls = []
            for group_syscalls in self.SYSCALL_GROUPS.values():
                syscalls.extend(group_syscalls)
        else:
            syscalls = self.SYSCALL_GROUPS.get(syscall_group, [])
        
        return FuzzingStrategy(
            target_type=FuzzingTarget.SYSCALL,
            target_name=f"syscall_{syscall_group}",
            syscalls=syscalls,
            enable_coverage=True,
            enable_comparisons=True,
            enable_fault_injection=True
        )

    
    def generate_ioctl_strategy(
        self,
        device_path: str,
        ioctl_commands: Optional[List[int]] = None
    ) -> FuzzingStrategy:
        """Generate strategy for ioctl fuzzing.
        
        Args:
            device_path: Path to device file
            ioctl_commands: Optional list of ioctl command numbers
            
        Returns:
            Fuzzing strategy
        """
        return FuzzingStrategy(
            target_type=FuzzingTarget.IOCTL,
            target_name=f"ioctl_{Path(device_path).name}",
            syscalls=["ioctl", "open", "close"],
            enable_coverage=True,
            enable_comparisons=True,
            metadata={
                "device_path": device_path,
                "ioctl_commands": ioctl_commands or []
            }
        )
    
    def generate_network_protocol_strategy(
        self,
        protocol: str,
        address_family: str = "AF_INET"
    ) -> FuzzingStrategy:
        """Generate strategy for network protocol fuzzing.
        
        Args:
            protocol: Protocol name (tcp, udp, icmp, etc.)
            address_family: Address family (AF_INET, AF_INET6, etc.)
            
        Returns:
            Fuzzing strategy
        """
        return FuzzingStrategy(
            target_type=FuzzingTarget.NETWORK,
            target_name=f"network_{protocol}_{address_family}",
            syscalls=self.SYSCALL_GROUPS["network"],
            enable_coverage=True,
            enable_comparisons=True,
            metadata={
                "protocol": protocol,
                "address_family": address_family
            }
        )
    
    def generate_filesystem_strategy(
        self,
        filesystem_type: str
    ) -> FuzzingStrategy:
        """Generate strategy for filesystem fuzzing.
        
        Args:
            filesystem_type: Type of filesystem (ext4, xfs, btrfs, etc.)
            
        Returns:
            Fuzzing strategy
        """
        return FuzzingStrategy(
            target_type=FuzzingTarget.FILESYSTEM,
            target_name=f"fs_{filesystem_type}",
            syscalls=self.SYSCALL_GROUPS["filesystem"],
            enable_coverage=True,
            enable_comparisons=True,
            metadata={"filesystem_type": filesystem_type}
        )



class CrashDetector:
    """Detector for kernel crashes and hangs."""
    
    # Patterns indicating different crash types
    CRASH_PATTERNS = {
        "kernel_bug": [
            "kernel BUG at",
            "BUG:",
            "kernel BUG"
        ],
        "kasan": [
            "KASAN:",
            "AddressSanitizer:",
            "use-after-free",
            "out-of-bounds",
            "slab-out-of-bounds"
        ],
        "general_protection_fault": [
            "general protection fault",
            "GPF:",
            "protection fault"
        ],
        "null_pointer_dereference": [
            "unable to handle kernel NULL pointer dereference",
            "NULL pointer dereference",
            "BUG: unable to handle kernel paging request"
        ],
        "stack_overflow": [
            "stack overflow",
            "kernel stack overflow",
            "double fault"
        ],
        "deadlock": [
            "possible deadlock",
            "INFO: task .* blocked for more than",
            "hung task"
        ],
        "memory_corruption": [
            "memory corruption",
            "corrupted",
            "bad page state"
        ],
        "warning": [
            "WARNING:",
            "WARN_ON"
        ]
    }
    
    def detect_crash(self, log_output: str) -> Optional[Dict[str, Any]]:
        """Detect crash from kernel log output.
        
        Args:
            log_output: Kernel log output
            
        Returns:
            Crash information dictionary or None
        """
        for crash_type, patterns in self.CRASH_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in log_output.lower():
                    return {
                        "crash_type": crash_type,
                        "pattern_matched": pattern,
                        "severity": self._determine_severity(crash_type)
                    }
        
        return None
    
    def _determine_severity(self, crash_type: str) -> CrashSeverity:
        """Determine severity based on crash type.
        
        Args:
            crash_type: Type of crash
            
        Returns:
            Crash severity
        """
        critical_types = ["kasan", "general_protection_fault", "stack_overflow"]
        high_types = ["kernel_bug", "null_pointer_dereference", "memory_corruption"]
        medium_types = ["deadlock"]
        
        if crash_type in critical_types:
            return CrashSeverity.CRITICAL
        elif crash_type in high_types:
            return CrashSeverity.HIGH
        elif crash_type in medium_types:
            return CrashSeverity.MEDIUM
        else:
            return CrashSeverity.LOW

    
    def extract_stack_trace(self, log_output: str) -> Optional[str]:
        """Extract stack trace from crash log.
        
        Args:
            log_output: Kernel log output
            
        Returns:
            Stack trace or None
        """
        lines = log_output.split('\n')
        stack_trace_lines = []
        in_stack_trace = False
        
        for line in lines:
            # Start of stack trace
            if any(marker in line for marker in ["Call Trace:", "Backtrace:", "Stack:"]):
                in_stack_trace = True
                stack_trace_lines.append(line)
                continue
            
            # In stack trace
            if in_stack_trace:
                # Stack trace line typically starts with spaces or brackets
                if line.strip().startswith(('[', ' ', '\t')) and line.strip():
                    stack_trace_lines.append(line)
                elif not line.strip():
                    # Empty line might continue
                    continue
                else:
                    # End of stack trace
                    break
        
        return '\n'.join(stack_trace_lines) if stack_trace_lines else None
    
    def extract_affected_function(self, stack_trace: Optional[str]) -> Optional[str]:
        """Extract the affected function from stack trace.
        
        Args:
            stack_trace: Stack trace string
            
        Returns:
            Function name or None
        """
        if not stack_trace:
            return None
        
        lines = stack_trace.split('\n')
        for line in lines:
            # Look for function names in format: [<address>] function_name+0x...
            if '+0x' in line and ']' in line:
                parts = line.split(']')
                if len(parts) > 1:
                    func_part = parts[1].strip()
                    if '+0x' in func_part:
                        func_name = func_part.split('+0x')[0].strip()
                        return func_name
        
        return None



class CrashMinimizer:
    """Minimizer for crash-inducing inputs."""
    
    def minimize_reproducer(
        self,
        original_reproducer: str,
        crash_validator: callable
    ) -> str:
        """Minimize a crash reproducer to smallest form.
        
        Args:
            original_reproducer: Original reproducing input/program
            crash_validator: Function that returns True if input still crashes
            
        Returns:
            Minimized reproducer
        """
        # Start with original
        current = original_reproducer
        
        # Try removing lines
        lines = current.split('\n')
        minimized_lines = self._minimize_lines(lines, crash_validator)
        current = '\n'.join(minimized_lines)
        
        # Try reducing values
        current = self._minimize_values(current, crash_validator)
        
        return current
    
    def _minimize_lines(
        self,
        lines: List[str],
        crash_validator: callable
    ) -> List[str]:
        """Minimize by removing lines.
        
        Args:
            lines: Lines of reproducer
            crash_validator: Validation function
            
        Returns:
            Minimized lines
        """
        result = lines.copy()
        
        # Try removing each line
        i = 0
        while i < len(result):
            # Try without this line
            test_lines = result[:i] + result[i+1:]
            test_reproducer = '\n'.join(test_lines)
            
            if crash_validator(test_reproducer):
                # Still crashes, keep it removed
                result = test_lines
            else:
                # Needed for crash, keep it
                i += 1
        
        return result
    
    def _minimize_values(
        self,
        reproducer: str,
        crash_validator: callable
    ) -> str:
        """Minimize numeric values in reproducer.
        
        Args:
            reproducer: Reproducer string
            crash_validator: Validation function
            
        Returns:
            Minimized reproducer
        """
        import re
        
        # Find all numeric values
        numbers = re.findall(r'\b\d+\b', reproducer)
        
        for num_str in numbers:
            num = int(num_str)
            if num <= 1:
                continue
            
            # Try smaller values
            for smaller in [1, num // 2, num - 1]:
                if smaller >= num:
                    continue
                
                test_reproducer = reproducer.replace(num_str, str(smaller), 1)
                if crash_validator(test_reproducer):
                    reproducer = test_reproducer
                    break
        
        return reproducer



class SyzkallerRunner:
    """Runner for Syzkaller fuzzer."""
    
    def __init__(self, syzkaller_path: Optional[str] = None):
        """Initialize Syzkaller runner.
        
        Args:
            syzkaller_path: Path to Syzkaller installation
        """
        self.syzkaller_path = syzkaller_path or self._find_syzkaller()
        self.crash_detector = CrashDetector()
        self.crash_minimizer = CrashMinimizer()
    
    def _find_syzkaller(self) -> str:
        """Find Syzkaller installation.
        
        Returns:
            Path to Syzkaller
        """
        # Try common locations
        common_paths = [
            "/usr/local/syzkaller",
            "/opt/syzkaller",
            str(Path.home() / "syzkaller")
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        # Default
        return "/usr/local/syzkaller"
    
    def create_config(
        self,
        strategy: FuzzingStrategy,
        kernel_image: str,
        work_dir: str
    ) -> Dict[str, Any]:
        """Create Syzkaller configuration.
        
        Args:
            strategy: Fuzzing strategy
            kernel_image: Path to kernel image
            work_dir: Working directory
            
        Returns:
            Configuration dictionary
        """
        config = {
            "target": "linux/amd64",
            "http": "127.0.0.1:56741",
            "workdir": work_dir,
            "kernel_obj": str(Path(kernel_image).parent),
            "image": kernel_image,
            "sshkey": str(Path.home() / ".ssh/id_rsa"),
            "syzkaller": self.syzkaller_path,
            "procs": 8,
            "type": "qemu",
            "vm": {
                "count": 4,
                "kernel": kernel_image,
                "cpu": 2,
                "mem": 2048
            }
        }
        
        # Add syscall enable list if specified
        if strategy.syscalls:
            config["enable_syscalls"] = strategy.syscalls
        
        # Add coverage options
        if strategy.enable_coverage:
            config["cover"] = True
        
        if strategy.enable_comparisons:
            config["comparisons"] = True
        
        return config

    
    def run_fuzzing(
        self,
        config: Dict[str, Any],
        duration: int = 3600
    ) -> Dict[str, Any]:
        """Run Syzkaller fuzzing campaign.
        
        Args:
            config: Syzkaller configuration
            duration: Duration in seconds
            
        Returns:
            Fuzzing results
        """
        # Write config to file
        config_file = Path(config["workdir"]) / "syzkaller.cfg"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Run Syzkaller
        syz_manager = Path(self.syzkaller_path) / "bin" / "syz-manager"
        
        try:
            process = subprocess.Popen(
                [str(syz_manager), "-config", str(config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for duration or completion
            start_time = time.time()
            while time.time() - start_time < duration:
                if process.poll() is not None:
                    break
                time.sleep(10)
            
            # Stop fuzzing
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
            
            # Collect results
            results = self._collect_results(config["workdir"])
            return results
            
        except Exception as e:
            return {
                "error": str(e),
                "crashes": [],
                "executions": 0
            }
    
    def _collect_results(self, work_dir: str) -> Dict[str, Any]:
        """Collect fuzzing results from work directory.
        
        Args:
            work_dir: Syzkaller work directory
            
        Returns:
            Results dictionary
        """
        work_path = Path(work_dir)
        crashes_dir = work_path / "crashes"
        
        results = {
            "crashes": [],
            "executions": 0,
            "coverage": 0.0
        }
        
        if not crashes_dir.exists():
            return results
        
        # Parse crashes
        for crash_dir in crashes_dir.iterdir():
            if not crash_dir.is_dir():
                continue
            
            crash_info = self._parse_crash_dir(crash_dir)
            if crash_info:
                results["crashes"].append(crash_info)
        
        # Read stats if available
        stats_file = work_path / "stats.json"
        if stats_file.exists():
            try:
                with open(stats_file) as f:
                    stats = json.load(f)
                    results["executions"] = stats.get("exec_total", 0)
                    results["coverage"] = stats.get("coverage", 0.0)
            except:
                pass
        
        return results

    
    def _parse_crash_dir(self, crash_dir: Path) -> Optional[Dict[str, Any]]:
        """Parse crash directory to extract crash information.
        
        Args:
            crash_dir: Path to crash directory
            
        Returns:
            Crash information dictionary
        """
        # Read crash log
        log_file = crash_dir / "log"
        if not log_file.exists():
            return None
        
        try:
            with open(log_file) as f:
                log_content = f.read()
        except:
            return None
        
        # Detect crash type
        crash_detection = self.crash_detector.detect_crash(log_content)
        if not crash_detection:
            return None
        
        # Extract stack trace
        stack_trace = self.crash_detector.extract_stack_trace(log_content)
        affected_function = self.crash_detector.extract_affected_function(stack_trace)
        
        # Read reproducer if available
        reproducer = None
        repro_file = crash_dir / "repro.prog"
        if repro_file.exists():
            try:
                with open(repro_file) as f:
                    reproducer = f.read()
            except:
                pass
        
        return {
            "crash_id": crash_dir.name,
            "title": crash_dir.name.replace('_', ' '),
            "crash_type": crash_detection["crash_type"],
            "severity": crash_detection["severity"].value,
            "crash_log": log_content[:1000],  # First 1000 chars
            "stack_trace": stack_trace,
            "affected_function": affected_function,
            "reproducer": reproducer
        }


class KernelFuzzer:
    """Main kernel fuzzing system interface."""
    
    def __init__(self, syzkaller_path: Optional[str] = None):
        """Initialize kernel fuzzer.
        
        Args:
            syzkaller_path: Path to Syzkaller installation
        """
        self.strategy_generator = FuzzingStrategyGenerator()
        self.syzkaller_runner = SyzkallerRunner(syzkaller_path)
        self.crash_detector = CrashDetector()
        self.crash_minimizer = CrashMinimizer()
        self.active_campaigns: Dict[str, FuzzingCampaign] = {}
    
    def start_campaign(
        self,
        strategy: FuzzingStrategy,
        kernel_image: str,
        work_dir: Optional[str] = None
    ) -> FuzzingCampaign:
        """Start a fuzzing campaign.
        
        Args:
            strategy: Fuzzing strategy
            kernel_image: Path to kernel image
            work_dir: Optional work directory
            
        Returns:
            Fuzzing campaign
        """
        campaign_id = str(uuid.uuid4())
        
        if work_dir is None:
            work_dir = tempfile.mkdtemp(prefix=f"fuzz_{campaign_id}_")
        
        campaign = FuzzingCampaign(
            campaign_id=campaign_id,
            strategy=strategy,
            start_time=datetime.now(),
            status="running"
        )
        
        self.active_campaigns[campaign_id] = campaign
        
        # Create Syzkaller config
        config = self.syzkaller_runner.create_config(
            strategy,
            kernel_image,
            work_dir
        )
        
        # Run fuzzing in background (in real implementation, use threading/async)
        # For now, run synchronously
        results = self.syzkaller_runner.run_fuzzing(
            config,
            duration=strategy.max_execution_time
        )
        
        # Update campaign with results
        campaign.total_executions = results.get("executions", 0)
        campaign.coverage_percentage = results.get("coverage", 0.0)
        
        # Process crashes
        for crash_data in results.get("crashes", []):
            crash_info = CrashInfo(
                crash_id=crash_data["crash_id"],
                title=crash_data["title"],
                severity=CrashSeverity(crash_data["severity"]),
                crash_type=crash_data["crash_type"],
                crash_log=crash_data["crash_log"],
                stack_trace=crash_data.get("stack_trace"),
                affected_function=crash_data.get("affected_function"),
                reproducer=crash_data.get("reproducer")
            )
            
            campaign.crashes.append(crash_info)
        
        campaign.crashes_found = len(campaign.crashes)
        campaign.unique_crashes = len(set(c.title for c in campaign.crashes))
        campaign.status = "completed"
        campaign.end_time = datetime.now()
        
        return campaign

    
    def stop_campaign(self, campaign_id: str) -> bool:
        """Stop a running fuzzing campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            True if stopped successfully
        """
        campaign = self.active_campaigns.get(campaign_id)
        if not campaign:
            return False
        
        if campaign.status != "running":
            return False
        
        campaign.status = "stopped"
        campaign.end_time = datetime.now()
        
        return True
    
    def get_campaign_status(self, campaign_id: str) -> Optional[FuzzingCampaign]:
        """Get status of a fuzzing campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign or None
        """
        return self.active_campaigns.get(campaign_id)
    
    def minimize_crash(
        self,
        crash_info: CrashInfo,
        crash_validator: callable
    ) -> CrashInfo:
        """Minimize a crash reproducer.
        
        Args:
            crash_info: Crash information
            crash_validator: Function to validate if input still crashes
            
        Returns:
            Updated crash info with minimized reproducer
        """
        if not crash_info.reproducer:
            return crash_info
        
        minimized = self.crash_minimizer.minimize_reproducer(
            crash_info.reproducer,
            crash_validator
        )
        
        crash_info.minimized_reproducer = minimized
        return crash_info
    
    def generate_report(
        self,
        campaign: FuzzingCampaign
    ) -> Dict[str, Any]:
        """Generate fuzzing campaign report.
        
        Args:
            campaign: Fuzzing campaign
            
        Returns:
            Report dictionary
        """
        # Group crashes by type
        crashes_by_type = {}
        for crash in campaign.crashes:
            crash_type = crash.crash_type
            if crash_type not in crashes_by_type:
                crashes_by_type[crash_type] = []
            crashes_by_type[crash_type].append(crash)
        
        # Group by severity
        crashes_by_severity = {}
        for crash in campaign.crashes:
            severity = crash.severity.value
            if severity not in crashes_by_severity:
                crashes_by_severity[severity] = []
            crashes_by_severity[severity].append(crash)
        
        report = {
            "campaign_id": campaign.campaign_id,
            "strategy": {
                "target_type": campaign.strategy.target_type.value,
                "target_name": campaign.strategy.target_name
            },
            "duration_seconds": (
                (campaign.end_time - campaign.start_time).total_seconds()
                if campaign.end_time else 0
            ),
            "total_executions": campaign.total_executions,
            "coverage_percentage": campaign.coverage_percentage,
            "crashes_found": campaign.crashes_found,
            "unique_crashes": campaign.unique_crashes,
            "crashes_by_type": {
                crash_type: len(crashes)
                for crash_type, crashes in crashes_by_type.items()
            },
            "crashes_by_severity": {
                severity: len(crashes)
                for severity, crashes in crashes_by_severity.items()
            },
            "crash_details": [crash.to_dict() for crash in campaign.crashes]
        }
        
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fuzzer statistics.
        
        Returns:
            Statistics dictionary
        """
        total_campaigns = len(self.active_campaigns)
        completed_campaigns = sum(
            1 for c in self.active_campaigns.values()
            if c.status == "completed"
        )
        total_crashes = sum(
            c.crashes_found for c in self.active_campaigns.values()
        )
        total_executions = sum(
            c.total_executions for c in self.active_campaigns.values()
        )
        
        return {
            "total_campaigns": total_campaigns,
            "completed_campaigns": completed_campaigns,
            "running_campaigns": total_campaigns - completed_campaigns,
            "total_crashes_found": total_crashes,
            "total_executions": total_executions,
            "campaigns": [
                {
                    "campaign_id": c.campaign_id,
                    "status": c.status,
                    "crashes_found": c.crashes_found
                }
                for c in self.active_campaigns.values()
            ]
        }
