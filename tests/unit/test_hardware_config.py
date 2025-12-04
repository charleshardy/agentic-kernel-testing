"""Unit tests for hardware configuration management."""

import pytest
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from ai_generator.models import HardwareConfig, Peripheral
from execution.hardware_config import (
    HardwareConfigParser,
    TestMatrixGenerator,
    HardwareCapabilityDetector,
    HardwareClassifier,
    TestMatrix,
    HardwareCapability
)


class TestHardwareConfigParser:
    """Tests for HardwareConfigParser."""
    
    def test_parse_valid_config(self):
        """Test parsing a valid hardware configuration."""
        config_data = {
            'architecture': 'x86_64',
            'cpu_model': 'Intel Core i7',
            'memory_mb': 4096,
            'storage_type': 'ssd',
            'is_virtual': True,
            'emulator': 'qemu'
        }
        
        config = HardwareConfigParser.parse_config(config_data)
        
        assert config.architecture == 'x86_64'
        assert config.cpu_model == 'Intel Core i7'
        assert config.memory_mb == 4096
        assert config.storage_type == 'ssd'
        assert config.is_virtual is True
        assert config.emulator == 'qemu'
    
    def test_parse_config_with_peripherals(self):
        """Test parsing configuration with peripherals."""
        config_data = {
            'architecture': 'arm64',
            'cpu_model': 'ARM Cortex-A72',
            'memory_mb': 2048,
            'peripherals': [
                {'name': 'eth0', 'type': 'network', 'model': 'virtio-net'},
                {'name': 'uart0', 'type': 'serial', 'model': 'pl011'}
            ]
        }
        
        config = HardwareConfigParser.parse_config(config_data)
        
        assert len(config.peripherals) == 2
        assert config.peripherals[0].name == 'eth0'
        assert config.peripherals[1].type == 'serial'
    
    def test_parse_config_missing_architecture(self):
        """Test parsing fails when architecture is missing."""
        config_data = {
            'cpu_model': 'Intel Core i7',
            'memory_mb': 4096
        }
        
        with pytest.raises(ValueError, match="must specify 'architecture'"):
            HardwareConfigParser.parse_config(config_data)
    
    def test_parse_config_missing_cpu_model(self):
        """Test parsing fails when cpu_model is missing."""
        config_data = {
            'architecture': 'x86_64',
            'memory_mb': 4096
        }
        
        with pytest.raises(ValueError, match="must specify 'cpu_model'"):
            HardwareConfigParser.parse_config(config_data)
    
    def test_parse_config_missing_memory(self):
        """Test parsing fails when memory_mb is missing."""
        config_data = {
            'architecture': 'x86_64',
            'cpu_model': 'Intel Core i7'
        }
        
        with pytest.raises(ValueError, match="must specify 'memory_mb'"):
            HardwareConfigParser.parse_config(config_data)
    
    def test_parse_config_invalid_architecture(self):
        """Test parsing fails with unsupported architecture."""
        config_data = {
            'architecture': 'mips',
            'cpu_model': 'MIPS R4000',
            'memory_mb': 2048
        }
        
        with pytest.raises(ValueError, match="Unsupported architecture"):
            HardwareConfigParser.parse_config(config_data)
    
    def test_parse_config_invalid_memory(self):
        """Test parsing fails with invalid memory value."""
        config_data = {
            'architecture': 'x86_64',
            'cpu_model': 'Intel Core i7',
            'memory_mb': -1024
        }
        
        with pytest.raises(ValueError, match="must be a positive integer"):
            HardwareConfigParser.parse_config(config_data)
    
    def test_parse_config_invalid_storage_type(self):
        """Test parsing fails with unsupported storage type."""
        config_data = {
            'architecture': 'x86_64',
            'cpu_model': 'Intel Core i7',
            'memory_mb': 4096,
            'storage_type': 'tape'
        }
        
        with pytest.raises(ValueError, match="Unsupported storage type"):
            HardwareConfigParser.parse_config(config_data)
    
    def test_parse_config_invalid_emulator(self):
        """Test parsing fails with unsupported emulator."""
        config_data = {
            'architecture': 'x86_64',
            'cpu_model': 'Intel Core i7',
            'memory_mb': 4096,
            'is_virtual': True,
            'emulator': 'virtualbox'
        }
        
        with pytest.raises(ValueError, match="Unsupported emulator"):
            HardwareConfigParser.parse_config(config_data)
    
    def test_parse_config_file(self):
        """Test parsing configuration from file."""
        config_data = {
            'architecture': 'arm64',
            'cpu_model': 'ARM Cortex-A72',
            'memory_mb': 2048
        }
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)
        
        try:
            config = HardwareConfigParser.parse_config_file(temp_path)
            assert config.architecture == 'arm64'
            assert config.memory_mb == 2048
        finally:
            temp_path.unlink()
    
    def test_parse_config_file_not_found(self):
        """Test parsing fails when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            HardwareConfigParser.parse_config_file(Path('/nonexistent/config.json'))
    
    def test_validate_config_low_memory_warning(self):
        """Test validation warns about low memory."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=256
        )
        
        warnings = HardwareConfigParser.validate_config(config)
        
        assert len(warnings) > 0
        assert any('Low memory' in w for w in warnings)
    
    def test_validate_config_high_memory_warning(self):
        """Test validation warns about excessive memory."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=65536
        )
        
        warnings = HardwareConfigParser.validate_config(config)
        
        assert len(warnings) > 0
        assert any('High memory' in w for w in warnings)
    
    def test_validate_config_no_warnings(self):
        """Test validation passes with reasonable config."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=4096,
            is_virtual=True,
            emulator='qemu'
        )
        
        warnings = HardwareConfigParser.validate_config(config)
        
        assert len(warnings) == 0


class TestTestMatrixGenerator:
    """Tests for TestMatrixGenerator."""
    
    def test_generate_matrix_single_arch(self):
        """Test generating matrix for single architecture."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['x86_64'],
            memory_sizes=[2048, 4096],
            virtual_only=True
        )
        
        assert len(matrix) == 2
        assert all(c.architecture == 'x86_64' for c in matrix.configurations)
        assert all(c.is_virtual for c in matrix.configurations)
    
    def test_generate_matrix_multiple_archs(self):
        """Test generating matrix for multiple architectures."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['x86_64', 'arm64'],
            memory_sizes=[2048],
            virtual_only=True
        )
        
        assert len(matrix) == 2
        archs = {c.architecture for c in matrix.configurations}
        assert archs == {'x86_64', 'arm64'}
    
    def test_generate_matrix_with_physical(self):
        """Test generating matrix with physical configurations."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['x86_64'],
            memory_sizes=[4096],
            virtual_only=False
        )
        
        assert len(matrix) == 2
        assert sum(c.is_virtual for c in matrix.configurations) == 1
        assert sum(not c.is_virtual for c in matrix.configurations) == 1
    
    def test_generate_matrix_with_peripherals(self):
        """Test generating matrix with peripherals."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['arm64'],
            memory_sizes=[2048],
            virtual_only=True,
            include_peripherals=True
        )
        
        assert len(matrix) == 1
        assert len(matrix.configurations[0].peripherals) > 0
    
    def test_generate_from_configs(self):
        """Test generating matrix from existing configs."""
        configs = [
            HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048),
            HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=4096)
        ]
        
        matrix = TestMatrixGenerator.generate_from_configs(configs)
        
        assert len(matrix) == 2
        assert matrix.configurations == configs
    
    def test_matrix_get_by_architecture(self):
        """Test filtering matrix by architecture."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['x86_64', 'arm64'],
            memory_sizes=[2048],
            virtual_only=True
        )
        
        x86_configs = matrix.get_by_architecture('x86_64')
        
        assert len(x86_configs) == 1
        assert x86_configs[0].architecture == 'x86_64'
    
    def test_matrix_get_virtual_configs(self):
        """Test getting virtual configurations from matrix."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['x86_64'],
            memory_sizes=[2048],
            virtual_only=False
        )
        
        virtual_configs = matrix.get_virtual_configs()
        
        assert len(virtual_configs) == 1
        assert all(c.is_virtual for c in virtual_configs)
    
    def test_matrix_get_physical_configs(self):
        """Test getting physical configurations from matrix."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['x86_64'],
            memory_sizes=[2048],
            virtual_only=False
        )
        
        physical_configs = matrix.get_physical_configs()
        
        assert len(physical_configs) == 1
        assert all(not c.is_virtual for c in physical_configs)
    
    def test_matrix_serialization(self):
        """Test matrix serialization and deserialization."""
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=['x86_64'],
            memory_sizes=[2048],
            virtual_only=True
        )
        
        matrix_dict = matrix.to_dict()
        restored_matrix = TestMatrix.from_dict(matrix_dict)
        
        assert len(restored_matrix) == len(matrix)
        assert restored_matrix.configurations[0].architecture == matrix.configurations[0].architecture


class TestHardwareCapabilityDetector:
    """Tests for HardwareCapabilityDetector."""
    
    def test_detect_virtualization_capability(self):
        """Test detecting virtualization capability."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=4096,
            is_virtual=True,
            emulator='qemu'
        )
        
        capabilities = HardwareCapabilityDetector.detect_capabilities(config)
        
        virt_caps = [c for c in capabilities if c.name == 'virtualization']
        assert len(virt_caps) == 1
        assert virt_caps[0].available is True
    
    def test_detect_x86_64_capabilities(self):
        """Test detecting x86_64 specific capabilities."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=4096
        )
        
        capabilities = HardwareCapabilityDetector.detect_capabilities(config)
        
        cap_names = {c.name for c in capabilities}
        assert '64bit' in cap_names
        assert 'sse' in cap_names
        assert 'avx' in cap_names
    
    def test_detect_arm64_capabilities(self):
        """Test detecting ARM64 specific capabilities."""
        config = HardwareConfig(
            architecture='arm64',
            cpu_model='ARM Cortex-A72',
            memory_mb=2048
        )
        
        capabilities = HardwareCapabilityDetector.detect_capabilities(config)
        
        cap_names = {c.name for c in capabilities}
        assert '64bit' in cap_names
        assert 'arm' in cap_names
        assert 'neon' in cap_names
    
    def test_detect_large_memory_capability(self):
        """Test detecting large memory capability."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=8192
        )
        
        capabilities = HardwareCapabilityDetector.detect_capabilities(config)
        
        large_mem_caps = [c for c in capabilities if c.name == 'large_memory']
        assert len(large_mem_caps) == 1
        assert large_mem_caps[0].available is True
    
    def test_detect_fast_storage_capability(self):
        """Test detecting fast storage capability."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=4096,
            storage_type='nvme'
        )
        
        capabilities = HardwareCapabilityDetector.detect_capabilities(config)
        
        storage_caps = [c for c in capabilities if c.name == 'fast_storage']
        assert len(storage_caps) == 1
        assert storage_caps[0].available is True
    
    def test_detect_peripheral_capabilities(self):
        """Test detecting peripheral capabilities."""
        config = HardwareConfig(
            architecture='arm64',
            cpu_model='ARM Cortex-A72',
            memory_mb=2048,
            peripherals=[
                Peripheral(name='eth0', type='network'),
                Peripheral(name='uart0', type='serial')
            ]
        )
        
        capabilities = HardwareCapabilityDetector.detect_capabilities(config)
        
        cap_names = {c.name for c in capabilities}
        assert 'peripheral_network' in cap_names
        assert 'peripheral_serial' in cap_names
    
    def test_supports_feature(self):
        """Test checking if config supports specific feature."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=4096
        )
        
        assert HardwareCapabilityDetector.supports_feature(config, '64bit') is True
        assert HardwareCapabilityDetector.supports_feature(config, 'nonexistent') is False


class TestHardwareClassifier:
    """Tests for HardwareClassifier."""
    
    def test_classify_virtual(self):
        """Test classifying virtual hardware."""
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel Core i7',
            memory_mb=4096,
            is_virtual=True
        )
        
        classification = HardwareClassifier.classify(config)
        
        assert classification == 'virtual'
    
    def test_classify_physical(self):
        """Test classifying physical hardware."""
        config = HardwareConfig(
            architecture='arm64',
            cpu_model='ARM Cortex-A72',
            memory_mb=2048,
            is_virtual=False
        )
        
        classification = HardwareClassifier.classify(config)
        
        assert classification == 'physical'
    
    def test_is_virtual(self):
        """Test checking if config is virtual."""
        virtual_config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel',
            memory_mb=4096,
            is_virtual=True
        )
        physical_config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel',
            memory_mb=4096,
            is_virtual=False
        )
        
        assert HardwareClassifier.is_virtual(virtual_config) is True
        assert HardwareClassifier.is_virtual(physical_config) is False
    
    def test_is_physical(self):
        """Test checking if config is physical."""
        virtual_config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel',
            memory_mb=4096,
            is_virtual=True
        )
        physical_config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel',
            memory_mb=4096,
            is_virtual=False
        )
        
        assert HardwareClassifier.is_physical(virtual_config) is False
        assert HardwareClassifier.is_physical(physical_config) is True
    
    def test_prefer_virtual(self):
        """Test sorting to prefer virtual configurations."""
        configs = [
            HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=False),
            HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=True),
            HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=False),
            HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=True)
        ]
        
        sorted_configs = HardwareClassifier.prefer_virtual(configs)
        
        # First two should be virtual
        assert sorted_configs[0].is_virtual is True
        assert sorted_configs[1].is_virtual is True
        # Last two should be physical
        assert sorted_configs[2].is_virtual is False
        assert sorted_configs[3].is_virtual is False
    
    def test_prefer_virtual_with_architecture_filter(self):
        """Test sorting with architecture filter."""
        configs = [
            HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=False),
            HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=True),
            HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=False),
            HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=True)
        ]
        
        sorted_configs = HardwareClassifier.prefer_virtual(configs, architecture='x86_64')
        
        assert len(sorted_configs) == 2
        assert all(c.architecture == 'x86_64' for c in sorted_configs)
        assert sorted_configs[0].is_virtual is True
    
    def test_get_equivalent_configs(self):
        """Test finding equivalent configurations."""
        ref_config = HardwareConfig(
            architecture='x86_64',
            cpu_model='Intel',
            memory_mb=4096,
            is_virtual=True
        )
        
        all_configs = [
            ref_config,
            HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=False),
            HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=True),
            HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=4096, is_virtual=True)
        ]
        
        equivalent = HardwareClassifier.get_equivalent_configs(ref_config, all_configs)
        
        assert len(equivalent) == 1
        assert equivalent[0].architecture == 'x86_64'
        assert equivalent[0].memory_mb == 4096
        assert equivalent[0].is_virtual is False
