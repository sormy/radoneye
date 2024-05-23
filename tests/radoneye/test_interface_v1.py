from typing import Any
from unittest.mock import MagicMock, call

import pytest
from bleak import BleakClient
from inline_snapshot import snapshot

from radoneye.interface_v1 import (
    CHAR_UUID_COMMAND,
    CHAR_UUID_HISTORY,
    CHAR_UUID_STATUS,
    COMMAND_BEEP,
    COMMAND_HISTORY,
    COMMAND_STATUS_10,
    COMMAND_STATUS_50,
    COMMAND_STATUS_51,
    COMMAND_STATUS_A6,
    COMMAND_STATUS_AF,
    COMMAND_STATUS_E8,
    parse_history_data,
    parse_history_size,
    parse_status,
    retrieve_history_v1,
    retrieve_status_v1,
    trigger_beep_v1,
)

# triggered by command 0x10
msg_a4 = b"\xA4\x0E\x32\x30\x32\x30\x31\x32\x30\x32\x53\x4E\x30\x31\x35\x39\x08\x00\x00\x00"  # ??20201202SN0159????
msg_a8 = b"\xA8\x06\x05\x52\x44\x32\x30\x30\x30\x32\x53\x4E\x30\x31\x35\x39\x08\x00\x00\x00"  # ???RD200????????????
msg_ac = b"\xAC\x07\x00\x00\x00\x00\x40\x40\x06\x32\x53\x4E\x30\x31\x35\x39\x08\x00\x00\x00"  # ??_______???????????
msg_50 = b"\x50\x10\xE1\x7A\x14\x3F\xF6\x28\xBC\x3F\x00\x00\x00\x00\x01\x00\x04\x00\x00\x00"  # ??________________??
msg_51 = b"\x51\x0E\x02\x00\xC1\x2D\x00\x00\x3E\x40\x08\x00\x50\xB1\x0C\x40\x04\x00\x00\x00"  # ??______________????

# triggered by command 0xAF
msg_af = b"\xAF\x07\x56\x31\x2E\x32\x2E\x34\x0A\x66\x66\x86\x3F\xB1\x0C\x40\x04\x00\x00\x00"  # ??V1.2.4_???????????

# triggered by command 0xA6
msg_a6 = b"\xA6\x03\x52\x55\x32\x32\x2E\x34\x0A\x66\x66\x86\x3F\xB1\x0C\x40\x04\x00\x00\x00"  # ??RU2???????????????

# triggered by command 0xE8 (history status)
msg_e8 = b"\xE8\x0B\x46\x00\x37\x29\x5C\x4F\x3F\x66\x66\x86\x3F\xB1\x0C\x40\x04\x00\x00\x00"  # ??___________???????

# triggered by command 0xE9 (history data)
msg_e9 = [
    bytes.fromhex(msg)
    for msg in [
        "85 00 46 00 5E 00 7C 00 85 00 5E 00 82 00 79 00 58 00 82 00"
        "8E 00 73 00 4F 00 61 00 93 00 8B 00 93 00 AE 00 9F 00 93 00"
        "82 00 8B 00 85 00 8E 00 67 00 79 00 79 00 85 00 A5 00 73 00"
        "A5 00 82 00 67 00 73 00 8B 00 70 00 46 00 6A 00 58 00 6A 00"
        "C3 00 6A 00 73 00 85 00 67 00 8E 00 93 00 79 00 B1 00 B7 00"
        "B7 00 BA 00 9C 00 9C 00 CC 00 82 00 61 00 58 00 96 00 8B 00"
        "8B 00 C0 00 A5 00 A8 00 73 00 70 00 61 00 4C 00 46 00 43 00"
    ]
]


@pytest.fixture
def bleak_client():
    status_callback: Any = None
    history_callback: Any = None

    def start_notify_side_effect(char: Any, callback: Any):
        nonlocal status_callback
        nonlocal history_callback
        if char == CHAR_UUID_STATUS:
            status_callback = callback
        elif char == CHAR_UUID_HISTORY:
            history_callback = callback

    def stop_notify_side_effect(char: Any):
        nonlocal status_callback
        nonlocal history_callback
        if char == CHAR_UUID_STATUS:
            status_callback = None
        elif char == CHAR_UUID_HISTORY:
            history_callback = None

    def write_gatt_char_side_effect(char: Any, data: bytearray):
        if status_callback is not None:
            if data[0] == COMMAND_STATUS_10:
                status_callback(char, bytearray(msg_a4))
                status_callback(char, bytearray(msg_a8))
                status_callback(char, bytearray(msg_ac))
                status_callback(char, bytearray(msg_50))
                status_callback(char, bytearray(msg_51))
            elif data[0] == COMMAND_STATUS_50:
                status_callback(char, bytearray(msg_50))
            elif data[0] == COMMAND_STATUS_51:
                status_callback(char, bytearray(msg_51))
            elif data[0] == COMMAND_STATUS_A6:
                status_callback(char, bytearray(msg_a6))
            elif data[0] == COMMAND_STATUS_AF:
                status_callback(char, bytearray(msg_af))
            elif data[0] == COMMAND_STATUS_E8:
                status_callback(char, bytearray(msg_e8))
        if history_callback is not None:
            if data[0] == COMMAND_HISTORY:
                for msg in msg_e9:
                    history_callback(char, bytearray(msg))

    client = MagicMock(BleakClient)

    client.start_notify.side_effect = start_notify_side_effect
    client.write_gatt_char.side_effect = write_gatt_char_side_effect
    client.stop_notify.side_effect = stop_notify_side_effect

    return client


def test_parse_status():
    result = parse_status(
        bytearray(msg_50),
        bytearray(msg_51),
        bytearray(msg_a4),
        bytearray(msg_a6),
        bytearray(msg_a8),
        bytearray(msg_af),
    )

    assert result == snapshot(
        {
            "serial": "RU22012020159",
            "model": "RD200",
            "version": "V1.2.4",
            "latest_bq_m3": 21,
            "latest_pci_l": 0.58,
            "day_avg_bq_m3": 54,
            "day_avg_pci_l": 1.47,
            "month_avg_bq_m3": 0,
            "month_avg_pci_l": 0.0,
            "peak_bq_m3": 81,
            "peak_pci_l": 2.2,
            "counts_current": 1,
            "counts_previous": 4,
            "counts_str": "1/4",
            "uptime_minutes": 11713,
            "uptime_str": "8d03h13m",
        }
    )


def test_parse_history():
    size = parse_history_size(bytearray(msg_e8))
    result = parse_history_data(bytearray(b"".join(msg_e9)), size)
    assert result["values_bq_m3"][:10] == snapshot([49, 26, 35, 46, 49, 35, 48, 45, 32, 48])
    assert result["values_pci_l"][:10] == snapshot(
        [1.32, 0.7, 0.93, 1.23, 1.32, 0.93, 1.29, 1.2, 0.87, 1.29]
    )


@pytest.mark.asyncio
async def test_retrieve_status(bleak_client: Any):
    result = await retrieve_status_v1(bleak_client, timeout=1)

    assert bleak_client.start_notify.mock_calls[0].args[0] == CHAR_UUID_STATUS
    assert bleak_client.stop_notify.mock_calls[0].args[0] == CHAR_UUID_STATUS

    assert bleak_client.write_gatt_char.mock_calls == [
        call(CHAR_UUID_COMMAND, bytearray([COMMAND_STATUS_10])),
        call(CHAR_UUID_COMMAND, bytearray([COMMAND_STATUS_AF])),
        call(CHAR_UUID_COMMAND, bytearray([COMMAND_STATUS_A6])),
    ]

    assert result == snapshot(
        {
            "serial": "RU22012020159",
            "model": "RD200",
            "version": "V1.2.4",
            "latest_bq_m3": 21,
            "latest_pci_l": 0.58,
            "day_avg_bq_m3": 54,
            "day_avg_pci_l": 1.47,
            "month_avg_bq_m3": 0,
            "month_avg_pci_l": 0.0,
            "peak_bq_m3": 81,
            "peak_pci_l": 2.2,
            "counts_current": 1,
            "counts_previous": 4,
            "counts_str": "1/4",
            "uptime_minutes": 11713,
            "uptime_str": "8d03h13m",
        }
    )


@pytest.mark.asyncio
async def test_retrieve_history(bleak_client: Any):
    result = await retrieve_history_v1(bleak_client, status_timeout=1, history_timeout=1)

    assert bleak_client.start_notify.mock_calls[0].args[0] == CHAR_UUID_STATUS
    assert bleak_client.stop_notify.mock_calls[0].args[0] == CHAR_UUID_STATUS

    assert bleak_client.start_notify.mock_calls[1].args[0] == CHAR_UUID_HISTORY
    assert bleak_client.stop_notify.mock_calls[1].args[0] == CHAR_UUID_HISTORY

    assert bleak_client.write_gatt_char.mock_calls == [
        call(CHAR_UUID_COMMAND, bytearray([COMMAND_STATUS_E8])),
        call(CHAR_UUID_COMMAND, bytearray([COMMAND_HISTORY])),
    ]

    expected_size = parse_history_size(bytearray(msg_e8))
    expected_result = parse_history_data(bytearray(b"".join(msg_e9)), expected_size)

    assert result == expected_result


@pytest.mark.asyncio
async def test_trigger_beep(bleak_client: Any):
    await trigger_beep_v1(bleak_client)

    assert bleak_client.write_gatt_char.mock_calls == [
        call(CHAR_UUID_COMMAND, bytearray([COMMAND_BEEP]))
    ]
