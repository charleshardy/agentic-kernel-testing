"""Generator Factory for Property-Based Tests.

Creates Hypothesis strategies (generators) for property-based tests.
Supports domain-specific generators with constraints and edge cases.
"""

from typing import Dict, Any, List, Optional, Type
from dataclasses import fields, is_dataclass
import string

try:
    from hypothesis import strategies as st
    from hypothesis.strategies import SearchStrategy
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    SearchStrategy = Any

from .models import TypeSpecification


class GeneratorFactory:
    """Creates Hypothesis strategies for property-based tests.
    
    Provides methods to create generators for:
    - Primitive types (int, str, float, bool)
    - Complex types (list, dict, dataclass)
    - Domain-specific types with constraints
    - Edge cases and boundary values
    """
    
    # Default constraints for common types
    DEFAULT_CONSTRAINTS = {
        'int': {'min_value': -1000000, 'max_value': 1000000},
        'str': {'min_size': 0, 'max_size': 1000},
        'float': {'min_value': -1e10, 'max_value': 1e10},
        'list': {'min_size': 0, 'max_size': 100},
        'dict': {'min_size': 0, 'max_size': 50},
    }
    
    # Domain-specific generators for infrastructure models
    DOMAIN_GENERATORS = {
        'hostname': lambda: st.from_regex(r'[a-z][a-z0-9-]{0,62}', fullmatch=True),
        'ip_address': lambda: st.ip_addresses(v=4).map(str),
        'port': lambda: st.integers(min_value=1, max_value=65535),
        'architecture': lambda: st.sampled_from(['x86_64', 'arm64', 'armv7', 'riscv64']),
        'status': lambda: st.sampled_from(['online', 'offline', 'degraded', 'maintenance']),
        'percentage': lambda: st.floats(min_value=0.0, max_value=100.0),
        'memory_mb': lambda: st.integers(min_value=512, max_value=1048576),
        'cpu_cores': lambda: st.integers(min_value=1, max_value=256),
        'storage_gb': lambda: st.integers(min_value=1, max_value=100000),
        'uuid': lambda: st.uuids().map(lambda u: u.hex),
        'email': lambda: st.emails(),
        'url': lambda: st.from_regex(r'https?://[a-z0-9.-]+\.[a-z]{2,}(/[a-z0-9/-]*)?', fullmatch=True),
    }
    
    def __init__(self):
        """Initialize the generator factory."""
        if not HYPOTHESIS_AVAILABLE:
            raise ImportError("Hypothesis is required for property-based testing. Install with: pip install hypothesis")
    
    def create_generator(self, type_spec: TypeSpecification) -> SearchStrategy:
        """Create a generator for a type specification.
        
        Args:
            type_spec: TypeSpecification describing the type
            
        Returns:
            Hypothesis SearchStrategy for the type
        """
        base_type = type_spec.base_type.lower()
        constraints = {**self.DEFAULT_CONSTRAINTS.get(base_type, {}), **type_spec.constraints}
        
        # Create base generator
        if base_type == 'int':
            generator = st.integers(
                min_value=constraints.get('min_value', -1000000),
                max_value=constraints.get('max_value', 1000000)
            )
        elif base_type == 'str':
            generator = st.text(
                min_size=constraints.get('min_size', 0),
                max_size=constraints.get('max_size', 1000)
            )
        elif base_type == 'float':
            generator = st.floats(
                min_value=constraints.get('min_value', -1e10),
                max_value=constraints.get('max_value', 1e10),
                allow_nan=constraints.get('allow_nan', False),
                allow_infinity=constraints.get('allow_infinity', False)
            )
        elif base_type == 'bool':
            generator = st.booleans()
        elif base_type == 'list':
            element_type = constraints.get('element_type', 'str')
            element_spec = TypeSpecification(name=f"{type_spec.name}_element", base_type=element_type)
            element_gen = self.create_generator(element_spec)
            generator = st.lists(
                element_gen,
                min_size=constraints.get('min_size', 0),
                max_size=constraints.get('max_size', 100)
            )
        elif base_type == 'dict':
            key_type = constraints.get('key_type', 'str')
            value_type = constraints.get('value_type', 'str')
            key_spec = TypeSpecification(name=f"{type_spec.name}_key", base_type=key_type)
            value_spec = TypeSpecification(name=f"{type_spec.name}_value", base_type=value_type)
            generator = st.dictionaries(
                self.create_generator(key_spec),
                self.create_generator(value_spec),
                min_size=constraints.get('min_size', 0),
                max_size=constraints.get('max_size', 50)
            )
        elif base_type in self.DOMAIN_GENERATORS:
            generator = self.DOMAIN_GENERATORS[base_type]()
        else:
            # Default to text for unknown types
            generator = st.text(min_size=0, max_size=100)
        
        # Add edge cases if specified
        if type_spec.edge_cases:
            generator = self.create_edge_case_generator(generator, type_spec.edge_cases)
        
        return generator
    
    def create_domain_generator(self, domain: str, constraints: Optional[Dict[str, Any]] = None) -> SearchStrategy:
        """Create a domain-specific generator with constraints.
        
        Args:
            domain: Domain name (e.g., "build_server", "host", "board")
            constraints: Optional dictionary of constraints
            
        Returns:
            Constrained Hypothesis SearchStrategy
        """
        constraints = constraints or {}
        
        if domain == 'build_server':
            return self._create_build_server_generator(constraints)
        elif domain == 'host':
            return self._create_host_generator(constraints)
        elif domain == 'board':
            return self._create_board_generator(constraints)
        elif domain == 'test_case':
            return self._create_test_case_generator(constraints)
        elif domain == 'artifact':
            return self._create_artifact_generator(constraints)
        elif domain in self.DOMAIN_GENERATORS:
            return self.DOMAIN_GENERATORS[domain]()
        else:
            raise ValueError(f"Unknown domain: {domain}")
    
    def _create_build_server_generator(self, constraints: Dict[str, Any]) -> SearchStrategy:
        """Create a generator for BuildServer objects."""
        return st.fixed_dictionaries({
            'id': st.uuids().map(lambda u: u.hex),
            'hostname': self.DOMAIN_GENERATORS['hostname'](),
            'ip_address': self.DOMAIN_GENERATORS['ip_address'](),
            'ssh_port': st.just(22) | st.integers(min_value=1024, max_value=65535),
            'ssh_username': st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=32),
            'status': st.sampled_from(['online', 'offline', 'degraded', 'maintenance']),
            'supported_architectures': st.lists(
                st.sampled_from(['x86_64', 'arm64', 'armv7', 'riscv64']),
                min_size=1,
                max_size=4,
                unique=True
            ),
            'total_cpu_cores': st.integers(min_value=1, max_value=128),
            'total_memory_mb': st.integers(min_value=1024, max_value=1048576),
            'total_storage_gb': st.integers(min_value=10, max_value=10000),
            'active_build_count': st.integers(min_value=0, max_value=constraints.get('max_builds', 10)),
            'max_concurrent_builds': st.integers(min_value=1, max_value=16),
            'maintenance_mode': st.booleans(),
        })
    
    def _create_host_generator(self, constraints: Dict[str, Any]) -> SearchStrategy:
        """Create a generator for Host objects."""
        return st.fixed_dictionaries({
            'id': st.uuids().map(lambda u: u.hex),
            'hostname': self.DOMAIN_GENERATORS['hostname'](),
            'ip_address': self.DOMAIN_GENERATORS['ip_address'](),
            'ssh_port': st.just(22) | st.integers(min_value=1024, max_value=65535),
            'ssh_username': st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=32),
            'status': st.sampled_from(['online', 'offline', 'degraded', 'maintenance']),
            'architecture': st.sampled_from(['x86_64', 'arm64']),
            'total_cpu_cores': st.integers(min_value=1, max_value=256),
            'total_memory_mb': st.integers(min_value=1024, max_value=2097152),
            'total_storage_gb': st.integers(min_value=10, max_value=100000),
            'kvm_enabled': st.booleans(),
            'running_vm_count': st.integers(min_value=0, max_value=constraints.get('max_vms', 50)),
            'max_vms': st.integers(min_value=1, max_value=100),
            'maintenance_mode': st.booleans(),
            'cpu_percent': st.floats(min_value=0.0, max_value=100.0),
            'memory_percent': st.floats(min_value=0.0, max_value=100.0),
        })
    
    def _create_board_generator(self, constraints: Dict[str, Any]) -> SearchStrategy:
        """Create a generator for Board objects."""
        return st.fixed_dictionaries({
            'id': st.uuids().map(lambda u: u.hex),
            'name': st.text(alphabet=string.ascii_lowercase + string.digits + '-', min_size=1, max_size=64),
            'board_type': st.sampled_from(['raspberry_pi_4', 'beaglebone', 'riscv_board', 'jetson_nano']),
            'architecture': st.sampled_from(['arm64', 'armv7', 'riscv64']),
            'status': st.sampled_from(['available', 'in_use', 'flashing', 'offline', 'maintenance']),
            'ip_address': self.DOMAIN_GENERATORS['ip_address']() | st.none(),
            'serial_device': st.from_regex(r'/dev/ttyUSB[0-9]', fullmatch=True) | st.none(),
            'power_control_method': st.sampled_from(['usb_hub', 'network_pdu', 'gpio_relay', 'manual']),
            'maintenance_mode': st.booleans(),
            'peripherals': st.lists(
                st.sampled_from(['gpio', 'i2c', 'spi', 'uart', 'usb', 'ethernet', 'wifi']),
                min_size=0,
                max_size=7,
                unique=True
            ),
        })
    
    def _create_test_case_generator(self, constraints: Dict[str, Any]) -> SearchStrategy:
        """Create a generator for TestCase objects."""
        return st.fixed_dictionaries({
            'id': st.uuids().map(lambda u: f"test_{u.hex[:8]}"),
            'name': st.text(min_size=1, max_size=100),
            'description': st.text(min_size=0, max_size=500),
            'test_type': st.sampled_from(['unit', 'integration', 'fuzz', 'performance', 'security']),
            'target_subsystem': st.text(alphabet=string.ascii_lowercase + '_', min_size=1, max_size=50),
            'execution_time_estimate': st.integers(min_value=1, max_value=3600),
            'test_script': st.text(min_size=10, max_size=10000),
        })
    
    def _create_artifact_generator(self, constraints: Dict[str, Any]) -> SearchStrategy:
        """Create a generator for Artifact objects."""
        return st.fixed_dictionaries({
            'id': st.uuids().map(lambda u: u.hex),
            'build_id': st.uuids().map(lambda u: u.hex),
            'artifact_type': st.sampled_from(['kernel_image', 'initrd', 'rootfs', 'device_tree', 'kernel_modules']),
            'filename': st.from_regex(r'[a-z0-9_-]+\.(img|bin|dtb|tar\.gz)', fullmatch=True),
            'path': st.from_regex(r'/artifacts/[a-z0-9/-]+', fullmatch=True),
            'size_bytes': st.integers(min_value=1, max_value=10737418240),  # Up to 10GB
            'checksum_sha256': st.from_regex(r'[a-f0-9]{64}', fullmatch=True),
            'architecture': st.sampled_from(['x86_64', 'arm64', 'armv7', 'riscv64']),
        })
    
    def compose_generators(self, generators: Dict[str, SearchStrategy]) -> SearchStrategy:
        """Compose multiple generators into a complex strategy.
        
        Args:
            generators: Dictionary mapping field names to strategies
            
        Returns:
            Composed Hypothesis SearchStrategy
        """
        return st.fixed_dictionaries(generators)
    
    def create_edge_case_generator(self, base_generator: SearchStrategy, edge_cases: List[Any]) -> SearchStrategy:
        """Create a generator that includes specific edge cases.
        
        Args:
            base_generator: Base strategy
            edge_cases: List of edge case values to include
            
        Returns:
            Strategy that includes edge cases
        """
        if not edge_cases:
            return base_generator
        
        # Create a strategy that samples from edge cases with some probability
        edge_case_strategy = st.sampled_from(edge_cases)
        
        # Combine with base generator, preferring edge cases 20% of the time
        return st.one_of(
            base_generator,
            base_generator,
            base_generator,
            base_generator,
            edge_case_strategy,
        )
    
    def create_dataclass_generator(self, dataclass_type: Type) -> SearchStrategy:
        """Create a generator for a dataclass type.
        
        Args:
            dataclass_type: The dataclass type to generate
            
        Returns:
            Hypothesis SearchStrategy for the dataclass
        """
        if not is_dataclass(dataclass_type):
            raise ValueError(f"{dataclass_type} is not a dataclass")
        
        field_generators = {}
        for field in fields(dataclass_type):
            field_type = field.type
            
            # Map Python types to generators
            if field_type == int:
                field_generators[field.name] = st.integers()
            elif field_type == str:
                field_generators[field.name] = st.text(max_size=100)
            elif field_type == float:
                field_generators[field.name] = st.floats(allow_nan=False)
            elif field_type == bool:
                field_generators[field.name] = st.booleans()
            elif hasattr(field_type, '__origin__'):
                # Handle generic types like List[str], Optional[int], etc.
                origin = field_type.__origin__
                if origin is list:
                    element_type = field_type.__args__[0] if field_type.__args__ else str
                    if element_type == str:
                        field_generators[field.name] = st.lists(st.text(max_size=50), max_size=10)
                    elif element_type == int:
                        field_generators[field.name] = st.lists(st.integers(), max_size=10)
                    else:
                        field_generators[field.name] = st.lists(st.text(max_size=50), max_size=10)
                elif origin is dict:
                    field_generators[field.name] = st.dictionaries(
                        st.text(max_size=20),
                        st.text(max_size=50),
                        max_size=10
                    )
                else:
                    field_generators[field.name] = st.none() | st.text(max_size=50)
            else:
                # Default to text for unknown types
                field_generators[field.name] = st.text(max_size=100)
        
        return st.fixed_dictionaries(field_generators).map(lambda d: dataclass_type(**d))


# Convenience function
def create_generator(type_spec: TypeSpecification) -> SearchStrategy:
    """Create a generator for a type specification.
    
    Args:
        type_spec: TypeSpecification describing the type
        
    Returns:
        Hypothesis SearchStrategy
    """
    factory = GeneratorFactory()
    return factory.create_generator(type_spec)


def create_domain_generator(domain: str, constraints: Optional[Dict[str, Any]] = None) -> SearchStrategy:
    """Create a domain-specific generator.
    
    Args:
        domain: Domain name
        constraints: Optional constraints
        
    Returns:
        Hypothesis SearchStrategy
    """
    factory = GeneratorFactory()
    return factory.create_domain_generator(domain, constraints)
