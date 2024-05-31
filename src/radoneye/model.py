from abc import abstractmethod
from typing import Literal, TypedDict


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
    alarm_enabled: int
    alarm_level_bq_m3: int
    alarm_level_pci_l: float
    alarm_interval_minutes: int


class RadonEyeHistory(TypedDict):
    values_bq_m3: list[int]
    values_pci_l: list[float]


RadonUnit = Literal["bq/m3", "pci/l"]


class RadonEyeInterface:
    @abstractmethod
    def supports(self) -> bool:
        raise NotImplementedError("Not supported method supports()")

    @abstractmethod
    async def status(self) -> RadonEyeStatus:
        raise NotImplementedError("Not supported method status()")

    @abstractmethod
    async def history(self) -> RadonEyeHistory:
        raise NotImplementedError("Not supported method history()")

    @abstractmethod
    async def beep(self) -> None:
        raise NotImplementedError("Not supported method beep()")

    @abstractmethod
    async def setup_alarm(
        self,
        enabled: bool,
        level: float,
        unit: RadonUnit,
        interval: int,
    ) -> None:
        raise NotImplementedError("Not supported method setup_alarm()")
