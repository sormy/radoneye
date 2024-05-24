import asyncio
import math
from struct import unpack
from typing import cast

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from radoneye.debug import dump_in, dump_out
from radoneye.model import RadonEyeHistory, RadonEyeStatus
from radoneye.util import (
    format_counts,
    format_uptime,
    read_float,
    read_int,
    read_short,
    read_str_sz,
    round_pci_l,
    to_bq_m3,
)

SERVICE_UUID = "00001523-1212-efde-1523-785feabcd123"

CHAR_COMMAND = "00001524-1212-efde-1523-785feabcd123"
CHAR_STATUS = "00001525-1212-efde-1523-785feabcd123"
CHAR_HISTORY = "00001526-1212-efde-1523-785feabcd123"

COMMAND_STATUS_10 = 0x10  # requests message A4, A8, AC, 50, 51
COMMAND_STATUS_A6 = 0xA6  # requests message A6
COMMAND_STATUS_AF = 0xAF  # requests message AF
COMMAND_STATUS_50 = 0x50  # requests message 50
COMMAND_STATUS_51 = 0x51  # requests message 51
COMMAND_STATUS_E8 = 0xE8  # requests message E8 (history metadata)

COMMAND_HISTORY = 0xE9

COMMAND_BEEP = 0xA1

MSG_PREAMBLE_50 = 0x50
MSG_PREAMBLE_51 = 0x51
MSG_PREAMBLE_A4 = 0xA4
MSG_PREAMBLE_A6 = 0xA6
MSG_PREAMBLE_A8 = 0xA8
MSG_PREAMBLE_AF = 0xAF
MSG_PREAMBLE_E8 = 0xE8

BEEP_DELAY = 0.2  # sec


def parse_status(
    msg_50: bytearray,
    msg_51: bytearray,
    msg_a4: bytearray,
    msg_a6: bytearray,
    msg_a8: bytearray,
    msg_af: bytearray,
) -> RadonEyeStatus:
    # Most messages start with command code followed by byte representing length of data inside buffer
    # buffer has at most 20 bytes (including command code), unused buffer part can contain "trash".

    serial_part1 = read_str_sz(msg_a6, offset=1)  # series?
    serial_part2 = read_str_sz(msg_a4, offset=1)[2:8]  # manufacturing date (YYMMDD)?
    serial_part3 = read_str_sz(msg_a4, offset=1)[-4:]  # serial within manufacturing date?
    serial = serial_part1 + serial_part2 + serial_part3  # example: {RU2}{201202}{0159}

    model = read_str_sz(msg_a8, offset=2)

    version = read_str_sz(msg_af, offset=1).rstrip()  # value has useless trailing new line

    latest_value = read_float(msg_50, offset=2)
    latest_pci_l = round_pci_l(latest_value)
    latest_bq_m3 = to_bq_m3(latest_value)

    day_avg_value = read_float(msg_50, offset=6)
    day_avg_pci_l = round_pci_l(day_avg_value)
    day_avg_bq_m3 = to_bq_m3(day_avg_value)

    month_avg_value = read_float(msg_50, offset=10)
    month_avg_pci_l = round_pci_l(month_avg_value)
    month_avg_bq_m3 = to_bq_m3(month_avg_value)

    counts_current = read_short(msg_50, 14)  # is it correct?
    counts_previous = read_short(msg_50, 16)  # is it correct?
    counts_str = format_counts(counts_current, counts_previous)

    uptime_minutes = read_int(msg_51, offset=4)
    uptime_str = format_uptime(uptime_minutes)

    peak_value = read_float(msg_51, offset=12)
    peak_pci_l = round_pci_l(peak_value)
    peak_bq_m3 = to_bq_m3(peak_value)

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


def parse_history_size(msg_e8: bytearray) -> int:
    return read_short(msg_e8, 2)


def parse_history_data(msg_e9: bytearray, size: int) -> RadonEyeHistory:
    values = cast(list[int], unpack("<" + "H" * size, msg_e9))
    values_pci_l = [v / 37 / math.e for v in values]
    return {
        "values_bq_m3": [to_bq_m3(v) for v in values_pci_l],
        "values_pci_l": [round_pci_l(v) for v in values_pci_l],
    }


def supports_v1(client: BleakClient) -> bool:
    return bool(client.services.get_service(SERVICE_UUID))


async def retrieve_status_v1(
    client: BleakClient,
    timeout: float | None = None,
    debug: bool = False,
) -> RadonEyeStatus:
    loop = asyncio.get_running_loop()

    future = loop.create_future()

    msg_50: bytearray | None = None
    msg_51: bytearray | None = None
    msg_a4: bytearray | None = None
    msg_a6: bytearray | None = None
    msg_a8: bytearray | None = None
    msg_af: bytearray | None = None

    def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
        nonlocal msg_50
        nonlocal msg_51
        nonlocal msg_a4
        nonlocal msg_a6
        nonlocal msg_a8
        nonlocal msg_af

        if data[0] == MSG_PREAMBLE_50:
            msg_50 = dump_in(data, debug)
        elif data[0] == MSG_PREAMBLE_51:
            msg_51 = dump_in(data, debug)
        elif data[0] == MSG_PREAMBLE_A4:
            msg_a4 = dump_in(data, debug)
        elif data[0] == MSG_PREAMBLE_A6:
            msg_a6 = dump_in(data, debug)
        elif data[0] == MSG_PREAMBLE_A8:
            msg_a8 = dump_in(data, debug)
        elif data[0] == MSG_PREAMBLE_AF:
            msg_af = dump_in(data, debug)

        if msg_50 and msg_51 and msg_a4 and msg_a6 and msg_a8 and msg_af:
            status = parse_status(
                msg_50,
                msg_51,
                msg_a4,
                msg_a6,
                msg_a8,
                msg_af,
            )
            future.set_result(status)

    await client.start_notify(CHAR_STATUS, callback)  # type: ignore
    await client.write_gatt_char(CHAR_COMMAND, dump_out(bytearray([COMMAND_STATUS_10]), debug))
    await client.write_gatt_char(CHAR_COMMAND, dump_out(bytearray([COMMAND_STATUS_AF]), debug))
    await client.write_gatt_char(CHAR_COMMAND, dump_out(bytearray([COMMAND_STATUS_A6]), debug))
    result = await asyncio.wait_for(future, timeout)
    await client.stop_notify(CHAR_STATUS)
    return result


async def retrieve_history_v1(
    client: BleakClient,
    status_timeout: float | None = None,
    history_timeout: float | None = None,
    debug: bool = False,
) -> RadonEyeHistory:
    loop = asyncio.get_running_loop()

    size_future = loop.create_future()
    result_future = loop.create_future()

    result_size: int = -1
    result_data = bytearray()

    def callback_status(char: BleakGATTCharacteristic, data: bytearray) -> None:
        nonlocal result_size
        if data[0] == MSG_PREAMBLE_E8:
            size_future.set_result(parse_history_size(dump_in(data, debug)))

    def callback_history(char: BleakGATTCharacteristic, data: bytearray) -> None:
        nonlocal result_data
        result_data.extend(dump_in(data, debug))
        if len(result_data) >= result_size:
            result_future.set_result(parse_history_data(result_data, result_size))

    await client.start_notify(CHAR_STATUS, callback_status)  # type: ignore
    await client.write_gatt_char(CHAR_COMMAND, dump_out(bytearray([COMMAND_STATUS_E8]), debug))
    result_size = await asyncio.wait_for(size_future, status_timeout)
    await client.stop_notify(CHAR_STATUS)

    if result_size == 0:
        result = RadonEyeHistory(values_bq_m3=[], values_pci_l=[])
    else:
        await client.start_notify(CHAR_HISTORY, callback_history)  # type: ignore
        await client.write_gatt_char(CHAR_COMMAND, dump_out(bytearray([COMMAND_HISTORY]), debug))
        result = await asyncio.wait_for(result_future, history_timeout)
        await client.stop_notify(CHAR_HISTORY)

    return result


async def trigger_beep_v1(client: BleakClient, debug: bool = False) -> None:
    # RadonEye app writes longer command, but it is actually enough to send one byte to beep
    await client.write_gatt_char(CHAR_COMMAND, dump_out(bytearray([COMMAND_BEEP]), debug))
    # there is some delay needed before you can do next beep, otherwise it will be just one beep
    await asyncio.sleep(BEEP_DELAY)
