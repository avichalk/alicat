"""Test configuraton parameters."""

from unittest import mock

import pytest

from alicat.basis import BASISMeter
from alicat.mock import BASISClient


def pytest_addoption(parser):
    parser.addoption("--hardware", action="store_true", help="Run hardware tests.")

@pytest.fixture(scope='module', autouse=True)
async def patch_serial_client(request):
    """Replace the serial client with our mock."""
    if request.config.getoption("--hardware"):
        ADDRESS = "COM16" # tests requite unit: A, baud: 38400
        async with BASISMeter(ADDRESS) as device:
            res = await device._write_and_read('A')
            if not res:
                pytest.exit("Device not found. Ensure device is connected " \
                "with unit id A and BAUD rate 38400 on the correct COM port.")
        yield
        async with BASISMeter(ADDRESS) as device:
            res = await device._write_and_read('AS 0')

    else:
        with mock.patch('alicat.basis.SerialClient', BASISClient):
            yield
