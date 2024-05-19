import asyncio
import math
from struct import unpack
from typing import cast

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from radoneye.interface import (
    RadonEyeHistory,
    RadonEyeHistoryPage,
    RadonEyeInterfaceBase,
    RadonEyeStatus,
)

SERVICE_V2 = "00001523-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_V2_COMMAND = "00001524-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_V2_STATUS = "00001525-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_V2_HISTORY = "00001526-0000-1000-8000-00805f9b34fb"
COMMAND_V2_STATUS = [0x40]
COMMAND_V2_HISTORY = [0x41]
COMMAND_V2_BEEP = [0xA1, 0x11]

BEEP_DELAY = 0.2  # sec


class RadonEyeMessageParserV2:
    @classmethod
    def read_short(cls, data: bytearray, start: int) -> int:
        return unpack("<H", data[slice(start, start + 2)])[0]

    @classmethod
    def read_str(cls, data: bytearray, start: int, length: int) -> str:
        return data[slice(start, start + length)].decode()

    @classmethod
    def to_pci_l(cls, value_bq_m3: int) -> float:
        return round(value_bq_m3 / 37, 2)

    @classmethod
    def parse_status(cls, data: bytearray) -> RadonEyeStatus:
        serial = cls.read_str(data, 8, 3) + cls.read_str(data, 2, 6) + cls.read_str(data, 11, 4)
        model = cls.read_str(data, 16, 6)
        version = cls.read_str(data, 22, 6)
        latest_bq_m3 = cls.read_short(data, 33)
        latest_pci_l = cls.to_pci_l(latest_bq_m3)
        day_avg_bq_m3 = cls.read_short(data, 35)
        day_avg_pci_l = cls.to_pci_l(day_avg_bq_m3)
        month_avg_bq_m3 = cls.read_short(data, 37)
        month_avg_pci_l = cls.to_pci_l(month_avg_bq_m3)
        counts_current = cls.read_short(data, 39)
        counts_previous = cls.read_short(data, 41)
        counts_str = f"{counts_current}/{counts_previous}"
        uptime_minutes = cls.read_short(data, 43)
        uptime_days = math.floor(uptime_minutes / (60 * 24))
        uptime_hours = math.floor(uptime_minutes % (60 * 24) / 60)
        uptime_mins = uptime_minutes % 60
        uptime_str = f"{uptime_days}d{uptime_hours:02}h{uptime_mins:02}m"
        peak_bq_m3 = cls.read_short(data, 51)
        peak_pci_l = cls.to_pci_l(peak_bq_m3)

        return {
            "serial": serial,
            "model": model,
            "version": version,
            "latest_bq_m3": latest_bq_m3,
            "latest_pci_l": latest_pci_l,
            "day_avg_bq_m3": day_avg_bq_m3,
            "day_avg_pci_l": day_avg_pci_l,
            "month_avg_bq_m3": month_avg_bq_m3,
            "month_avg_pci_l": month_avg_pci_l,
            "peak_bq_m3": peak_bq_m3,
            "peak_pci_l": peak_pci_l,
            "counts_current": counts_current,
            "counts_previous": counts_previous,
            "counts_str": counts_str,
            "uptime_minutes": uptime_minutes,
            "uptime_str": uptime_str,
        }

    @classmethod
    def parse_history_page(cls, data: bytearray) -> RadonEyeHistoryPage:
        data.pop(0)  # command

        page_count = data.pop(0)
        page_no = data.pop(0)
        value_count = data.pop(0)
        values_bq_m3 = cast(list[int], unpack("<" + "H" * (len(data) // 2), data))
        values_pci_l = [cls.to_pci_l(x) for x in values_bq_m3]

        return {
            "page_count": page_count,
            "page_no": page_no,
            "value_count": value_count,
            "values_bq_m3": values_bq_m3,
            "values_pci_l": values_pci_l,
        }

    @classmethod
    def merge_history(cls, pages: list[RadonEyeHistoryPage]) -> RadonEyeHistory:
        pages = sorted(pages, key=lambda page: page["page_no"])
        if pages:
            for index, page in enumerate(pages):
                if index + 1 != page["page_no"]:
                    raise ValueError("History page order mismatch")
            if pages[0]["page_count"] != len(pages):
                raise ValueError("History page count mismatch")
        return {
            "values_bq_m3": [value for page in pages for value in page["values_bq_m3"]],
            "values_pci_l": [value for page in pages for value in page["values_pci_l"]],
        }


class RadonEyeAdapterV2(RadonEyeInterfaceBase):
    status_read_timeout: float
    history_read_timeout: float

    def __init__(self, status_read_timeout: float, history_read_timeout: float) -> None:
        self.status_read_timeout = status_read_timeout
        self.history_read_timeout = history_read_timeout

    @classmethod
    def supports(cls, client: BleakClient) -> bool:
        return bool(client.services.get_service(SERVICE_V2))

    async def status(self, client: BleakClient) -> RadonEyeStatus:
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
            if data[0] == COMMAND_V2_STATUS[0]:
                future.set_result(RadonEyeMessageParserV2.parse_status(data))

        await client.start_notify(CHARACTERISTIC_V2_STATUS, callback)  # type: ignore
        await client.write_gatt_char(CHARACTERISTIC_V2_COMMAND, bytearray(COMMAND_V2_STATUS))
        result = await asyncio.wait_for(future, timeout=self.status_read_timeout)
        await client.stop_notify(CHARACTERISTIC_V2_STATUS)
        return result

    async def history(self, client: BleakClient) -> RadonEyeHistory:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        pages: list[RadonEyeHistoryPage] = []

        def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
            if data[0] == COMMAND_V2_HISTORY[0]:
                page = RadonEyeMessageParserV2.parse_history_page(data)
                pages.append(page)
                if page["page_count"] == page["page_no"]:
                    future.set_result(RadonEyeMessageParserV2.merge_history(pages))

        await client.start_notify(CHARACTERISTIC_V2_HISTORY, callback)  # type: ignore
        await client.write_gatt_char(CHARACTERISTIC_V2_COMMAND, bytearray(COMMAND_V2_HISTORY))
        result = await asyncio.wait_for(future, timeout=self.history_read_timeout)
        await client.stop_notify(CHARACTERISTIC_V2_HISTORY)
        return result

    async def beep(self, client: BleakClient) -> None:
        await client.write_gatt_char(CHARACTERISTIC_V2_COMMAND, bytearray(COMMAND_V2_BEEP))
        # there is some delay needed before you can do next beep, otherwise it will be just one beep
        await asyncio.sleep(BEEP_DELAY)
