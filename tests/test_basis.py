"""Test the BASIS devices/driver respond with correct data."""
import pytest

from alicat.basis import BASISMeter  #, BASISController

ADDRESS = "COM16" # tests requite unit: A, baud: 38400

@pytest.fixture(scope='session', autouse=True)
async def precondition():
    """Exit if com port inaccessible or device not found."""
    async with BASISMeter(ADDRESS) as device:
        res = await device._write_and_read('A')
        if not res:
            pytest.exit("Ensure device is connected on correct port.")

@pytest.mark.skip # broken on 3.9
@pytest.mark.parametrize('cls', [BASISMeter])  # Fixme: fix FlowMeter
async def test_is_connected(cls):
    """Confirm that connection status works."""
    async with cls(ADDRESS) as device:
        assert await device.is_connected(ADDRESS)
        assert not await device.is_connected('bad_address')

@pytest.mark.parametrize('gas', ['Air', 'H2'])
async def test_set_standard_gas_name(gas):
    """Confirm that setting standard gases by name works."""
    async with BASISMeter(ADDRESS) as device:
        await device.set_gas(gas)
        result = await device.get()
        assert gas == result['gas']
        with pytest.raises(ValueError, match='not supported'):
            await device.set_gas('methylacetylene-propadiene propane')

@pytest.mark.parametrize('gas', [('Air', 0), ('Ar', 1)])
async def test_set_standard_gas_number(gas):
    """Confirm that setting standard gases by number works."""
    async with BASISMeter(ADDRESS) as device:
        await device.set_gas(gas[1])
        result = await device.get()
        assert gas[0] == result['gas']

