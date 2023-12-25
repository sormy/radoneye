from bleak import BleakScanner
from bleak.backends.device import BLEDevice

RADONEYE_NAME_PREFIX = "FR:"


class RadonEyeScanner:
    @classmethod
    async def discover(
        cls,
        timeout: float = 5,
        adapter: str | None = None,
    ) -> list[BLEDevice]:
        devices = await BleakScanner.discover(timeout=timeout, adapter=adapter)  # type: ignore
        return [dev for dev in devices if dev.name and dev.name.startswith(RADONEYE_NAME_PREFIX)]
