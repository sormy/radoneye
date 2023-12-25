from typing import Union

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from radoneye.interface import RadonEyeHistory, RadonEyeInterfaceBase, RadonEyeStatus
from radoneye.interface_factory import RadonEyeInterfaceFactory


class RadonEyeClient:
    client: BleakClient
    api: RadonEyeInterfaceBase

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

    def __init_api(self) -> None:
        self.api = RadonEyeInterfaceFactory.create(
            self.client,
            status_read_timeout=self.status_read_timeout,
            history_read_timeout=self.history_read_timeout,
        )

    async def __aenter__(self):
        await self.client.connect()  # type: ignore
        self.__init_api()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        await self.client.disconnect()

    async def connect(self) -> None:
        await self.client.connect()  # type: ignore
        self.__init_api()

    async def disconnect(self) -> None:
        await self.client.disconnect()  # type: ignore

    @property
    def is_connected(self) -> bool:
        return self.client.is_connected

    async def beep(self) -> None:
        await self.api.beep(self.client)

    async def status(self) -> RadonEyeStatus:
        return await self.api.status(self.client)

    async def history(self) -> RadonEyeHistory:
        return await self.api.history(self.client)
