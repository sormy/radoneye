import math
from struct import pack, unpack


def read_str_sz(buffer: bytearray, offset: int) -> str:
    # string length is encoded as first byte followed by string content with optional new line
    return buffer[(offset + 1) : (offset + 1 + buffer[offset])].decode()


def read_str(buffer: bytearray, offset: int, length: int) -> str:
    return buffer[(offset) : (offset + length)].decode()


def read_float(buffer: bytearray, offset: int) -> float:
    return float(unpack("<f", buffer[offset : (offset + 4)])[0])


def read_int(buffer: bytearray, offset: int) -> int:
    return unpack("<I", buffer[offset : (offset + 4)])[0]


def read_short(buffer: bytearray, offset: int) -> int:
    return unpack("<H", buffer[offset : (offset + 2)])[0]


def read_short_list(buffer: bytearray, offset: int, size: int) -> list[int]:
    if offset == 0 and len(buffer) == size * 2:
        return unpack("<" + "H" * size, buffer)
    return unpack("<" + "H" * size, buffer[offset : (size * 2)])


def encode_short(value: int) -> bytearray:
    return bytearray(pack("<H", value))


def read_bool(buffer: bytearray, offset: int) -> bool:
    return unpack("<c", buffer[offset : (offset + 1)])[0][0] == 0x01


def encode_bool(value: bool) -> bytearray:
    return bytearray([0x01 if value else 0x00])


def read_byte(buffer: bytearray, offset: int) -> int:
    return unpack("<c", buffer[offset : (offset + 1)])[0][0]


def encode_byte(value: int) -> bytearray:
    return bytearray(pack("<c", bytes([value])))


def round_pci_l(value_pci_l: float) -> float:
    return round(value_pci_l, 2)


def to_bq_m3(value_pci_l: float) -> int:
    return round(value_pci_l * 37)


def to_pci_l(value_bq_m3: int) -> float:
    return round_pci_l(value_bq_m3 / 37)


def format_uptime(uptime_minutes: int) -> str:
    uptime_days = math.floor(uptime_minutes / (60 * 24))
    uptime_hours = math.floor(uptime_minutes % (60 * 24) / 60)
    uptime_mins = uptime_minutes % 60
    return f"{uptime_days}d{uptime_hours:02}h{uptime_mins:02}m"


def format_counts(counts_current: int, counts_previous: int) -> str:
    return f"{counts_current}/{counts_previous}"
