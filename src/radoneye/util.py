from __future__ import annotations

import math
import os
from struct import pack, unpack_from
from typing import cast

RADONEYE_ROUNDING_OFF = os.environ.get("RADONEYE_ROUNDING_OFF", "false") == "true"


def read_str_sz(buffer: bytearray, offset: int) -> str:
    # string length is encoded as first byte followed by string content with optional new line
    return buffer[(offset + 1) : (offset + 1 + buffer[offset])].decode()


def read_str(buffer: bytearray, offset: int, length: int) -> str:
    return buffer[(offset) : (offset + length)].decode()


def read_float(buffer: bytearray, offset: int) -> float:
    return float(unpack_from("<f", buffer, offset)[0])


def read_int(buffer: bytearray, offset: int) -> int:
    return unpack_from("<I", buffer, offset)[0]


def read_short(buffer: bytearray, offset: int) -> int:
    return unpack_from("<H", buffer, offset)[0]


def read_short_list(buffer: bytearray, offset: int, size: int) -> list[int]:
    return cast(list[int], unpack_from("<" + "H" * size, buffer, offset))


def encode_float(value: float) -> bytearray:
    return bytearray(pack("<f", value))


def encode_short(value: int | float) -> bytearray:
    value_to_pack = round(value) if isinstance(value, float) else value
    return bytearray(pack("<H", value_to_pack))


def read_bool(buffer: bytearray, offset: int) -> bool:
    return unpack_from("<c", buffer, offset)[0][0] == 0x01


def encode_bool(value: bool) -> bytearray:
    return bytearray([0x01 if value else 0x00])


def read_byte(buffer: bytearray, offset: int) -> int:
    return unpack_from("<c", buffer, offset)[0][0]


def encode_byte(value: int) -> bytearray:
    return bytearray(pack("<c", bytes([value])))


def round_pci_l(value_pci_l: float) -> float:
    if RADONEYE_ROUNDING_OFF:
        return value_pci_l
    return round(value_pci_l, 2)


def to_bq_m3(value_pci_l: float) -> float:
    if RADONEYE_ROUNDING_OFF:
        return value_pci_l * 37
    return round(value_pci_l * 37)


def to_pci_l(value_bq_m3: float) -> float:
    return round_pci_l(value_bq_m3 / 37)


def format_uptime(uptime_minutes: int) -> str:
    uptime_days = math.floor(uptime_minutes / (60 * 24))
    uptime_hours = math.floor(uptime_minutes % (60 * 24) / 60)
    uptime_mins = uptime_minutes % 60
    return f"{uptime_days}d{uptime_hours:02}h{uptime_mins:02}m"


def format_counts(counts_current: int, counts_previous: int) -> str:
    return f"{counts_current}/{counts_previous}"
