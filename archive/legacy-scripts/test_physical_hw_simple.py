#!/usr/bin/env python3
"""Simple test to verify physical hardware lab implementation."""

import sys
sys.path.insert(0, '.')

from execution.physical_hardware_lab import (
    PhysicalHardwareLab,
    PhysicalHardware,
    ReservationStatus
)
from ai_generator.models import HardwareConfig, Credentials, TestCase, TestType

def test_basic_functionality():
    """Test basic physical hardware lab functionality."""
    print("Testing Physical Hardware Lab Implementation...")
    
    # Create hardware config
    config = HardwareConfig(
        architecture="arm64",
        cpu_model="ARM Cortex-A72",
        memory_mb=4096,
        storage_type="emmc",
        is_virtual=False,
        emulator=None
    )
    
    # Create credentials
    creds = Credentials(
        username="testuser",
        password="testpass"
    )
    
    # Create physical hardware
    hw = PhysicalHardware(
        hardware_id="rpi-001",
        config=config,
        ip_address="192.168.1.100",
        ssh_credentials=creds,
        power_control_type="pdu",
        location="Lab Rack 1"
    )
    
    print(f"✓ Created physical hardware: {hw.hardware_id}")
    
    # Create lab
    lab = PhysicalHardwareLab(hardware_inventory=[hw])
    print(f"✓ Created lab with {len(lab.hardware)} hardware")
    
    # Test reservation
    reservation = lab.reserve_hardware("rpi-001", "test-user", duration_minutes=30)
    print(f"✓ Reserved hardware: {reservation.reservation_id}")
    assert hw.status == ReservationStatus.RESERVED
    
    # Test listing available hardware
    available = lab.list_available_hardware()
    print(f"✓ Available hardware count: {len(available)}")
    assert len(available) == 0  # Should be 0 since we reserved it
    
    # Test release
    lab.release_reservation(reservation.reservation_id)
    print(f"✓ Released reservation")
    assert hw.status == ReservationStatus.AVAILABLE
    
    # Test available again
    available = lab.list_available_hardware()
    assert len(available) == 1
    print(f"✓ Available hardware after release: {len(available)}")
    
    # Test power control
    result = lab.power_control("rpi-001", "on")
    print(f"✓ Power control executed: {result}")
    
    # Test maintenance mode
    lab.set_hardware_maintenance("rpi-001", maintenance=True)
    assert hw.status == ReservationStatus.MAINTENANCE
    print(f"✓ Set maintenance mode")
    
    lab.set_hardware_maintenance("rpi-001", maintenance=False)
    assert hw.status == ReservationStatus.AVAILABLE
    print(f"✓ Cleared maintenance mode")
    
    print("\n✅ All basic tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_basic_functionality()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
