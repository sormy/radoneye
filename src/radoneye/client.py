from __future__ import annotations

from typing import Literal, Union

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from radoneye.interface_v1 import (
    retrieve_history_v1,
    retrieve_status_v1,
    supports_v1,
    trigger_beep_v1,
)
from radoneye.interface_v2 import (
    retrieve_history_v2,
    retrieve_status_v2,
    setup_alarm_v2,
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
    debug: bool

    def __init__(
        self,
        address_or_ble_device: Union[BLEDevice, str],
        connect_timeout: float = 10,
        status_read_timeout: float = 5,
        history_read_timeout: float = 60,
        adapter: str | None = None,
        debug: bool = False,
    ) -> None:
        self.client = BleakClient(address_or_ble_device, timout=connect_timeout, adapter=adapter)
        self.adapter = adapter
        self.connect_timeout = connect_timeout
        self.status_read_timeout = status_read_timeout
        self.history_read_timeout = history_read_timeout
        self.debug = debug

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
            return await trigger_beep_v1(self.client, self.debug)
        elif supports_v2(self.client):
            return await trigger_beep_v2(self.client, self.debug)
        else:
            raise NotImplementedError("Not supported device")

    async def status(self) -> RadonEyeStatus:
        if supports_v1(self.client):
            return await retrieve_status_v1(self.client, self.status_read_timeout, self.debug)
        elif supports_v2(self.client):
            return await retrieve_status_v2(self.client, self.status_read_timeout, self.debug)
        else:
            raise NotImplementedError("Not supported device")

    async def history(self) -> RadonEyeHistory:
        if supports_v1(self.client):
            return await retrieve_history_v1(
                self.client, self.status_read_timeout, self.history_read_timeout, self.debug
            )
        elif supports_v2(self.client):
            return await retrieve_history_v2(self.client, self.history_read_timeout, self.debug)
        else:
            raise NotImplementedError("Not supported device")

    async def alarm(
        self,
        enabled: bool,
        level: float,  # value in bq/m3 or pci/l
        unit: Literal["bq/m3", "pci/l"],
        interval: int,  # in minutes, app supports 10 mins, 1 hour and 6 hours
    ) -> None:
        if supports_v1(self.client):
            raise NotImplementedError("Not implemented yet")
        elif supports_v2(self.client):
            await setup_alarm_v2(
                self.client,
                enabled=enabled,
                level=level,
                unit=unit,
                interval=interval,
                debug=self.debug,
            )
        else:
            raise NotImplementedError("Not supported device")
