from __future__ import annotations

from typing import Union

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from radoneye.interface_v1 import InterfaceV1
from radoneye.interface_v2 import InterfaceV2
from radoneye.model import RadonEyeHistory, RadonEyeInterface, RadonEyeStatus, RadonUnit


class RadonEyeClient:
    def __init__(
        self,
        address_or_ble_device: Union[BLEDevice, str],
        connect_timeout: float = 30,
        status_read_timeout: float = 5,
        history_read_timeout: float = 60,
        adapter: str | None = None,
        debug: bool = False,
    ) -> None:
        self.client = BleakClient(address_or_ble_device, timeout=connect_timeout, adapter=adapter)
        self.interface: RadonEyeInterface | None = None
        self.status_read_timeout = status_read_timeout
        self.history_read_timeout = history_read_timeout
        self.adapter = adapter
        self.debug = debug

    async def __aenter__(self):
        await self.client.connect()  # type: ignore
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        try:
            await self.client.disconnect()
        except (EOFError, Exception):
            # Ignore errors during disconnect - connection may already be closed
            pass

    async def connect(self) -> None:
        await self.client.connect()  # type: ignore

    async def disconnect(self) -> None:
        try:
            await self.client.disconnect()  # type: ignore
        except (EOFError, Exception):
            # Ignore errors during disconnect - connection may already be closed
            pass

    @property
    def is_connected(self) -> bool:
        return self.client.is_connected

    async def beep(self) -> None:
        return await self.__get_interface().beep()

    async def status(self) -> RadonEyeStatus:
        return await self.__get_interface().status()

    async def history(self) -> RadonEyeHistory:
        return await self.__get_interface().history()

    async def set_alarm(
        self,
        enabled: bool,  # even when disabled, we still need to provide alarm configuration
        level: float,  # value in bq/m3 or pci/l
        unit: RadonUnit,  # bq/m3 or pci/l
        interval: int,  # in minutes, app supports 10 mins, 1 hour and 6 hours
    ) -> None:
        return await self.__get_interface().set_alarm(enabled, level, unit, interval)

    async def set_unit(self, unit: RadonUnit) -> None:
        return await self.__get_interface().set_unit(unit)

    def __get_interface(self) -> RadonEyeInterface:
        if self.interface:
            return self.interface

        for InterfaceClass in [InterfaceV2, InterfaceV1]:
            interface = InterfaceClass(
                client=self.client,
                status_read_timeout=self.status_read_timeout,
                history_read_timeout=self.history_read_timeout,
                debug=self.debug,
            )
            if interface.supports():
                self.interface = interface
                return interface

        raise NotImplementedError("Not supported device")
