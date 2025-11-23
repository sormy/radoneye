from __future__ import annotations

import asyncio
import math
from typing import TypedDict

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from radoneye.debug import dump_in, dump_out
from radoneye.model import RadonEyeHistory, RadonEyeInterface, RadonEyeStatus, RadonUnit
from radoneye.util import (
    encode_bool,
    encode_byte,
    encode_short,
    format_counts,
    format_uptime,
    read_bool,
    read_byte,
    read_int,
    read_short,
    read_short_list,
    read_str,
    to_bq_m3,
    to_pci_l,
)

SERVICE_UUID = "00001523-0000-1000-8000-00805f9b34fb"

CHAR_COMMAND = "00001524-0000-1000-8000-00805f9b34fb"
CHAR_STATUS = "00001525-0000-1000-8000-00805f9b34fb"
CHAR_HISTORY = "00001526-0000-1000-8000-00805f9b34fb"

COMMAND_STATUS = 0x40
COMMAND_HISTORY = 0x41
COMMAND_BEEP = 0xA1
COMMAND_SET_ALARM = 0xAA
COMMAND_SET_UNIT = 0xA2

INVOKE_DELAY = 0.2  # sec


class RadonEyeHistoryPage(TypedDict):
    page_count: int
    page_no: int
    value_count: int
    values_bq_m3: list[int]
    values_pci_l: list[float]


def parse_status(data: bytearray) -> RadonEyeStatus:
    if read_byte(data, 15) == 0x06:  # v2
        serial_part1 = read_str(data, 8, 3)  # series?
        serial_part2 = read_str(data, 2, 6)  # manufacturing date (YYMMDD)?
        serial_part3 = read_str(data, 11, 4)  # serial within manufacturing date?
        serial = serial_part1 + serial_part2 + serial_part3
        model = read_str(data, 16, 6)
    elif read_byte(data, 14) == 0x07:  # v3
        serial = read_str(data, 2, 12)
        model = read_str(data, 15, 7)
    else:
        serial = "unknown"
        model = "unknown"

    firmware_version = read_str(data, 22, 6)

    display_unit = "bq/m3" if read_bool(data, 28) else "pci/l"

    alarm_enabled = read_bool(data, 29)
    alarm_level_bq_m3 = read_short(data, 30)
    alarm_level_pci_l = to_pci_l(alarm_level_bq_m3)
    alarm_interval = read_byte(data, 32)
    alarm_interval_minutes = alarm_interval * 10

    latest_bq_m3 = read_short(data, 33)
    latest_pci_l = to_pci_l(latest_bq_m3)

    day_avg_bq_m3 = read_short(data, 35)
    day_avg_pci_l = to_pci_l(day_avg_bq_m3)

    month_avg_bq_m3 = read_short(data, 37)
    month_avg_pci_l = to_pci_l(month_avg_bq_m3)

    counts_current = read_short(data, 39)
    counts_previous = read_short(data, 41)
    counts_str = format_counts(counts_current, counts_previous)

    uptime_minutes = read_int(data, 43)
    uptime_str = format_uptime(uptime_minutes)

    peak_bq_m3 = read_short(data, 51)
    peak_pci_l = to_pci_l(peak_bq_m3)

    return {
        "serial": serial,
        "model": model,
        "firmware_version": firmware_version,
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
        "display_unit": display_unit,
        "alarm_enabled": alarm_enabled,
        "alarm_level_bq_m3": alarm_level_bq_m3,
        "alarm_level_pci_l": alarm_level_pci_l,
        "alarm_interval_minutes": alarm_interval_minutes,
    }


def parse_history_page(data: bytearray) -> RadonEyeHistoryPage:
    data.pop(0)  # command

    page_count = data.pop(0)
    page_no = data.pop(0)
    value_count = data.pop(0)
    values_bq_m3 = read_short_list(data, 0, len(data) // 2)
    values_pci_l = [to_pci_l(x) for x in values_bq_m3]

    return {
        "page_count": page_count,
        "page_no": page_no,
        "value_count": value_count,
        "values_bq_m3": values_bq_m3,
        "values_pci_l": values_pci_l,
    }


def merge_history(pages: list[RadonEyeHistoryPage]) -> RadonEyeHistory:
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


class InterfaceV2(RadonEyeInterface):
    def __init__(
        self,
        client: BleakClient,
        status_read_timeout: float | None = None,
        history_read_timeout: float | None = None,
        debug: bool = False,
    ):
        self.client = client
        self.status_read_timeout = status_read_timeout
        self.history_read_timeout = history_read_timeout
        self.debug = debug

    def supports(self) -> bool:
        return bool(self.client.services.get_service(SERVICE_UUID))

    async def status(self) -> RadonEyeStatus:
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
            # Early exit if already complete
            if future.done():
                return
            if data[0] == COMMAND_STATUS:
                future.set_result(parse_status(dump_in(data, self.debug)))

        await self.client.start_notify(CHAR_STATUS, callback)  # type: ignore
        await self.client.write_gatt_char(
            CHAR_COMMAND, dump_out(bytearray([COMMAND_STATUS]), self.debug)
        )
        result = await asyncio.wait_for(future, self.status_read_timeout)
        await self.client.stop_notify(CHAR_STATUS)
        return result

    async def history(self) -> RadonEyeHistory:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        pages: list[RadonEyeHistoryPage] = []

        def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
            # Early exit if already complete
            if future.done():
                return
            if data[0] == COMMAND_HISTORY:
                page = parse_history_page(dump_in(data, self.debug))
                pages.append(page)
                if page["page_count"] == page["page_no"]:
                    future.set_result(merge_history(pages))

        await self.client.start_notify(CHAR_HISTORY, callback)  # type: ignore
        await self.client.write_gatt_char(
            CHAR_COMMAND, dump_out(bytearray([COMMAND_HISTORY]), self.debug)
        )
        result = await asyncio.wait_for(future, self.history_read_timeout)
        await self.client.stop_notify(CHAR_HISTORY)
        return result

    async def beep(self) -> None:
        # RadonEye app writes longer command, but it is actually enough to send one byte to beep
        await self.client.write_gatt_char(
            CHAR_COMMAND, dump_out(bytearray([COMMAND_BEEP]), self.debug)
        )
        # there is some delay needed before you can do next beep, otherwise it will be just one beep
        await asyncio.sleep(INVOKE_DELAY)

    async def set_alarm(
        self,
        enabled: bool,
        level: float,
        unit: RadonUnit,
        interval: int,
    ) -> None:
        command = (
            bytearray([COMMAND_SET_ALARM, 0x11])
            + encode_bool(enabled)
            + encode_short(to_bq_m3(level) if unit == "pci/l" else level)
            + encode_byte(math.ceil(interval / 10))
        )
        await self.client.write_gatt_char(CHAR_COMMAND, dump_out(command, self.debug))
        await asyncio.sleep(INVOKE_DELAY)  # doesn't work without delay

    async def set_unit(self, unit: RadonUnit) -> None:
        command = bytearray([COMMAND_SET_UNIT, 0x11]) + encode_bool(
            False if unit == "pci/l" else True
        )
        await self.client.write_gatt_char(CHAR_COMMAND, dump_out(command, self.debug))
        await asyncio.sleep(INVOKE_DELAY)  # doesn't work without delay
