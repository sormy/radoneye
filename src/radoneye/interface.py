from abc import abstractmethod
from typing import TypedDict

from bleak import BleakClient


class RadonEyeStatus(TypedDict):
    serial: str
    model: str
    version: str
    latest_bq_m3: int
    latest_pci_l: float
    day_avg_bq_m3: int
    day_avg_pci_l: float
    month_avg_bq_m3: int
    month_avg_pci_l: float
    peak_bq_m3: int
    peak_pci_l: float
    counts_current: int
    counts_previous: int
    counts_str: str
    uptime_minutes: int
    uptime_str: str


class RadonEyeHistoryPage(TypedDict):
    page_count: int
    page_no: int
    value_count: int
    values_bq_m3: list[int]
    values_pci_l: list[float]


class RadonEyeHistory(TypedDict):
    values_bq_m3: list[int]
    values_pci_l: list[float]


class RadonEyeInterfaceBase:
    @classmethod
    @abstractmethod
    def supports(cls, client: BleakClient) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def status(self, client: BleakClient) -> RadonEyeStatus:
        raise NotImplementedError

    @abstractmethod
    async def history(self, client: BleakClient) -> RadonEyeHistory:
        raise NotImplementedError

    @abstractmethod
    async def beep(self, client: BleakClient) -> None:
        raise NotImplementedError
