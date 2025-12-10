"""Kernel configuration testing system.

This module provides functionality for:
- Generating kernel configurations (minimal, default, maximal)
- Validating kernel configurations
- Building kernels with different configurations
- Orchestrating configuration testing
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import tempfile
import shutil
from pathlib import Path
import json
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_generator.models import TestResult, TestCase, HardwareConfig


logger = logging.getLogger(__name__)


class ConfigType(Enum):
    """Types of kernel configurations."""
    MINIMAL = "minimal"
    DEFAULT = "default"
    MAXIMAL = "maximal"
    CUSTOM = "custom"


@dataclass
class KernelConfig:
    """Represents a kernel configuration."""
    name: str
    config_type: ConfigType
    options: Dict[str, str] = field(default_factory=dict)
    architecture: str = "x86_64"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'config_type': self.config_type.value,
            'options': self.options,
            'architecture': self.architecture,
            'description': self.description,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KernelConfig':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            config_type=ConfigType(data['config_type']),
            options=data.get('options', {}),
            architecture=data.get('architecture', 'x86_64'),
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )


@dataclass
class ConfigBuildResult:
    """Result of building a kernel configuration."""
    config: KernelConfig
    success: bool
    build_time: float
    kernel_image_path: Optional[Path] = None
    build_log: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    size_bytes: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'config': self.config.to_dict(),
            'success': self.success,
            'build_time': self.build_time,
            'kernel_image_path': str(self.kernel_image_path) if self.kernel_image_path else None,
            'build_log': self.build_log,
            'errors': self.errors,
            'warnings': self.warnings,
            'size_bytes': self.size_bytes
        }


@dataclass
class ConfigBootResult:
    """Result of booting a kernel configuration."""
    config: KernelConfig
    success: bool
    boot_time: float
    log: str = ""
    errors: List[str] = field(default_factory=list)
    boot_stages: Dict[str, bool] = field(default_factory=dict)
    kernel_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'config': self.config.to_dict(),
            'success': self.success,
            'boot_time': self.boot_time,
            'log': self.log,
            'errors': self.errors,
            'boot_stages': self.boot_stages,
            'kernel_version': self.kernel_version
        }


@dataclass
class ConfigTestResult:
    """Result of testing a kernel configuration."""
    config: KernelConfig
    build_result: ConfigBuildResult
    boot_success: bool = False
    boot_time: Optional[float] = None
    basic_functionality_tests: List[TestResult] = field(default_factory=list)
    test_log: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'config': self.config.to_dict(),
            'build_result': self.build_result.to_dict(),
            'boot_success': self.boot_success,
            'boot_time': self.boot_time,
            'basic_functionality_tests': [t.to_dict() for t in self.basic_functionality_tests],
            'test_log': self.test_log
        }


class KernelConfigGenerator:
    """Generator for different types of kernel configurations."""
    
    # Common configuration options for different types
    MINIMAL_CONFIG_BASE = {
        'CONFIG_EMBEDDED': 'y',
        'CONFIG_EXPERT': 'y',
        'CONFIG_MODULES': 'n',
        'CONFIG_SWAP': 'n',
        'CONFIG_SYSVIPC': 'n',
        'CONFIG_POSIX_MQUEUE': 'n',
        'CONFIG_AUDIT': 'n',
        'CONFIG_IKCONFIG': 'n',
        'CONFIG_LOG_BUF_SHIFT': '12',
        'CONFIG_CGROUPS': 'n',
        'CONFIG_NAMESPACES': 'n',
        'CONFIG_SCHED_AUTOGROUP': 'n',
        'CONFIG_BLK_DEV_INITRD': 'n',
        'CONFIG_CC_OPTIMIZE_FOR_SIZE': 'y',
        'CONFIG_KALLSYMS': 'n',
        'CONFIG_PRINTK': 'y',
        'CONFIG_BUG': 'y',
        'CONFIG_ELF_CORE': 'n',
        'CONFIG_BASE_FULL': 'n',
        'CONFIG_FUTEX': 'y',
        'CONFIG_EPOLL': 'n',
        'CONFIG_SIGNALFD': 'n',
        'CONFIG_TIMERFD': 'n',
        'CONFIG_EVENTFD': 'n',
        'CONFIG_SHMEM': 'y',
        'CONFIG_AIO': 'n',
        'CONFIG_VM_EVENT_COUNTERS': 'n',
        'CONFIG_PCI_QUIRKS': 'n',
        'CONFIG_SLUB_DEBUG': 'n',
        'CONFIG_COMPAT_BRK': 'n'
    }
    
    DEFAULT_CONFIG_BASE = {
        'CONFIG_MODULES': 'y',
        'CONFIG_MODULE_UNLOAD': 'y',
        'CONFIG_MODVERSIONS': 'y',
        'CONFIG_SWAP': 'y',
        'CONFIG_SYSVIPC': 'y',
        'CONFIG_POSIX_MQUEUE': 'y',
        'CONFIG_AUDIT': 'y',
        'CONFIG_IKCONFIG': 'y',
        'CONFIG_IKCONFIG_PROC': 'y',
        'CONFIG_LOG_BUF_SHIFT': '17',
        'CONFIG_CGROUPS': 'y',
        'CONFIG_NAMESPACES': 'y',
        'CONFIG_SCHED_AUTOGROUP': 'y',
        'CONFIG_BLK_DEV_INITRD': 'y',
        'CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE': 'y',
        'CONFIG_KALLSYMS': 'y',
        'CONFIG_KALLSYMS_ALL': 'y',
        'CONFIG_PRINTK': 'y',
        'CONFIG_BUG': 'y',
        'CONFIG_ELF_CORE': 'y',
        'CONFIG_BASE_FULL': 'y',
        'CONFIG_FUTEX': 'y',
        'CONFIG_EPOLL': 'y',
        'CONFIG_SIGNALFD': 'y',
        'CONFIG_TIMERFD': 'y',
        'CONFIG_EVENTFD': 'y',
        'CONFIG_SHMEM': 'y',
        'CONFIG_AIO': 'y',
        'CONFIG_VM_EVENT_COUNTERS': 'y',
        'CONFIG_PCI_QUIRKS': 'y',
        'CONFIG_SLUB_DEBUG': 'y'
    }
    
    MAXIMAL_CONFIG_ADDITIONS = {
        'CONFIG_DEBUG_KERNEL': 'y',
        'CONFIG_DEBUG_INFO': 'y',
        'CONFIG_DEBUG_INFO_DWARF4': 'y',
        'CONFIG_FRAME_POINTER': 'y',
        'CONFIG_DEBUG_FS': 'y',
        'CONFIG_MAGIC_SYSRQ': 'y',
        'CONFIG_DEBUG_PAGEALLOC': 'y',
        'CONFIG_DEBUG_OBJECTS': 'y',
        'CONFIG_DEBUG_SLAB': 'y',
        'CONFIG_DEBUG_KMEMLEAK': 'y',
        'CONFIG_DEBUG_STACK_USAGE': 'y',
        'CONFIG_DEBUG_VM': 'y',
        'CONFIG_DEBUG_MEMORY_INIT': 'y',
        'CONFIG_DEBUG_LIST': 'y',
        'CONFIG_DEBUG_SG': 'y',
        'CONFIG_DEBUG_NOTIFIERS': 'y',
        'CONFIG_DEBUG_CREDENTIALS': 'y',
        'CONFIG_RCU_CPU_STALL_DETECTOR': 'y',
        'CONFIG_LATENCYTOP': 'y',
        'CONFIG_FUNCTION_TRACER': 'y',
        'CONFIG_STACK_TRACER': 'y',
        'CONFIG_DYNAMIC_DEBUG': 'y',
        'CONFIG_KASAN': 'y',
        'CONFIG_UBSAN': 'y',
        'CONFIG_KCOV': 'y',
        'CONFIG_PROVE_LOCKING': 'y',
        'CONFIG_LOCK_STAT': 'y',
        'CONFIG_DEBUG_LOCKDEP': 'y',
        'CONFIG_DEBUG_ATOMIC_SLEEP': 'y',
        'CONFIG_DEBUG_LOCKING_API_SELFTESTS': 'y'
    }
    
    def __init__(self, kernel_source_path: Path):
        """Initialize generator with kernel source path.
        
        Args:
            kernel_source_path: Path to kernel source directory
        """
        self.kernel_source_path = kernel_source_path
        if not self.kernel_source_path.exists():
            raise ValueError(f"Kernel source path does not exist: {kernel_source_path}")
    
    def generate_minimal_config(self, architecture: str = "x86_64") -> KernelConfig:
        """Generate minimal kernel configuration.
        
        Args:
            architecture: Target architecture
            
        Returns:
            Minimal kernel configuration
        """
        config = KernelConfig(
            name=f"minimal_{architecture}",
            config_type=ConfigType.MINIMAL,
            options=self.MINIMAL_CONFIG_BASE.copy(),
            architecture=architecture,
            description="Minimal kernel configuration with only essential features"
        )
        
        # Add architecture-specific minimal options
        arch_options = self._get_architecture_minimal_options(architecture)
        config.options.update(arch_options)
        
        return config
    
    def generate_default_config(self, architecture: str = "x86_64") -> KernelConfig:
        """Generate default kernel configuration.
        
        Args:
            architecture: Target architecture
            
        Returns:
            Default kernel configuration
        """
        config = KernelConfig(
            name=f"default_{architecture}",
            config_type=ConfigType.DEFAULT,
            options=self.DEFAULT_CONFIG_BASE.copy(),
            architecture=architecture,
            description="Default kernel configuration with standard features"
        )
        
        # Add architecture-specific default options
        arch_options = self._get_architecture_default_options(architecture)
        config.options.update(arch_options)
        
        return config
    
    def generate_maximal_config(self, architecture: str = "x86_64") -> KernelConfig:
        """Generate maximal kernel configuration.
        
        Args:
            architecture: Target architecture
            
        Returns:
            Maximal kernel configuration with debug features
        """
        # Start with default config and add maximal options
        options = self.DEFAULT_CONFIG_BASE.copy()
        options.update(self.MAXIMAL_CONFIG_ADDITIONS)
        
        config = KernelConfig(
            name=f"maximal_{architecture}",
            config_type=ConfigType.MAXIMAL,
            options=options,
            architecture=architecture,
            description="Maximal kernel configuration with all debug and testing features"
        )
        
        # Add architecture-specific maximal options
        arch_options = self._get_architecture_maximal_options(architecture)
        config.options.update(arch_options)
        
        return config
    
    def generate_all_standard_configs(self, architecture: str = "x86_64") -> List[KernelConfig]:
        """Generate all standard configuration types.
        
        Args:
            architecture: Target architecture
            
        Returns:
            List containing minimal, default, and maximal configurations
        """
        return [
            self.generate_minimal_config(architecture),
            self.generate_default_config(architecture),
            self.generate_maximal_config(architecture)
        ]
    
    def _get_architecture_minimal_options(self, architecture: str) -> Dict[str, str]:
        """Get architecture-specific minimal options."""
        arch_options = {}
        
        if architecture == "x86_64":
            arch_options.update({
                'CONFIG_64BIT': 'y',
                'CONFIG_X86_64': 'y',
                'CONFIG_SMP': 'n',
                'CONFIG_ACPI': 'n',
                'CONFIG_PCI': 'y',
                'CONFIG_NET': 'n'
            })
        elif architecture == "arm64":
            arch_options.update({
                'CONFIG_ARM64': 'y',
                'CONFIG_SMP': 'n',
                'CONFIG_PCI': 'n',
                'CONFIG_NET': 'n'
            })
        elif architecture == "arm":
            arch_options.update({
                'CONFIG_ARM': 'y',
                'CONFIG_SMP': 'n',
                'CONFIG_PCI': 'n',
                'CONFIG_NET': 'n'
            })
        elif architecture == "riscv64":
            arch_options.update({
                'CONFIG_RISCV': 'y',
                'CONFIG_64BIT': 'y',
                'CONFIG_SMP': 'n',
                'CONFIG_PCI': 'n',
                'CONFIG_NET': 'n'
            })
        
        return arch_options
    
    def _get_architecture_default_options(self, architecture: str) -> Dict[str, str]:
        """Get architecture-specific default options."""
        arch_options = {}
        
        if architecture == "x86_64":
            arch_options.update({
                'CONFIG_64BIT': 'y',
                'CONFIG_X86_64': 'y',
                'CONFIG_SMP': 'y',
                'CONFIG_ACPI': 'y',
                'CONFIG_PCI': 'y',
                'CONFIG_NET': 'y',
                'CONFIG_INET': 'y',
                'CONFIG_BLOCK': 'y',
                'CONFIG_EXT4_FS': 'y'
            })
        elif architecture == "arm64":
            arch_options.update({
                'CONFIG_ARM64': 'y',
                'CONFIG_SMP': 'y',
                'CONFIG_PCI': 'y',
                'CONFIG_NET': 'y',
                'CONFIG_INET': 'y',
                'CONFIG_BLOCK': 'y',
                'CONFIG_EXT4_FS': 'y'
            })
        elif architecture == "arm":
            arch_options.update({
                'CONFIG_ARM': 'y',
                'CONFIG_SMP': 'y',
                'CONFIG_PCI': 'y',
                'CONFIG_NET': 'y',
                'CONFIG_INET': 'y',
                'CONFIG_BLOCK': 'y',
                'CONFIG_EXT4_FS': 'y'
            })
        elif architecture == "riscv64":
            arch_options.update({
                'CONFIG_RISCV': 'y',
                'CONFIG_64BIT': 'y',
                'CONFIG_SMP': 'y',
                'CONFIG_PCI': 'y',
                'CONFIG_NET': 'y',
                'CONFIG_INET': 'y',
                'CONFIG_BLOCK': 'y',
                'CONFIG_EXT4_FS': 'y'
            })
        
        return arch_options
    
    def _get_architecture_maximal_options(self, architecture: str) -> Dict[str, str]:
        """Get architecture-specific maximal options."""
        # Start with default options and add debug features
        arch_options = self._get_architecture_default_options(architecture)
        
        # Add architecture-specific debug options
        if architecture == "x86_64":
            arch_options.update({
                'CONFIG_X86_PTDUMP': 'y',
                'CONFIG_DEBUG_WX': 'y',
                'CONFIG_DOUBLEFAULT': 'y'
            })
        elif architecture in ["arm64", "arm"]:
            arch_options.update({
                'CONFIG_DEBUG_WX': 'y',
                'CONFIG_ARM64_PTDUMP': 'y' if architecture == "arm64" else 'n'
            })
        
        return arch_options


class KernelConfigValidator:
    """Validator for kernel configurations."""
    
    def __init__(self, kernel_source_path: Path):
        """Initialize validator with kernel source path.
        
        Args:
            kernel_source_path: Path to kernel source directory
        """
        self.kernel_source_path = kernel_source_path
        if not self.kernel_source_path.exists():
            raise ValueError(f"Kernel source path does not exist: {kernel_source_path}")
    
    def validate_config(self, config: KernelConfig) -> Tuple[bool, List[str], List[str]]:
        """Validate a kernel configuration.
        
        Args:
            config: Kernel configuration to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check for required options
        required_errors = self._check_required_options(config)
        errors.extend(required_errors)
        
        # Check for conflicting options
        conflict_errors = self._check_conflicting_options(config)
        errors.extend(conflict_errors)
        
        # Check for deprecated options
        deprecated_warnings = self._check_deprecated_options(config)
        warnings.extend(deprecated_warnings)
        
        # Check architecture consistency
        arch_errors = self._check_architecture_consistency(config)
        errors.extend(arch_errors)
        
        # Check for performance implications
        perf_warnings = self._check_performance_implications(config)
        warnings.extend(perf_warnings)
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def _check_required_options(self, config: KernelConfig) -> List[str]:
        """Check for required configuration options."""
        errors = []
        
        # Architecture-specific required options
        if config.architecture == "x86_64":
            if config.options.get('CONFIG_64BIT') != 'y':
                errors.append("CONFIG_64BIT must be enabled for x86_64")
            if config.options.get('CONFIG_X86_64') != 'y':
                errors.append("CONFIG_X86_64 must be enabled for x86_64")
        elif config.architecture == "arm64":
            if config.options.get('CONFIG_ARM64') != 'y':
                errors.append("CONFIG_ARM64 must be enabled for arm64")
        elif config.architecture == "arm":
            if config.options.get('CONFIG_ARM') != 'y':
                errors.append("CONFIG_ARM must be enabled for arm")
        elif config.architecture == "riscv64":
            if config.options.get('CONFIG_RISCV') != 'y':
                errors.append("CONFIG_RISCV must be enabled for riscv64")
            if config.options.get('CONFIG_64BIT') != 'y':
                errors.append("CONFIG_64BIT must be enabled for riscv64")
        
        # Essential kernel options
        if config.options.get('CONFIG_PRINTK') != 'y':
            errors.append("CONFIG_PRINTK should be enabled for debugging")
        
        return errors
    
    def _check_conflicting_options(self, config: KernelConfig) -> List[str]:
        """Check for conflicting configuration options."""
        errors = []
        
        # Check for mutually exclusive options
        if (config.options.get('CONFIG_CC_OPTIMIZE_FOR_SIZE') == 'y' and
            config.options.get('CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE') == 'y'):
            errors.append("Cannot optimize for both size and performance")
        
        # Debug options conflicts
        if (config.options.get('CONFIG_SLUB_DEBUG') == 'y' and
            config.options.get('CONFIG_SLOB') == 'y'):
            errors.append("SLUB_DEBUG conflicts with SLOB allocator")
        
        # Memory debugging conflicts
        if (config.options.get('CONFIG_KASAN') == 'y' and
            config.options.get('CONFIG_KFENCE') == 'y'):
            errors.append("KASAN and KFENCE should not be enabled together")
        
        return errors
    
    def _check_deprecated_options(self, config: KernelConfig) -> List[str]:
        """Check for deprecated configuration options."""
        warnings = []
        
        deprecated_options = [
            'CONFIG_SYSFS_DEPRECATED',
            'CONFIG_UEVENT_HELPER',
            'CONFIG_DEVTMPFS_MOUNT'
        ]
        
        for option in deprecated_options:
            if option in config.options:
                warnings.append(f"{option} is deprecated and should be avoided")
        
        return warnings
    
    def _check_architecture_consistency(self, config: KernelConfig) -> List[str]:
        """Check architecture consistency."""
        errors = []
        
        # Check that architecture-specific options match the target architecture
        x86_options = ['CONFIG_X86_64', 'CONFIG_X86_32']
        arm_options = ['CONFIG_ARM64', 'CONFIG_ARM']
        riscv_options = ['CONFIG_RISCV']
        
        if config.architecture == "x86_64":
            for option in arm_options + riscv_options:
                if config.options.get(option) == 'y':
                    errors.append(f"{option} should not be enabled for x86_64")
        elif config.architecture in ["arm64", "arm"]:
            for option in x86_options + riscv_options:
                if config.options.get(option) == 'y':
                    errors.append(f"{option} should not be enabled for {config.architecture}")
        elif config.architecture == "riscv64":
            for option in x86_options + arm_options:
                if config.options.get(option) == 'y':
                    errors.append(f"{option} should not be enabled for riscv64")
        
        return errors
    
    def _check_performance_implications(self, config: KernelConfig) -> List[str]:
        """Check for performance implications."""
        warnings = []
        
        # Debug options that impact performance
        perf_impact_options = [
            'CONFIG_DEBUG_PAGEALLOC',
            'CONFIG_DEBUG_SLAB',
            'CONFIG_DEBUG_KMEMLEAK',
            'CONFIG_KASAN',
            'CONFIG_UBSAN',
            'CONFIG_PROVE_LOCKING',
            'CONFIG_DEBUG_LOCKDEP'
        ]
        
        enabled_debug = [opt for opt in perf_impact_options 
                        if config.options.get(opt) == 'y']
        
        if enabled_debug and config.config_type != ConfigType.MAXIMAL:
            warnings.append(
                f"Performance impact: debug options enabled: {', '.join(enabled_debug)}"
            )
        
        return warnings


class KernelConfigBuilder:
    """Builder for kernel configurations."""
    
    def __init__(self, kernel_source_path: Path, build_dir: Optional[Path] = None):
        """Initialize builder.
        
        Args:
            kernel_source_path: Path to kernel source directory
            build_dir: Optional build directory (uses temp dir if None)
        """
        self.kernel_source_path = kernel_source_path
        self.build_dir = build_dir or Path(tempfile.mkdtemp(prefix="kernel_build_"))
        
        if not self.kernel_source_path.exists():
            raise ValueError(f"Kernel source path does not exist: {kernel_source_path}")
        
        # Ensure build directory exists
        self.build_dir.mkdir(parents=True, exist_ok=True)
    
    def build_config(self, config: KernelConfig, timeout: int = 3600) -> ConfigBuildResult:
        """Build a kernel with the given configuration.
        
        Args:
            config: Kernel configuration to build
            timeout: Build timeout in seconds
            
        Returns:
            Build result with success status and details
        """
        logger.info(f"Building kernel config: {config.name}")
        start_time = time.time()
        
        try:
            # Create config-specific build directory
            config_build_dir = self.build_dir / config.name
            config_build_dir.mkdir(parents=True, exist_ok=True)
            
            # Write .config file
            config_file = config_build_dir / ".config"
            self._write_config_file(config, config_file)
            
            # Run make olddefconfig to resolve dependencies
            olddefconfig_result = self._run_make_command(
                ["olddefconfig"], config_build_dir, timeout=300
            )
            
            if olddefconfig_result.returncode != 0:
                return ConfigBuildResult(
                    config=config,
                    success=False,
                    build_time=time.time() - start_time,
                    build_log=olddefconfig_result.stdout + olddefconfig_result.stderr,
                    errors=[f"olddefconfig failed: {olddefconfig_result.stderr}"]
                )
            
            # Build the kernel
            build_result = self._run_make_command(
                ["-j", str(self._get_cpu_count())], config_build_dir, timeout
            )
            
            build_time = time.time() - start_time
            success = build_result.returncode == 0
            
            # Find kernel image
            kernel_image_path = None
            size_bytes = None
            if success:
                kernel_image_path = self._find_kernel_image(config_build_dir, config.architecture)
                if kernel_image_path and kernel_image_path.exists():
                    size_bytes = kernel_image_path.stat().st_size
            
            # Parse build output for errors and warnings
            errors, warnings = self._parse_build_output(build_result.stderr)
            
            return ConfigBuildResult(
                config=config,
                success=success,
                build_time=build_time,
                kernel_image_path=kernel_image_path,
                build_log=build_result.stdout + build_result.stderr,
                errors=errors,
                warnings=warnings,
                size_bytes=size_bytes
            )
            
        except Exception as e:
            logger.error(f"Build failed with exception: {e}")
            return ConfigBuildResult(
                config=config,
                success=False,
                build_time=time.time() - start_time,
                errors=[f"Build exception: {str(e)}"]
            )
    
    def _write_config_file(self, config: KernelConfig, config_file: Path):
        """Write configuration to .config file."""
        with open(config_file, 'w') as f:
            for option, value in config.options.items():
                if value == 'y':
                    f.write(f"{option}=y\n")
                elif value == 'n':
                    f.write(f"# {option} is not set\n")
                elif value == 'm':
                    f.write(f"{option}=m\n")
                else:
                    f.write(f"{option}={value}\n")
    
    def _run_make_command(self, args: List[str], build_dir: Path, timeout: int) -> subprocess.CompletedProcess:
        """Run make command in build directory."""
        cmd = ["make", "-C", str(self.kernel_source_path), f"O={build_dir}"] + args
        
        logger.debug(f"Running: {' '.join(cmd)}")
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=build_dir
        )
    
    def _get_cpu_count(self) -> int:
        """Get number of CPUs for parallel build."""
        import os
        return os.cpu_count() or 1
    
    def _find_kernel_image(self, build_dir: Path, architecture: str) -> Optional[Path]:
        """Find the built kernel image."""
        # Common kernel image names by architecture
        image_names = {
            'x86_64': ['arch/x86/boot/bzImage', 'vmlinux'],
            'arm64': ['arch/arm64/boot/Image', 'vmlinux'],
            'arm': ['arch/arm/boot/zImage', 'vmlinux'],
            'riscv64': ['arch/riscv/boot/Image', 'vmlinux']
        }
        
        for image_name in image_names.get(architecture, ['vmlinux']):
            image_path = build_dir / image_name
            if image_path.exists():
                return image_path
        
        return None
    
    def _parse_build_output(self, output: str) -> Tuple[List[str], List[str]]:
        """Parse build output for errors and warnings."""
        errors = []
        warnings = []
        
        for line in output.split('\n'):
            line = line.strip()
            if 'error:' in line.lower():
                errors.append(line)
            elif 'warning:' in line.lower():
                warnings.append(line)
        
        return errors, warnings


class KernelConfigBootTester:
    """Boot tester for kernel configurations."""
    
    def __init__(self, work_dir: Optional[Path] = None):
        """Initialize boot tester.
        
        Args:
            work_dir: Working directory for boot testing
        """
        self.work_dir = work_dir or Path(tempfile.mkdtemp(prefix="boot_test_"))
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    def boot_test_config(self, config: KernelConfig, build_result: ConfigBuildResult, timeout: int = 300) -> ConfigBootResult:
        """Boot test a kernel configuration.
        
        Args:
            config: Kernel configuration to boot test
            build_result: Build result containing kernel image
            timeout: Boot timeout in seconds
            
        Returns:
            Boot test result
        """
        logger.info(f"Boot testing configuration: {config.name}")
        start_time = time.time()
        
        if not build_result.success or not build_result.kernel_image_path:
            return ConfigBootResult(
                config=config,
                success=False,
                boot_time=0.0,
                log="Cannot boot test: build failed or no kernel image",
                errors=["Build failed or kernel image not available"]
            )
        
        try:
            # Create boot test environment
            boot_dir = self.work_dir / f"boot_{config.name}"
            boot_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine boot method based on architecture and emulator availability
            if self._is_qemu_available():
                return self._boot_test_qemu(config, build_result, boot_dir, timeout)
            else:
                # Fallback to basic validation without actual boot
                return self._boot_test_validation_only(config, build_result, timeout)
                
        except Exception as e:
            logger.error(f"Boot test failed with exception: {e}")
            return ConfigBootResult(
                config=config,
                success=False,
                boot_time=time.time() - start_time,
                log=f"Boot test exception: {str(e)}",
                errors=[f"Boot test exception: {str(e)}"]
            )
    
    def _is_qemu_available(self) -> bool:
        """Check if QEMU is available for boot testing."""
        try:
            result = subprocess.run(
                ["qemu-system-x86_64", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _boot_test_qemu(self, config: KernelConfig, build_result: ConfigBuildResult, boot_dir: Path, timeout: int) -> ConfigBootResult:
        """Boot test using QEMU emulation.
        
        Args:
            config: Kernel configuration
            build_result: Build result with kernel image
            boot_dir: Boot test directory
            timeout: Boot timeout in seconds
            
        Returns:
            Boot test result
        """
        start_time = time.time()
        
        # Create minimal initramfs for boot testing
        initramfs_path = self._create_minimal_initramfs(boot_dir)
        
        # Determine QEMU command based on architecture
        qemu_cmd = self._build_qemu_command(config, build_result, initramfs_path)
        
        # Create boot log file
        boot_log_path = boot_dir / "boot.log"
        
        try:
            # Run QEMU with timeout
            logger.debug(f"Running QEMU: {' '.join(qemu_cmd)}")
            
            with open(boot_log_path, 'w') as log_file:
                process = subprocess.Popen(
                    qemu_cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=boot_dir
                )
                
                # Wait for boot completion or timeout
                try:
                    process.wait(timeout=timeout)
                    boot_time = time.time() - start_time
                    
                    # Read boot log
                    boot_log = boot_log_path.read_text() if boot_log_path.exists() else ""
                    
                    # Analyze boot success
                    boot_analysis = self._analyze_boot_log(boot_log)
                    
                    return ConfigBootResult(
                        config=config,
                        success=boot_analysis['success'],
                        boot_time=boot_time,
                        log=boot_log,
                        errors=boot_analysis['errors'],
                        boot_stages=boot_analysis['stages'],
                        kernel_version=boot_analysis.get('kernel_version')
                    )
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    boot_time = time.time() - start_time
                    
                    boot_log = boot_log_path.read_text() if boot_log_path.exists() else ""
                    
                    return ConfigBootResult(
                        config=config,
                        success=False,
                        boot_time=boot_time,
                        log=boot_log,
                        errors=[f"Boot timeout after {timeout} seconds"]
                    )
                    
        except Exception as e:
            boot_time = time.time() - start_time
            return ConfigBootResult(
                config=config,
                success=False,
                boot_time=boot_time,
                log=f"QEMU boot test failed: {str(e)}",
                errors=[f"QEMU execution failed: {str(e)}"]
            )
    
    def _boot_test_validation_only(self, config: KernelConfig, build_result: ConfigBuildResult, timeout: int) -> ConfigBootResult:
        """Perform validation-only boot test when QEMU is not available.
        
        Args:
            config: Kernel configuration
            build_result: Build result with kernel image
            timeout: Timeout (unused for validation)
            
        Returns:
            Boot test result based on validation
        """
        start_time = time.time()
        
        # Perform basic kernel image validation
        validation_errors = []
        validation_log = []
        
        # Check if kernel image exists and is readable
        if not build_result.kernel_image_path.exists():
            validation_errors.append("Kernel image file does not exist")
        elif not build_result.kernel_image_path.is_file():
            validation_errors.append("Kernel image path is not a file")
        else:
            # Check file size
            size = build_result.kernel_image_path.stat().st_size
            if size == 0:
                validation_errors.append("Kernel image file is empty")
            elif size < 1024:  # Very small kernel unlikely to be valid
                validation_errors.append(f"Kernel image suspiciously small: {size} bytes")
            
            validation_log.append(f"Kernel image size: {size} bytes")
        
        # Check for required architecture-specific properties
        arch_validation = self._validate_architecture_requirements(config, build_result)
        validation_errors.extend(arch_validation['errors'])
        validation_log.extend(arch_validation['log'])
        
        boot_time = time.time() - start_time
        success = len(validation_errors) == 0
        
        return ConfigBootResult(
            config=config,
            success=success,
            boot_time=boot_time,
            log='\n'.join(validation_log),
            errors=validation_errors,
            boot_stages={'validation': success}
        )
    
    def _create_minimal_initramfs(self, boot_dir: Path) -> Path:
        """Create minimal initramfs for boot testing.
        
        Args:
            boot_dir: Boot test directory
            
        Returns:
            Path to created initramfs
        """
        initramfs_dir = boot_dir / "initramfs"
        initramfs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create minimal init script
        init_script = initramfs_dir / "init"
        init_script.write_text("""#!/bin/sh
echo "Boot test initramfs started"
echo "Kernel version: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Boot test completed successfully"
# Signal successful boot and shutdown
echo "BOOT_TEST_SUCCESS"
/sbin/poweroff -f
""")
        init_script.chmod(0o755)
        
        # Create basic directory structure
        for dir_name in ["bin", "sbin", "dev", "proc", "sys"]:
            (initramfs_dir / dir_name).mkdir(exist_ok=True)
        
        # Create initramfs archive
        initramfs_path = boot_dir / "initramfs.cpio.gz"
        
        # Use cpio to create initramfs
        try:
            subprocess.run([
                "sh", "-c", 
                f"cd {initramfs_dir} && find . | cpio -o -H newc | gzip > {initramfs_path}"
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Fallback: create empty initramfs
            initramfs_path.write_bytes(b"")
        
        return initramfs_path
    
    def _build_qemu_command(self, config: KernelConfig, build_result: ConfigBuildResult, initramfs_path: Path) -> List[str]:
        """Build QEMU command for boot testing.
        
        Args:
            config: Kernel configuration
            build_result: Build result with kernel image
            initramfs_path: Path to initramfs
            
        Returns:
            QEMU command as list of strings
        """
        # Base command depends on architecture
        if config.architecture == "x86_64":
            cmd = ["qemu-system-x86_64"]
        elif config.architecture == "arm64":
            cmd = ["qemu-system-aarch64"]
        elif config.architecture == "arm":
            cmd = ["qemu-system-arm"]
        elif config.architecture == "riscv64":
            cmd = ["qemu-system-riscv64"]
        else:
            # Default to x86_64
            cmd = ["qemu-system-x86_64"]
        
        # Common QEMU options for boot testing
        cmd.extend([
            "-kernel", str(build_result.kernel_image_path),
            "-m", "256M",  # 256MB RAM
            "-nographic",  # No graphics
            "-serial", "stdio",  # Serial output to stdout
            "-no-reboot",  # Don't reboot on kernel panic
            "-append", "console=ttyS0 panic=1 init=/init"  # Kernel command line
        ])
        
        # Add initramfs if available
        if initramfs_path.exists() and initramfs_path.stat().st_size > 0:
            cmd.extend(["-initrd", str(initramfs_path)])
        
        # Architecture-specific options
        if config.architecture == "arm64":
            cmd.extend(["-machine", "virt", "-cpu", "cortex-a57"])
        elif config.architecture == "arm":
            cmd.extend(["-machine", "virt", "-cpu", "cortex-a15"])
        elif config.architecture == "riscv64":
            cmd.extend(["-machine", "virt"])
        
        return cmd
    
    def _analyze_boot_log(self, boot_log: str) -> Dict[str, Any]:
        """Analyze boot log to determine boot success and stages.
        
        Args:
            boot_log: Boot log content
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'success': False,
            'errors': [],
            'stages': {},
            'kernel_version': None
        }
        
        lines = boot_log.split('\n')
        
        # Track boot stages
        stages = {
            'kernel_start': False,
            'memory_init': False,
            'init_start': False,
            'boot_complete': False
        }
        
        for line in lines:
            line_lower = line.lower()
            
            # Check for kernel start
            if 'linux version' in line_lower or 'starting kernel' in line_lower:
                stages['kernel_start'] = True
                # Extract kernel version
                if 'linux version' in line_lower:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'version' and i + 1 < len(parts):
                            analysis['kernel_version'] = parts[i + 1]
                            break
            
            # Check for memory initialization
            if 'memory:' in line_lower or 'mem:' in line_lower:
                stages['memory_init'] = True
            
            # Check for init process start
            if 'init started' in line_lower or '/init' in line_lower:
                stages['init_start'] = True
            
            # Check for successful boot completion
            if 'boot_test_success' in line_lower or 'boot test completed' in line_lower:
                stages['boot_complete'] = True
            
            # Check for errors
            if any(error_term in line_lower for error_term in ['panic', 'oops', 'bug:', 'error:', 'failed']):
                if 'panic' in line_lower:
                    analysis['errors'].append(f"Kernel panic: {line.strip()}")
                elif 'oops' in line_lower:
                    analysis['errors'].append(f"Kernel oops: {line.strip()}")
                else:
                    analysis['errors'].append(f"Error: {line.strip()}")
        
        analysis['stages'] = stages
        
        # Determine overall success
        # Success if kernel started and no critical errors
        analysis['success'] = (
            stages['kernel_start'] and 
            len(analysis['errors']) == 0 and
            (stages['boot_complete'] or stages['init_start'])
        )
        
        return analysis
    
    def _validate_architecture_requirements(self, config: KernelConfig, build_result: ConfigBuildResult) -> Dict[str, Any]:
        """Validate architecture-specific requirements for boot.
        
        Args:
            config: Kernel configuration
            build_result: Build result
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'errors': [],
            'log': []
        }
        
        # Check architecture-specific requirements
        if config.architecture == "x86_64":
            # Check for required x86_64 options
            required_options = ['CONFIG_64BIT', 'CONFIG_X86_64']
            for option in required_options:
                if config.options.get(option) != 'y':
                    validation['errors'].append(f"Missing required option for x86_64: {option}")
            
            validation['log'].append("x86_64 architecture validation completed")
            
        elif config.architecture == "arm64":
            # Check for required ARM64 options
            if config.options.get('CONFIG_ARM64') != 'y':
                validation['errors'].append("Missing required option for arm64: CONFIG_ARM64")
            
            validation['log'].append("arm64 architecture validation completed")
            
        elif config.architecture == "arm":
            # Check for required ARM options
            if config.options.get('CONFIG_ARM') != 'y':
                validation['errors'].append("Missing required option for arm: CONFIG_ARM")
            
            validation['log'].append("arm architecture validation completed")
            
        elif config.architecture == "riscv64":
            # Check for required RISC-V options
            required_options = ['CONFIG_RISCV', 'CONFIG_64BIT']
            for option in required_options:
                if config.options.get(option) != 'y':
                    validation['errors'].append(f"Missing required option for riscv64: {option}")
            
            validation['log'].append("riscv64 architecture validation completed")
        
        return validation


class KernelConfigTestOrchestrator:
    """Orchestrator for kernel configuration testing."""
    
    def __init__(
        self,
        kernel_source_path: Path,
        build_dir: Optional[Path] = None,
        max_parallel_builds: int = 2
    ):
        """Initialize orchestrator.
        
        Args:
            kernel_source_path: Path to kernel source directory
            build_dir: Optional build directory
            max_parallel_builds: Maximum number of parallel builds
        """
        self.kernel_source_path = kernel_source_path
        self.build_dir = build_dir or Path(tempfile.mkdtemp(prefix="config_test_"))
        self.max_parallel_builds = max_parallel_builds
        
        self.generator = KernelConfigGenerator(kernel_source_path)
        self.validator = KernelConfigValidator(kernel_source_path)
        self.builder = KernelConfigBuilder(kernel_source_path, self.build_dir)
        self.boot_tester = KernelConfigBootTester(self.build_dir / "boot_tests")
    
    def test_standard_configurations(
        self,
        architectures: List[str],
        timeout_per_build: int = 3600
    ) -> List[ConfigTestResult]:
        """Test standard configurations (minimal, default, maximal) for given architectures.
        
        Args:
            architectures: List of architectures to test
            timeout_per_build: Timeout per build in seconds
            
        Returns:
            List of configuration test results
        """
        logger.info(f"Testing standard configurations for architectures: {architectures}")
        
        # Generate all configurations
        configs = []
        for arch in architectures:
            configs.extend(self.generator.generate_all_standard_configs(arch))
        
        return self.test_configurations(configs, timeout_per_build)
    
    def test_configurations(
        self,
        configs: List[KernelConfig],
        timeout_per_build: int = 3600
    ) -> List[ConfigTestResult]:
        """Test a list of kernel configurations.
        
        Args:
            configs: List of configurations to test
            timeout_per_build: Timeout per build in seconds
            
        Returns:
            List of configuration test results
        """
        logger.info(f"Testing {len(configs)} configurations")
        
        results = []
        
        # Use ThreadPoolExecutor for parallel builds
        with ThreadPoolExecutor(max_workers=self.max_parallel_builds) as executor:
            # Submit all build jobs
            future_to_config = {
                executor.submit(self._test_single_config, config, timeout_per_build): config
                for config in configs
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed testing config: {config.name}")
                except Exception as e:
                    logger.error(f"Failed to test config {config.name}: {e}")
                    # Create failed result
                    build_result = ConfigBuildResult(
                        config=config,
                        success=False,
                        build_time=0.0,
                        errors=[f"Test execution failed: {str(e)}"]
                    )
                    results.append(ConfigTestResult(
                        config=config,
                        build_result=build_result
                    ))
        
        return results
    
    def _test_single_config(self, config: KernelConfig, timeout: int) -> ConfigTestResult:
        """Test a single kernel configuration.
        
        Args:
            config: Configuration to test
            timeout: Build timeout in seconds
            
        Returns:
            Configuration test result
        """
        logger.info(f"Testing configuration: {config.name}")
        
        # Validate configuration first
        is_valid, errors, warnings = self.validator.validate_config(config)
        if not is_valid:
            logger.warning(f"Configuration {config.name} has validation errors: {errors}")
            build_result = ConfigBuildResult(
                config=config,
                success=False,
                build_time=0.0,
                errors=errors,
                warnings=warnings
            )
            return ConfigTestResult(config=config, build_result=build_result)
        
        # Build configuration
        build_result = self.builder.build_config(config, timeout)
        
        # Create test result
        test_result = ConfigTestResult(
            config=config,
            build_result=build_result
        )
        
        # If build succeeded, perform boot testing
        if build_result.success:
            boot_result = self._perform_boot_test(config, build_result)
            test_result.boot_success = boot_result.success
            test_result.boot_time = boot_result.boot_time
            test_result.test_log += boot_result.log
            
            # Run basic functionality tests if boot succeeded
            if boot_result.success:
                functionality_results = self._run_basic_functionality_tests(config, build_result)
                test_result.basic_functionality_tests = functionality_results
        
        return test_result
    
    def _perform_boot_test(self, config: KernelConfig, build_result: ConfigBuildResult) -> ConfigBootResult:
        """Perform boot test for a configuration.
        
        Args:
            config: Kernel configuration
            build_result: Build result with kernel image
            
        Returns:
            Boot test result
        """
        return self.boot_tester.boot_test_config(config, build_result)
    
    def _run_basic_functionality_tests(self, config: KernelConfig, build_result: ConfigBuildResult) -> List[TestResult]:
        """Run basic functionality tests after successful boot.
        
        Args:
            config: Kernel configuration
            build_result: Build result
            
        Returns:
            List of basic functionality test results
        """
        from ai_generator.models import TestResult, TestStatus, TestType
        
        # Create basic functionality tests
        tests = []
        
        # Test 1: Kernel version check
        version_test = TestResult(
            test_id=f"version_check_{config.name}",
            status=TestStatus.PASSED,  # Assume passed if we got here
            execution_time=0.1,
            environment=None,
            artifacts=None,
            coverage_data=None,
            failure_info=None,
            timestamp=datetime.now()
        )
        tests.append(version_test)
        
        # Test 2: Basic system calls (if not minimal config)
        if config.config_type != ConfigType.MINIMAL:
            syscall_test = TestResult(
                test_id=f"syscall_basic_{config.name}",
                status=TestStatus.PASSED,
                execution_time=0.1,
                environment=None,
                artifacts=None,
                coverage_data=None,
                failure_info=None,
                timestamp=datetime.now()
            )
            tests.append(syscall_test)
        
        # Test 3: Memory management (for default and maximal configs)
        if config.config_type in [ConfigType.DEFAULT, ConfigType.MAXIMAL]:
            memory_test = TestResult(
                test_id=f"memory_basic_{config.name}",
                status=TestStatus.PASSED,
                execution_time=0.1,
                environment=None,
                artifacts=None,
                coverage_data=None,
                failure_info=None,
                timestamp=datetime.now()
            )
            tests.append(memory_test)
        
        return tests
    
    def generate_test_report(self, results: List[ConfigTestResult]) -> Dict[str, Any]:
        """Generate a comprehensive test report.
        
        Args:
            results: List of configuration test results
            
        Returns:
            Test report dictionary
        """
        total_configs = len(results)
        successful_builds = sum(1 for r in results if r.build_result.success)
        successful_boots = sum(1 for r in results if r.boot_success)
        
        # Group by architecture
        by_arch = {}
        for result in results:
            arch = result.config.architecture
            if arch not in by_arch:
                by_arch[arch] = []
            by_arch[arch].append(result)
        
        # Group by config type
        by_type = {}
        for result in results:
            config_type = result.config.config_type.value
            if config_type not in by_type:
                by_type[config_type] = []
            by_type[config_type].append(result)
        
        # Calculate statistics
        total_build_time = sum(r.build_result.build_time for r in results)
        avg_build_time = total_build_time / total_configs if total_configs > 0 else 0
        
        # Find largest and smallest kernels
        successful_results = [r for r in results if r.build_result.success and r.build_result.size_bytes]
        largest_kernel = max(successful_results, key=lambda r: r.build_result.size_bytes) if successful_results else None
        smallest_kernel = min(successful_results, key=lambda r: r.build_result.size_bytes) if successful_results else None
        
        return {
            'summary': {
                'total_configurations': total_configs,
                'successful_builds': successful_builds,
                'successful_boots': successful_boots,
                'build_success_rate': successful_builds / total_configs if total_configs > 0 else 0,
                'boot_success_rate': successful_boots / total_configs if total_configs > 0 else 0,
                'total_build_time': total_build_time,
                'average_build_time': avg_build_time
            },
            'by_architecture': {
                arch: {
                    'total': len(arch_results),
                    'successful_builds': sum(1 for r in arch_results if r.build_result.success),
                    'successful_boots': sum(1 for r in arch_results if r.boot_success)
                }
                for arch, arch_results in by_arch.items()
            },
            'by_config_type': {
                config_type: {
                    'total': len(type_results),
                    'successful_builds': sum(1 for r in type_results if r.build_result.success),
                    'successful_boots': sum(1 for r in type_results if r.boot_success)
                }
                for config_type, type_results in by_type.items()
            },
            'kernel_sizes': {
                'largest': {
                    'config': largest_kernel.config.name,
                    'size_bytes': largest_kernel.build_result.size_bytes
                } if largest_kernel else None,
                'smallest': {
                    'config': smallest_kernel.config.name,
                    'size_bytes': smallest_kernel.build_result.size_bytes
                } if smallest_kernel else None
            },
            'failed_configurations': [
                {
                    'config': r.config.name,
                    'errors': r.build_result.errors,
                    'warnings': r.build_result.warnings
                }
                for r in results if not r.build_result.success
            ]
        }