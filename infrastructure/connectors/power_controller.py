"""
Power Controller for Physical Test Boards

Provides power control functionality for physical test boards via USB hub,
network PDU, or GPIO relay.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from infrastructure.models.board import PowerControlConfig, PowerControlMethod, PowerStatus

logger = logging.getLogger(__name__)


@dataclass
class PowerResult:
    """Result of a power control operation."""
    success: bool
    board_id: str
    operation: str  # on, off, cycle
    previous_status: PowerStatus
    new_status: PowerStatus
    duration_ms: int = 0
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PowerCycleResult:
    """Result of a power cycle operation."""
    success: bool
    board_id: str
    power_off_success: bool
    power_on_success: bool
    delay_seconds: int
    total_duration_ms: int = 0
    board_recovered: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PowerController:
    """
    Power controller for physical test boards.
    
    Supports USB hub, network PDU, and GPIO relay control methods.
    """

    def __init__(
        self,
        default_cycle_delay: int = 5,
        recovery_timeout: int = 60
    ):
        """
        Initialize Power controller.
        
        Args:
            default_cycle_delay: Default delay between power off and on (seconds)
            recovery_timeout: Timeout for board recovery after power cycle (seconds)
        """
        self.default_cycle_delay = default_cycle_delay
        self.recovery_timeout = recovery_timeout
        
        # Track power status
        self._power_status: Dict[str, PowerStatus] = {}
        self._power_history: Dict[str, List[PowerResult]] = {}

    async def power_on(
        self,
        board_id: str,
        config: PowerControlConfig
    ) -> PowerResult:
        """
        Power on a board.
        
        Args:
            board_id: Board identifier
            config: Power control configuration
            
        Returns:
            PowerResult with operation status
        """
        start_time = datetime.now(timezone.utc)
        previous_status = self._power_status.get(board_id, PowerStatus.UNKNOWN)
        
        try:
            logger.info(f"Powering on board {board_id} via {config.method.value}")
            
            if config.method == PowerControlMethod.USB_HUB:
                success = await self._usb_hub_power_on(config)
            elif config.method == PowerControlMethod.NETWORK_PDU:
                success = await self._pdu_power_on(config)
            elif config.method == PowerControlMethod.GPIO_RELAY:
                success = await self._gpio_power_on(config)
            elif config.method == PowerControlMethod.MANUAL:
                logger.warning(f"Manual power control required for board {board_id}")
                success = False
            else:
                success = False
            
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            new_status = PowerStatus.ON if success else previous_status
            self._power_status[board_id] = new_status
            
            result = PowerResult(
                success=success,
                board_id=board_id,
                operation="on",
                previous_status=previous_status,
                new_status=new_status,
                duration_ms=duration_ms
            )
            
            self._record_power_event(board_id, result)
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result = PowerResult(
                success=False,
                board_id=board_id,
                operation="on",
                previous_status=previous_status,
                new_status=previous_status,
                duration_ms=duration_ms,
                error_message=str(e)
            )
            
            self._record_power_event(board_id, result)
            return result

    async def power_off(
        self,
        board_id: str,
        config: PowerControlConfig
    ) -> PowerResult:
        """
        Power off a board.
        
        Args:
            board_id: Board identifier
            config: Power control configuration
            
        Returns:
            PowerResult with operation status
        """
        start_time = datetime.now(timezone.utc)
        previous_status = self._power_status.get(board_id, PowerStatus.UNKNOWN)
        
        try:
            logger.info(f"Powering off board {board_id} via {config.method.value}")
            
            if config.method == PowerControlMethod.USB_HUB:
                success = await self._usb_hub_power_off(config)
            elif config.method == PowerControlMethod.NETWORK_PDU:
                success = await self._pdu_power_off(config)
            elif config.method == PowerControlMethod.GPIO_RELAY:
                success = await self._gpio_power_off(config)
            elif config.method == PowerControlMethod.MANUAL:
                logger.warning(f"Manual power control required for board {board_id}")
                success = False
            else:
                success = False
            
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            new_status = PowerStatus.OFF if success else previous_status
            self._power_status[board_id] = new_status
            
            result = PowerResult(
                success=success,
                board_id=board_id,
                operation="off",
                previous_status=previous_status,
                new_status=new_status,
                duration_ms=duration_ms
            )
            
            self._record_power_event(board_id, result)
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            result = PowerResult(
                success=False,
                board_id=board_id,
                operation="off",
                previous_status=previous_status,
                new_status=previous_status,
                duration_ms=duration_ms,
                error_message=str(e)
            )
            
            self._record_power_event(board_id, result)
            return result

    async def power_cycle(
        self,
        board_id: str,
        config: PowerControlConfig,
        delay_seconds: Optional[int] = None
    ) -> PowerCycleResult:
        """
        Power cycle a board (off -> delay -> on).
        
        Args:
            board_id: Board identifier
            config: Power control configuration
            delay_seconds: Delay between off and on
            
        Returns:
            PowerCycleResult with operation status
        """
        delay = delay_seconds or self.default_cycle_delay
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"Power cycling board {board_id} with {delay}s delay")
        
        self._power_status[board_id] = PowerStatus.CYCLING
        
        # Power off
        off_result = await self.power_off(board_id, config)
        
        if not off_result.success:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PowerCycleResult(
                success=False,
                board_id=board_id,
                power_off_success=False,
                power_on_success=False,
                delay_seconds=delay,
                total_duration_ms=duration_ms,
                error_message=f"Power off failed: {off_result.error_message}"
            )
        
        # Wait
        await asyncio.sleep(delay)
        
        # Power on
        on_result = await self.power_on(board_id, config)
        
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return PowerCycleResult(
            success=on_result.success,
            board_id=board_id,
            power_off_success=True,
            power_on_success=on_result.success,
            delay_seconds=delay,
            total_duration_ms=duration_ms,
            board_recovered=on_result.success,
            error_message=on_result.error_message if not on_result.success else None
        )

    async def get_power_status(
        self,
        board_id: str,
        config: PowerControlConfig
    ) -> PowerStatus:
        """
        Get current power status of a board.
        
        Args:
            board_id: Board identifier
            config: Power control configuration
            
        Returns:
            Current PowerStatus
        """
        # In a real implementation, this would query the actual power state
        return self._power_status.get(board_id, PowerStatus.UNKNOWN)

    def get_power_history(
        self,
        board_id: str,
        limit: int = 10
    ) -> List[PowerResult]:
        """
        Get power control history for a board.
        
        Args:
            board_id: Board identifier
            limit: Maximum number of events to return
            
        Returns:
            List of PowerResult events
        """
        history = self._power_history.get(board_id, [])
        return history[-limit:]

    # Private methods for different power control methods

    async def _usb_hub_power_on(self, config: PowerControlConfig) -> bool:
        """Power on via USB hub."""
        if config.usb_hub_port is None:
            logger.error("USB hub port not configured")
            return False
        
        # In a real implementation, this would use uhubctl or similar
        logger.info(f"USB hub: enabling port {config.usb_hub_port}")
        await asyncio.sleep(0.5)  # Simulate operation
        return True

    async def _usb_hub_power_off(self, config: PowerControlConfig) -> bool:
        """Power off via USB hub."""
        if config.usb_hub_port is None:
            logger.error("USB hub port not configured")
            return False
        
        logger.info(f"USB hub: disabling port {config.usb_hub_port}")
        await asyncio.sleep(0.5)
        return True

    async def _pdu_power_on(self, config: PowerControlConfig) -> bool:
        """Power on via network PDU."""
        if config.pdu_address is None or config.pdu_outlet is None:
            logger.error("PDU address or outlet not configured")
            return False
        
        # In a real implementation, this would use SNMP or HTTP API
        logger.info(f"PDU {config.pdu_address}: enabling outlet {config.pdu_outlet}")
        await asyncio.sleep(0.5)
        return True

    async def _pdu_power_off(self, config: PowerControlConfig) -> bool:
        """Power off via network PDU."""
        if config.pdu_address is None or config.pdu_outlet is None:
            logger.error("PDU address or outlet not configured")
            return False
        
        logger.info(f"PDU {config.pdu_address}: disabling outlet {config.pdu_outlet}")
        await asyncio.sleep(0.5)
        return True

    async def _gpio_power_on(self, config: PowerControlConfig) -> bool:
        """Power on via GPIO relay."""
        if config.gpio_pin is None:
            logger.error("GPIO pin not configured")
            return False
        
        # In a real implementation, this would use RPi.GPIO or similar
        logger.info(f"GPIO: setting pin {config.gpio_pin} HIGH")
        await asyncio.sleep(0.1)
        return True

    async def _gpio_power_off(self, config: PowerControlConfig) -> bool:
        """Power off via GPIO relay."""
        if config.gpio_pin is None:
            logger.error("GPIO pin not configured")
            return False
        
        logger.info(f"GPIO: setting pin {config.gpio_pin} LOW")
        await asyncio.sleep(0.1)
        return True

    def _record_power_event(self, board_id: str, result: PowerResult) -> None:
        """Record a power event in history."""
        if board_id not in self._power_history:
            self._power_history[board_id] = []
        
        self._power_history[board_id].append(result)
        
        # Keep only last 100 events per board
        if len(self._power_history[board_id]) > 100:
            self._power_history[board_id] = self._power_history[board_id][-100:]
