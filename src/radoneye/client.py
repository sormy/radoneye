from typing import Union

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from radoneye.interface_v1 import retrieve_status_v1, supports_v1, trigger_beep_v1
from radoneye.interface_v2 import (
    retrieve_history_v2,
    retrieve_status_v2,
    supports_v2,
    trigger_beep_v2,
)
from radoneye.model import RadonEyeHistory, RadonEyeStatus


class RadonEyeClient:
    client: BleakClient

    adapter: str | None
    connect_timeout: float
    status_read_timeout: float
    history_read_timeout: float

    def __init__(
        self,
        address_or_ble_device: Union[BLEDevice, str],
        connect_timeout: float = 10,
        status_read_timeout: float = 5,
        history_read_timeout: float = 60,
        adapter: str | None = None,
    ) -> None:
        self.client = BleakClient(address_or_ble_device, timout=connect_timeout, adapter=adapter)
        self.adapter = adapter
        self.connect_timeout = connect_timeout
        self.status_read_timeout = status_read_timeout
        self.history_read_timeout = history_read_timeout

    async def __aenter__(self):
        await self.client.connect()  # type: ignore
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        await self.client.disconnect()

    async def connect(self) -> None:
        await self.client.connect()  # type: ignore

    async def disconnect(self) -> None:
        await self.client.disconnect()  # type: ignore

    @property
    def is_connected(self) -> bool:
        return self.client.is_connected

    async def beep(self) -> None:
        if supports_v1(self.client):
            return await trigger_beep_v1(self.client)
        elif supports_v2(self.client):
            return await trigger_beep_v2(self.client)
        else:
            raise NotImplementedError("Not supported device")

    async def status(self) -> RadonEyeStatus:
        if supports_v1(self.client):
            return await retrieve_status_v1(self.client, self.status_read_timeout)
        elif supports_v2(self.client):
            return await retrieve_status_v2(self.client, self.status_read_timeout)
        else:
            raise NotImplementedError("Not supported device")

    async def history(self) -> RadonEyeHistory:
        if supports_v1(self.client):
            raise NotImplementedError("Not supported feature yet")
        elif supports_v2(self.client):
            return await retrieve_history_v2(self.client, self.history_read_timeout)
        else:
            raise NotImplementedError("Not supported device")
