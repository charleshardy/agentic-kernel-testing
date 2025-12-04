"""Hardware configuration management for test execution.

This module provides functionality for:
- Parsing and validating hardware configurations
- Generating test matrices for multi-hardware testing
- Detecting hardware capabilities
- Classifying virtual vs physical hardware
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import json
from pathlib import Path

from ai_generator.models import HardwareConfig, Peripheral


@dataclass
class HardwareCapability:
    """Represents a hardware capability."""
    name: str
    available: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestMatrix:
    """Test matrix containing all hardware configurations to test."""
    configurations: List[HardwareConfig]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Return number of configurations in matrix."""
        return len(self.configurations)
    
    def get_by_architecture(self, arch: str) -> List[HardwareConfig]:
        """Get all configurations for a specific architecture."""
        return [cfg for cfg in self.configurations if cfg.architecture == arch]
    
    def get_virtual_configs(self) -> List[HardwareConfig]:
        """Get all virtual hardware configurations."""
        return [cfg for cfg in self.configurations if cfg.is_virtual]
    
    def get_physical_configs(self) -> List[HardwareConfig]:
        """Get all physical hardware configurations."""
        return [cfg for cfg in self.configurations if not cfg.is_virtual]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'configurations': [cfg.to_dict() for cfg in self.configurations],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestMatrix':
        """Create from dictionary."""
        configs = [HardwareConfig.from_dict(cfg) for cfg in data.get('configurations', [])]
        metadata = data.get('metadata', {})
        return cls(configurations=configs, metadata=metadata)


class HardwareConfigParser:
    """Parser for hardware configuration files and data."""
    
    SUPPORTED_ARCHITECTURES = {"x86_64", "arm64", "riscv64", "arm"}
    SUPPORTED_EMULATORS = {"qemu", "kvm", "bochs"}
    SUPPORTED_STORAGE_TYPES = {"ssd", "hdd", "nvme", "emmc", "sd"}
    
    @staticmethod
    def parse_config(config_data: Dict[str, Any]) -> HardwareConfig:
        """Parse and validate a hardware configuration from dictionary.
        
        Args:
            config_data: Dictionary containing hardware configuration
            
        Returns:
            Validated HardwareConfig instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate required fields
        if 'architecture' not in config_data:
            raise ValueError("Hardware configuration must specify 'architecture'")
        if 'cpu_model' not in config_data:
            raise ValueError("Hardware configuration must specify 'cpu_model'")
        if 'memory_mb' not in config_data:
            raise ValueError("Hardware configuration must specify 'memory_mb'")
        
        # Validate architecture
        arch = config_data['architecture']
        if arch not in HardwareConfigParser.SUPPORTED_ARCHITECTURES:
            raise ValueError(
                f"Unsupported architecture '{arch}'. "
                f"Supported: {HardwareConfigParser.SUPPORTED_ARCHITECTURES}"
            )
        
        # Validate memory
        memory_mb = config_data['memory_mb']
        if not isinstance(memory_mb, int) or memory_mb <= 0:
            raise ValueError(f"memory_mb must be a positive integer, got: {memory_mb}")
        
        # Validate storage type if provided
        storage_type = config_data.get('storage_type', 'ssd')
        if storage_type not in HardwareConfigParser.SUPPORTED_STORAGE_TYPES:
            raise ValueError(
                f"Unsupported storage type '{storage_type}'. "
                f"Supported: {HardwareConfigParser.SUPPORTED_STORAGE_TYPES}"
            )
        
        # Validate emulator if virtual
        is_virtual = config_data.get('is_virtual', True)
        emulator = config_data.get('emulator')
        if is_virtual and emulator and emulator not in HardwareConfigParser.SUPPORTED_EMULATORS:
            raise ValueError(
                f"Unsupported emulator '{emulator}'. "
                f"Supported: {HardwareConfigParser.SUPPORTED_EMULATORS}"
            )
        
        # Parse peripherals
        peripherals_data = config_data.get('peripherals', [])
        peripherals = []
        for p_data in peripherals_data:
            if isinstance(p_data, dict):
                if 'name' not in p_data or 'type' not in p_data:
                    raise ValueError("Peripheral must have 'name' and 'type' fields")
                peripherals.append(Peripheral.from_dict(p_data))
            elif isinstance(p_data, Peripheral):
                peripherals.append(p_data)
            else:
                raise ValueError(f"Invalid peripheral data: {p_data}")
        
        # Create HardwareConfig
        return HardwareConfig(
            architecture=arch,
            cpu_model=config_data['cpu_model'],
            memory_mb=memory_mb,
            storage_type=storage_type,
            peripherals=peripherals,
            is_virtual=is_virtual,
            emulator=emulator
        )
    
    @staticmethod
    def parse_config_file(file_path: Path) -> HardwareConfig:
        """Parse hardware configuration from JSON file.
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            Validated HardwareConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If configuration is invalid
            json.JSONDecodeError: If file is not valid JSON
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        return HardwareConfigParser.parse_config(config_data)
    
    @staticmethod
    def validate_config(config: HardwareConfig) -> List[str]:
        """Validate a hardware configuration and return list of warnings.
        
        Args:
            config: Hardware configuration to validate
            
        Returns:
            List of warning messages (empty if no warnings)
        """
        warnings = []
        
        # Check memory size
        if config.memory_mb < 512:
            warnings.append(f"Low memory: {config.memory_mb}MB may be insufficient for kernel testing")
        elif config.memory_mb > 32768:
            warnings.append(f"High memory: {config.memory_mb}MB may be excessive")
        
        # Check virtual/emulator consistency
        if config.is_virtual and not config.emulator:
            warnings.append("Virtual configuration should specify an emulator")
        if not config.is_virtual and config.emulator:
            warnings.append("Physical configuration should not specify an emulator")
        
        # Check architecture-specific issues
        if config.architecture == "riscv64" and config.emulator == "kvm":
            warnings.append("KVM may not be available for RISC-V architecture")
        
        return warnings


class TestMatrixGenerator:
    """Generator for test matrices covering multiple hardware configurations."""
    
    @staticmethod
    def generate_matrix(
        architectures: List[str],
        memory_sizes: List[int],
        virtual_only: bool = False,
        include_peripherals: bool = False
    ) -> TestMatrix:
        """Generate a test matrix from architecture and memory combinations.
        
        Args:
            architectures: List of architectures to test
            memory_sizes: List of memory sizes in MB
            virtual_only: If True, only generate virtual configurations
            include_peripherals: If True, include common peripherals
            
        Returns:
            TestMatrix with all combinations
        """
        configurations = []
        
        for arch in architectures:
            for memory_mb in memory_sizes:
                # Determine CPU model based on architecture
                cpu_model = TestMatrixGenerator._get_default_cpu_model(arch)
                
                # Create virtual configuration
                peripherals = []
                if include_peripherals:
                    peripherals = TestMatrixGenerator._get_default_peripherals(arch)
                
                virtual_config = HardwareConfig(
                    architecture=arch,
                    cpu_model=cpu_model,
                    memory_mb=memory_mb,
                    storage_type="ssd",
                    peripherals=peripherals.copy(),
                    is_virtual=True,
                    emulator="qemu"
                )
                configurations.append(virtual_config)
                
                # Create physical configuration if requested
                if not virtual_only:
                    physical_config = HardwareConfig(
                        architecture=arch,
                        cpu_model=cpu_model,
                        memory_mb=memory_mb,
                        storage_type="emmc" if arch in ["arm", "arm64"] else "ssd",
                        peripherals=peripherals.copy(),
                        is_virtual=False,
                        emulator=None
                    )
                    configurations.append(physical_config)
        
        return TestMatrix(
            configurations=configurations,
            metadata={
                'architectures': architectures,
                'memory_sizes': memory_sizes,
                'virtual_only': virtual_only,
                'include_peripherals': include_peripherals
            }
        )
    
    @staticmethod
    def generate_from_configs(configs: List[HardwareConfig]) -> TestMatrix:
        """Generate a test matrix from a list of hardware configurations.
        
        Args:
            configs: List of hardware configurations
            
        Returns:
            TestMatrix containing the configurations
        """
        return TestMatrix(configurations=configs)
    
    @staticmethod
    def load_matrix_from_file(file_path: Path) -> TestMatrix:
        """Load test matrix from JSON file.
        
        Args:
            file_path: Path to JSON file containing test matrix
            
        Returns:
            TestMatrix instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Matrix file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return TestMatrix.from_dict(data)
    
    @staticmethod
    def _get_default_cpu_model(architecture: str) -> str:
        """Get default CPU model for architecture."""
        cpu_models = {
            'x86_64': 'Intel Core i7',
            'arm64': 'ARM Cortex-A72',
            'arm': 'ARM Cortex-A53',
            'riscv64': 'SiFive U74'
        }
        return cpu_models.get(architecture, 'Generic')
    
    @staticmethod
    def _get_default_peripherals(architecture: str) -> List[Peripheral]:
        """Get default peripherals for architecture."""
        common_peripherals = [
            Peripheral(name="eth0", type="network", model="virtio-net"),
            Peripheral(name="disk0", type="storage", model="virtio-blk")
        ]
        
        if architecture in ["arm", "arm64"]:
            common_peripherals.append(
                Peripheral(name="uart0", type="serial", model="pl011")
            )
        
        return common_peripherals


class HardwareCapabilityDetector:
    """Detector for hardware capabilities and features."""
    
    @staticmethod
    def detect_capabilities(config: HardwareConfig) -> List[HardwareCapability]:
        """Detect capabilities of a hardware configuration.
        
        Args:
            config: Hardware configuration to analyze
            
        Returns:
            List of detected capabilities
        """
        capabilities = []
        
        # Virtualization capability
        if config.is_virtual:
            capabilities.append(HardwareCapability(
                name="virtualization",
                available=True,
                details={'emulator': config.emulator}
            ))
        
        # Architecture-specific capabilities
        arch_caps = HardwareCapabilityDetector._detect_architecture_capabilities(config.architecture)
        capabilities.extend(arch_caps)
        
        # Memory capabilities
        if config.memory_mb >= 4096:
            capabilities.append(HardwareCapability(
                name="large_memory",
                available=True,
                details={'memory_mb': config.memory_mb}
            ))
        
        # Storage capabilities
        if config.storage_type in ["nvme", "ssd"]:
            capabilities.append(HardwareCapability(
                name="fast_storage",
                available=True,
                details={'storage_type': config.storage_type}
            ))
        
        # Peripheral capabilities
        for peripheral in config.peripherals:
            capabilities.append(HardwareCapability(
                name=f"peripheral_{peripheral.type}",
                available=True,
                details={'peripheral': peripheral.name, 'model': peripheral.model}
            ))
        
        return capabilities
    
    @staticmethod
    def _detect_architecture_capabilities(architecture: str) -> List[HardwareCapability]:
        """Detect architecture-specific capabilities."""
        capabilities = []
        
        if architecture == "x86_64":
            capabilities.extend([
                HardwareCapability(name="64bit", available=True, details={}),
                HardwareCapability(name="sse", available=True, details={}),
                HardwareCapability(name="avx", available=True, details={})
            ])
        elif architecture in ["arm64", "arm"]:
            capabilities.extend([
                HardwareCapability(name="arm", available=True, details={}),
                HardwareCapability(name="neon", available=True, details={})
            ])
            if architecture == "arm64":
                capabilities.append(
                    HardwareCapability(name="64bit", available=True, details={})
                )
        elif architecture == "riscv64":
            capabilities.extend([
                HardwareCapability(name="64bit", available=True, details={}),
                HardwareCapability(name="riscv", available=True, details={})
            ])
        
        return capabilities
    
    @staticmethod
    def supports_feature(config: HardwareConfig, feature: str) -> bool:
        """Check if hardware configuration supports a specific feature.
        
        Args:
            config: Hardware configuration
            feature: Feature name to check
            
        Returns:
            True if feature is supported
        """
        capabilities = HardwareCapabilityDetector.detect_capabilities(config)
        return any(cap.name == feature and cap.available for cap in capabilities)


class HardwareClassifier:
    """Classifier for hardware configurations (virtual vs physical)."""
    
    @staticmethod
    def classify(config: HardwareConfig) -> str:
        """Classify hardware configuration as virtual or physical.
        
        Args:
            config: Hardware configuration to classify
            
        Returns:
            'virtual' or 'physical'
        """
        return 'virtual' if config.is_virtual else 'physical'
    
    @staticmethod
    def is_virtual(config: HardwareConfig) -> bool:
        """Check if configuration is virtual.
        
        Args:
            config: Hardware configuration
            
        Returns:
            True if virtual
        """
        return config.is_virtual
    
    @staticmethod
    def is_physical(config: HardwareConfig) -> bool:
        """Check if configuration is physical.
        
        Args:
            config: Hardware configuration
            
        Returns:
            True if physical
        """
        return not config.is_virtual
    
    @staticmethod
    def prefer_virtual(
        configs: List[HardwareConfig],
        architecture: Optional[str] = None
    ) -> List[HardwareConfig]:
        """Sort configurations to prefer virtual over physical.
        
        This implements the requirement that virtual environments should be
        used before physical hardware when both are available.
        
        Args:
            configs: List of hardware configurations
            architecture: Optional architecture filter
            
        Returns:
            Sorted list with virtual configs first
        """
        filtered = configs
        if architecture:
            filtered = [c for c in configs if c.architecture == architecture]
        
        # Sort: virtual first, then by architecture, then by memory
        return sorted(
            filtered,
            key=lambda c: (
                0 if c.is_virtual else 1,  # Virtual first
                c.architecture,
                -c.memory_mb  # Larger memory first
            )
        )
    
    @staticmethod
    def get_equivalent_configs(
        config: HardwareConfig,
        all_configs: List[HardwareConfig]
    ) -> List[HardwareConfig]:
        """Find equivalent configurations (same arch/memory, different virtual/physical).
        
        Args:
            config: Reference configuration
            all_configs: List of all available configurations
            
        Returns:
            List of equivalent configurations
        """
        return [
            c for c in all_configs
            if c.architecture == config.architecture
            and c.memory_mb == config.memory_mb
            and c != config
        ]
