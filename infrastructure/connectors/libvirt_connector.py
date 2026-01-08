"""
Libvirt Connector for VM Management

Provides libvirt connectivity for QEMU host management.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from infrastructure.connectors.ssh_connector import SSHCredentials, SSHConnector

logger = logging.getLogger(__name__)


class VMState(Enum):
    """State of a virtual machine."""
    RUNNING = "running"
    PAUSED = "paused"
    SHUTDOWN = "shutdown"
    SHUTOFF = "shutoff"
    CRASHED = "crashed"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


@dataclass
class VMInfo:
    """Information about a virtual machine."""
    id: str
    name: str
    state: VMState
    cpu_count: int
    memory_mb: int
    disk_gb: float
    created_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VMConfig:
    """Configuration for creating a virtual machine."""
    name: str
    cpu_count: int
    memory_mb: int
    disk_gb: float
    architecture: str = "x86_64"
    kernel_path: Optional[str] = None
    initrd_path: Optional[str] = None
    rootfs_path: Optional[str] = None
    kernel_args: str = ""
    network_bridge: str = "virbr0"
    enable_kvm: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HostCapabilities:
    """Capabilities of a libvirt host."""
    architecture: str
    cpu_model: str
    total_cpu_cores: int
    total_memory_mb: int
    kvm_available: bool
    nested_virt_available: bool
    supported_architectures: List[str] = field(default_factory=list)
    libvirt_version: str = ""
    qemu_version: str = ""


@dataclass
class LibvirtConnection:
    """Represents a libvirt connection."""
    host: str
    uri: str
    connected: bool = False
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LibvirtConnector:
    """
    Libvirt connector for QEMU host management.
    
    Provides methods for VM listing, creation, destruction, and capability detection.
    """

    def __init__(self, ssh_connector: Optional[SSHConnector] = None):
        """
        Initialize Libvirt connector.
        
        Args:
            ssh_connector: SSH connector for remote libvirt access
        """
        self.ssh_connector = ssh_connector or SSHConnector()
        self._connections: Dict[str, LibvirtConnection] = {}

    async def connect(
        self,
        host: str,
        credentials: SSHCredentials
    ) -> LibvirtConnection:
        """
        Connect to a libvirt host.
        
        Args:
            host: Hostname or IP address
            credentials: SSH credentials for the host
            
        Returns:
            LibvirtConnection object
        """
        uri = f"qemu+ssh://{credentials.username}@{host}/system"
        
        try:
            # Validate SSH connection first
            validation = await self.ssh_connector.validate_connection(credentials)
            if not validation.success:
                raise ConnectionError(f"SSH validation failed: {validation.error_message}")
            
            # Check if libvirt is available
            result = await self.ssh_connector.execute_command(
                credentials,
                "virsh version --daemon",
                timeout=30
            )
            
            if not result.success:
                raise ConnectionError(f"Libvirt not available: {result.stderr}")
            
            connection = LibvirtConnection(
                host=host,
                uri=uri,
                connected=True
            )
            
            self._connections[host] = connection
            logger.info(f"Connected to libvirt on {host}")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect to libvirt on {host}: {e}")
            raise

    async def disconnect(self, host: str) -> bool:
        """
        Disconnect from a libvirt host.
        
        Args:
            host: Hostname or IP address
            
        Returns:
            True if disconnection successful
        """
        if host in self._connections:
            self._connections[host].connected = False
            del self._connections[host]
            logger.info(f"Disconnected from libvirt on {host}")
            return True
        return False

    async def list_vms(
        self,
        credentials: SSHCredentials,
        include_inactive: bool = True
    ) -> List[VMInfo]:
        """
        List virtual machines on a host.
        
        Args:
            credentials: SSH credentials for the host
            include_inactive: Include inactive VMs
            
        Returns:
            List of VMInfo objects
        """
        try:
            # List all VMs
            cmd = "virsh list --all" if include_inactive else "virsh list"
            result = await self.ssh_connector.execute_command(credentials, cmd)
            
            if not result.success:
                logger.error(f"Failed to list VMs: {result.stderr}")
                return []
            
            # Parse virsh output (simplified)
            vms = []
            lines = result.stdout.strip().split('\n')
            
            # Skip header lines
            for line in lines[2:]:
                parts = line.split()
                if len(parts) >= 3:
                    vm_id = parts[0] if parts[0] != '-' else None
                    name = parts[1]
                    state_str = ' '.join(parts[2:])
                    
                    state = self._parse_vm_state(state_str)
                    
                    # Get VM details
                    vm_info = await self._get_vm_details(credentials, name)
                    if vm_info:
                        vms.append(vm_info)
                    else:
                        vms.append(VMInfo(
                            id=vm_id or name,
                            name=name,
                            state=state,
                            cpu_count=0,
                            memory_mb=0,
                            disk_gb=0
                        ))
            
            return vms
            
        except Exception as e:
            logger.error(f"Error listing VMs: {e}")
            return []

    async def create_vm(
        self,
        credentials: SSHCredentials,
        config: VMConfig
    ) -> Optional[VMInfo]:
        """
        Create a new virtual machine.
        
        Args:
            credentials: SSH credentials for the host
            config: VM configuration
            
        Returns:
            VMInfo if successful, None otherwise
        """
        try:
            # Generate VM XML definition
            xml = self._generate_vm_xml(config)
            
            # Create temporary XML file on remote host
            xml_path = f"/tmp/vm_{config.name}.xml"
            
            # Write XML to remote host
            write_cmd = f"cat > {xml_path} << 'EOF'\n{xml}\nEOF"
            result = await self.ssh_connector.execute_command(credentials, write_cmd)
            
            if not result.success:
                logger.error(f"Failed to write VM XML: {result.stderr}")
                return None
            
            # Define the VM
            define_cmd = f"virsh define {xml_path}"
            result = await self.ssh_connector.execute_command(credentials, define_cmd)
            
            if not result.success:
                logger.error(f"Failed to define VM: {result.stderr}")
                return None
            
            # Start the VM
            start_cmd = f"virsh start {config.name}"
            result = await self.ssh_connector.execute_command(credentials, start_cmd)
            
            if not result.success:
                logger.error(f"Failed to start VM: {result.stderr}")
                # VM is defined but not started
            
            # Clean up XML file
            await self.ssh_connector.execute_command(credentials, f"rm -f {xml_path}")
            
            # Get VM info
            return await self._get_vm_details(credentials, config.name)
            
        except Exception as e:
            logger.error(f"Error creating VM: {e}")
            return None

    async def destroy_vm(
        self,
        credentials: SSHCredentials,
        vm_name: str,
        undefine: bool = True
    ) -> bool:
        """
        Destroy (stop) a virtual machine.
        
        Args:
            credentials: SSH credentials for the host
            vm_name: Name of the VM
            undefine: Also undefine (remove) the VM
            
        Returns:
            True if successful
        """
        try:
            # Force stop the VM
            destroy_cmd = f"virsh destroy {vm_name}"
            result = await self.ssh_connector.execute_command(credentials, destroy_cmd)
            
            # VM might already be stopped, so don't fail on destroy error
            
            if undefine:
                # Undefine the VM
                undefine_cmd = f"virsh undefine {vm_name}"
                result = await self.ssh_connector.execute_command(credentials, undefine_cmd)
                
                if not result.success:
                    logger.error(f"Failed to undefine VM: {result.stderr}")
                    return False
            
            logger.info(f"Destroyed VM: {vm_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error destroying VM: {e}")
            return False

    async def get_host_capabilities(
        self,
        credentials: SSHCredentials
    ) -> Optional[HostCapabilities]:
        """
        Get capabilities of a libvirt host.
        
        Args:
            credentials: SSH credentials for the host
            
        Returns:
            HostCapabilities if successful
        """
        try:
            # Get CPU info
            cpu_result = await self.ssh_connector.execute_command(
                credentials,
                "nproc"
            )
            cpu_cores = int(cpu_result.stdout.strip()) if cpu_result.success else 0
            
            # Get memory info
            mem_result = await self.ssh_connector.execute_command(
                credentials,
                "free -m | grep Mem | awk '{print $2}'"
            )
            memory_mb = int(mem_result.stdout.strip()) if mem_result.success else 0
            
            # Get architecture
            arch_result = await self.ssh_connector.execute_command(
                credentials,
                "uname -m"
            )
            architecture = arch_result.stdout.strip() if arch_result.success else "unknown"
            
            # Check KVM availability
            kvm_result = await self.ssh_connector.execute_command(
                credentials,
                "test -e /dev/kvm && echo 'yes' || echo 'no'"
            )
            kvm_available = kvm_result.stdout.strip() == "yes" if kvm_result.success else False
            
            # Get libvirt version
            version_result = await self.ssh_connector.execute_command(
                credentials,
                "virsh version --daemon 2>/dev/null | grep 'libvirt' | head -1"
            )
            libvirt_version = version_result.stdout.strip() if version_result.success else ""
            
            return HostCapabilities(
                architecture=architecture,
                cpu_model="",  # Would need more parsing
                total_cpu_cores=cpu_cores,
                total_memory_mb=memory_mb,
                kvm_available=kvm_available,
                nested_virt_available=False,  # Would need more checking
                supported_architectures=[architecture],
                libvirt_version=libvirt_version
            )
            
        except Exception as e:
            logger.error(f"Error getting host capabilities: {e}")
            return None

    async def _get_vm_details(
        self,
        credentials: SSHCredentials,
        vm_name: str
    ) -> Optional[VMInfo]:
        """Get detailed information about a VM."""
        try:
            # Get VM info using virsh dominfo
            result = await self.ssh_connector.execute_command(
                credentials,
                f"virsh dominfo {vm_name}"
            )
            
            if not result.success:
                return None
            
            # Parse dominfo output
            info = {}
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip().lower()] = value.strip()
            
            state = self._parse_vm_state(info.get('state', 'unknown'))
            
            # Get CPU count
            cpu_count = int(info.get('cpu(s)', 0))
            
            # Get memory (convert from KiB to MB)
            memory_str = info.get('max memory', '0 KiB')
            memory_kb = int(memory_str.split()[0])
            memory_mb = memory_kb // 1024
            
            return VMInfo(
                id=info.get('id', vm_name),
                name=vm_name,
                state=state,
                cpu_count=cpu_count,
                memory_mb=memory_mb,
                disk_gb=0  # Would need to query disk info separately
            )
            
        except Exception as e:
            logger.error(f"Error getting VM details: {e}")
            return None

    def _parse_vm_state(self, state_str: str) -> VMState:
        """Parse VM state string to VMState enum."""
        state_str = state_str.lower()
        if 'running' in state_str:
            return VMState.RUNNING
        elif 'paused' in state_str:
            return VMState.PAUSED
        elif 'shut off' in state_str or 'shutoff' in state_str:
            return VMState.SHUTOFF
        elif 'shutdown' in state_str:
            return VMState.SHUTDOWN
        elif 'crashed' in state_str:
            return VMState.CRASHED
        elif 'suspended' in state_str:
            return VMState.SUSPENDED
        else:
            return VMState.UNKNOWN

    def _generate_vm_xml(self, config: VMConfig) -> str:
        """Generate libvirt XML definition for a VM."""
        kvm_type = "kvm" if config.enable_kvm else "qemu"
        
        xml = f"""<domain type='{kvm_type}'>
  <name>{config.name}</name>
  <memory unit='MiB'>{config.memory_mb}</memory>
  <vcpu>{config.cpu_count}</vcpu>
  <os>
    <type arch='{config.architecture}'>hvm</type>"""
        
        if config.kernel_path:
            xml += f"\n    <kernel>{config.kernel_path}</kernel>"
        if config.initrd_path:
            xml += f"\n    <initrd>{config.initrd_path}</initrd>"
        if config.kernel_args:
            xml += f"\n    <cmdline>{config.kernel_args}</cmdline>"
        
        xml += """
  </os>
  <devices>
    <emulator>/usr/bin/qemu-system-""" + config.architecture + """</emulator>"""
        
        if config.rootfs_path:
            xml += f"""
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{config.rootfs_path}'/>
      <target dev='vda' bus='virtio'/>
    </disk>"""
        
        xml += f"""
    <interface type='bridge'>
      <source bridge='{config.network_bridge}'/>
      <model type='virtio'/>
    </interface>
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
  </devices>
</domain>"""
        
        return xml
