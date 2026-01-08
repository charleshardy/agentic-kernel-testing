"""
Physical Test Board Data Models

Models for physical test board registration, monitoring, and management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class BoardStatus(Enum):
    """Status of a physical test board."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    FLASHING = "flashing"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class HealthLevel(Enum):
    """Health level indicator."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class PowerStatus(Enum):
    """Power status of a board."""
    ON = "on"
    OFF = "off"
    CYCLING = "cycling"
    UNKNOWN = "unknown"


class PowerControlMethod(Enum):
    """Method for controlling board power."""
    USB_HUB = "usb_hub"
    NETWORK_PDU = "network_pdu"
    GPIO_RELAY = "gpio_relay"
    MANUAL = "manual"


@dataclass
class PowerControlConfig:
    """Configuration for board power control."""
    method: PowerControlMethod
    usb_hub_port: Optional[int] = None
    pdu_outlet: Optional[int] = None
    pdu_address: Optional[str] = None
    gpio_pin: Optional[int] = None
    relay_address: Optional[str] = None

    def is_automated(self) -> bool:
        """Check if power control is automated (not manual)."""
        return self.method != PowerControlMethod.MANUAL


@dataclass
class BoardHealth:
    """Health status of a physical test board."""
    connectivity: HealthLevel = HealthLevel.UNKNOWN
    temperature_celsius: Optional[float] = None
    storage_percent: Optional[float] = None
    power_status: PowerStatus = PowerStatus.UNKNOWN
    last_response_time_ms: Optional[int] = None

    def is_healthy(self) -> bool:
        """Check if board is healthy."""
        return self.connectivity == HealthLevel.HEALTHY

    def needs_attention(self) -> bool:
        """Check if board needs attention."""
        if self.connectivity in (HealthLevel.DEGRADED, HealthLevel.UNHEALTHY):
            return True
        if self.temperature_celsius and self.temperature_celsius > 80:
            return True
        if self.storage_percent and self.storage_percent > 90:
            return True
        return False


@dataclass
class Board:
    """A physical test board for hardware testing."""
    id: str
    name: str
    board_type: str  # raspberry_pi_4, beaglebone, riscv_board
    architecture: str  # arm64, armv7, riscv64
    power_control: PowerControlConfig
    created_at: datetime
    updated_at: datetime
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_port: int = 22
    ssh_username: Optional[str] = None
    serial_device: Optional[str] = None  # /dev/ttyUSB0
    serial_baud_rate: int = 115200
    status: BoardStatus = BoardStatus.UNKNOWN
    health: BoardHealth = field(default_factory=BoardHealth)
    flash_station_id: Optional[str] = None
    current_firmware_version: Optional[str] = None
    last_flash_timestamp: Optional[datetime] = None
    assigned_test_id: Optional[str] = None
    group_id: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    peripherals: List[str] = field(default_factory=list)
    maintenance_mode: bool = False
    last_health_check: Optional[datetime] = None

    def is_available(self) -> bool:
        """Check if board is available for allocation."""
        return (
            self.status == BoardStatus.AVAILABLE and
            not self.maintenance_mode and
            self.health.is_healthy()
        )

    def can_be_allocated(self) -> bool:
        """Check if board can be allocated for a test."""
        return (
            self.status in (BoardStatus.AVAILABLE, BoardStatus.UNKNOWN) and
            not self.maintenance_mode
        )

    def supports_architecture(self, arch: str) -> bool:
        """Check if board supports the given architecture."""
        return self.architecture.lower() == arch.lower()

    def has_peripherals(self, required: List[str]) -> bool:
        """Check if board has all required peripherals."""
        board_peripherals = set(p.lower() for p in self.peripherals)
        return all(p.lower() in board_peripherals for p in required)

    def matches_type(self, board_types: List[str]) -> bool:
        """Check if board matches any of the given types."""
        if not board_types:
            return True
        return self.board_type.lower() in [t.lower() for t in board_types]


@dataclass
class BoardRequirements:
    """Requirements for selecting a physical test board."""
    architecture: str
    board_types: List[str] = field(default_factory=list)
    required_peripherals: List[str] = field(default_factory=list)
    preferred_board_id: Optional[str] = None
    required_labels: Dict[str, str] = field(default_factory=dict)
    group_id: Optional[str] = None
    firmware_version: Optional[str] = None


@dataclass
class BoardSelectionResult:
    """Result of board selection."""
    success: bool
    board: Optional[Board] = None
    reservation_id: Optional[str] = None
    error_message: Optional[str] = None
    alternative_boards: List[Board] = field(default_factory=list)
    estimated_wait_time: Optional[int] = None  # seconds
    requires_flashing: bool = False
