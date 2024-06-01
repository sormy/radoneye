from unittest.mock import AsyncMock, patch

import pytest
from bleak.backends.device import BLEDevice

from radoneye.scanner import RadonEyeScanner


@patch("bleak.BleakScanner.discover")
@pytest.mark.asyncio
async def test_discover(mock_discover: AsyncMock):
    dev1 = BLEDevice("70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9", "FR:RU22201030383", None, 0)
    dev2 = BLEDevice("3775964E-C653-C00C-7F02-7C03F9F0122D", "FR:RU22204180050", None, 0)
    dev3 = BLEDevice("12345678-1234-1234-1234-123456789012", "FX:RU22204180050", None, 0)

    mock_discover.return_value = [dev1, dev2, dev3]

    result = await RadonEyeScanner.discover()
    assert result == [dev1, dev2]
