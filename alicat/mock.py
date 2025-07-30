"""Mock for offline testing of `FlowController`s."""
from __future__ import annotations

import asyncio
from random import choice, random
from time import sleep
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from .driver import FlowController as RealFlowController
from .util import Client as RealClient


class FlowController(RealFlowController):
    """Mocks an Alicat MFC for offline testing."""

    def __init__(self, address: str, unit: str = 'A', *args: Any, **kwargs: Any) -> None:
        """Initialize the device client."""
        super().__init__()
        self.hw = Client(self)
        self.hw.address = address
        self.open = True
        self.control_point: str = choice(list(self.control_points))  # type:ignore[assignment]
        self.state: dict[str, str | float] = {
            'setpoint': 10,
            'gas': 'N2',
            'mass_flow': 10 * (0.95 + 0.1 * random()),
            'pressure': random() * 50.0,
            'temperature': random() * 50.0,
            'total_flow': 0.0,
            'unit': unit,
            'volumetric_flow': 0.0,
        }
        self.ramp_config = { 'up': False, 'down': False, 'zero': False, 'power': False }
        self.unit: str = unit
        self.button_lock: bool = False
        self.keys = ['pressure', 'temperature', 'volumetric_flow', 'mass_flow',
                     'setpoint', 'gas']
        self.firmware = '6v21.0-R22 Nov 30 2016,16:04:20'

    async def get(self) -> dict[str, str | float]:
        """Return the full state."""
        sleep(random() * 0.25)
        return self.state

    async def set_gas(self, gas: int | str) -> None:
        """Set the gas type."""
        if isinstance(gas, int):
            gas = self.gases[gas]
        self.state['gas'] = gas

    async def get_ramp_config(self) -> dict[str, bool]:
        """Get ramp config."""
        return self.ramp_config

    async def set_ramp_config(self, config: dict[str, bool]) -> None:
        """Set ramp config."""
        self.ramp_config = config

class Client(RealClient):
    """Mock the alicat communication client."""

    def __init__(self, parent: FlowController) -> None:
        self.parent = parent
        super().__init__(timeout=0.01)
        self.writer = MagicMock(spec=asyncio.StreamWriter)
        self.writer.write.side_effect=self._handle_write
        self.reader = AsyncMock(spec=asyncio.StreamReader)
        self.reader.read.return_value = self.eol
        self.reader.readuntil.side_effect = self._handle_read

        self.open = True
        self._next_reply = ''

    async def _handle_connection(self) -> None:
        pass

    def _handle_write(self, data: bytes) -> None:
        """Act on writes sent to the mock client, updating internal state and setting self._next_reply if necessary."""
        msg = data.decode()
        if msg[0] != self.parent.unit:  # command for another unit
            return
        msg = msg[1:-1]  # strip unit and newline at end
        if msg == '$$L':  # lock
            self.parent.button_lock = True
            self._next_reply = 'FIXME - should be dataframe'
        elif msg == '$$U':  # unlock
            self.parent.button_lock = False
            self._next_reply = 'FIXME - should be dataframe'
        elif 'W122=' in msg:  # set control point
            cp = int(msg[5:])
            self.parent.control_point = next(p for p, i in self.parent.control_points.items() if cp == i)
            self._next_reply = "122=" + str(cp)
        elif msg == 'R122':  # read control point
            self._next_reply = "122=" + str(self.parent.control_points[self.parent.control_point])
        elif msg[0] == 'S':  # set setpoint
            self.parent.state['setpoint'] = float(msg[1:])
            self._next_reply = 'FIXME - should be dataframe'
        else:
            raise NotImplementedError(msg)

    async def _handle_read(self, separator: bytes) -> bytes:
        """Reply to read requests from the mock client."""
        reply = self._next_reply.encode() + separator
        self._next_reply = ''
        return reply
