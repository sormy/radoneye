import asyncio
from struct import unpack
from typing import TypedDict, cast

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from radoneye.model import RadonEyeHistory, RadonEyeStatus
from radoneye.util import format_counts, format_uptime, read_short, read_str, to_pci_l

SERVICE_UUID = "00001523-0000-1000-8000-00805f9b34fb"

CHAR_UUID_COMMAND = "00001524-0000-1000-8000-00805f9b34fb"
CHAR_UUID_STATUS = "00001525-0000-1000-8000-00805f9b34fb"
CHAR_UUID_HISTORY = "00001526-0000-1000-8000-00805f9b34fb"

COMMAND_STATUS = 0x40
COMMAND_HISTORY = 0x41
COMMAND_BEEP = 0xA1

BEEP_DELAY = 0.2  # sec


class RadonEyeHistoryPage(TypedDict):
    page_count: int
    page_no: int
    value_count: int
    values_bq_m3: list[int]
    values_pci_l: list[float]


def parse_status(data: bytearray) -> RadonEyeStatus:
    serial_part1 = read_str(data, 8, 3)  # series?
    serial_part2 = read_str(data, 2, 6)  # manufacturing date (YYMMDD)?
    serial_part3 = read_str(data, 11, 4)  # serial within manufacturing date?
    serial = serial_part1 + serial_part2 + serial_part3

    model = read_str(data, 16, 6)

    version = read_str(data, 22, 6)

    latest_bq_m3 = read_short(data, 33)
    latest_pci_l = to_pci_l(latest_bq_m3)

    day_avg_bq_m3 = read_short(data, 35)
    day_avg_pci_l = to_pci_l(day_avg_bq_m3)

    month_avg_bq_m3 = read_short(data, 37)
    month_avg_pci_l = to_pci_l(month_avg_bq_m3)

    counts_current = read_short(data, 39)
    counts_previous = read_short(data, 41)
    counts_str = format_counts(counts_current, counts_previous)

    uptime_minutes = read_short(data, 43)
    uptime_str = format_uptime(uptime_minutes)

    peak_bq_m3 = read_short(data, 51)
    peak_pci_l = to_pci_l(peak_bq_m3)

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


def parse_history_page(data: bytearray) -> RadonEyeHistoryPage:
    data.pop(0)  # command

    page_count = data.pop(0)
    page_no = data.pop(0)
    value_count = data.pop(0)
    values_bq_m3 = cast(list[int], unpack("<" + "H" * (len(data) // 2), data))
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


def supports_v2(client: BleakClient) -> bool:
    return bool(client.services.get_service(SERVICE_UUID))


async def retrieve_status_v2(client: BleakClient, timeout: float | None = None) -> RadonEyeStatus:
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
        if data[0] == COMMAND_STATUS:
            future.set_result(parse_status(data))

    await client.start_notify(CHAR_UUID_STATUS, callback)  # type: ignore
    await client.write_gatt_char(CHAR_UUID_COMMAND, bytearray([COMMAND_STATUS]))
    result = await asyncio.wait_for(future, timeout)
    await client.stop_notify(CHAR_UUID_STATUS)
    return result


async def retrieve_history_v2(client: BleakClient, timeout: float | None = None) -> RadonEyeHistory:
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    pages: list[RadonEyeHistoryPage] = []

    def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
        if data[0] == COMMAND_HISTORY:
            page = parse_history_page(data)
            pages.append(page)
            if page["page_count"] == page["page_no"]:
                future.set_result(merge_history(pages))

    await client.start_notify(CHAR_UUID_HISTORY, callback)  # type: ignore
    await client.write_gatt_char(CHAR_UUID_COMMAND, bytearray([COMMAND_HISTORY]))
    result = await asyncio.wait_for(future, timeout)
    await client.stop_notify(CHAR_UUID_HISTORY)
    return result


async def trigger_beep_v2(client: BleakClient) -> None:
    # RadonEye app writes longer command, but it is actually enough to send one byte to beep
    await client.write_gatt_char(CHAR_UUID_COMMAND, bytearray([COMMAND_BEEP]))
    # there is some delay needed before you can do next beep, otherwise it will be just one beep
    await asyncio.sleep(BEEP_DELAY)
