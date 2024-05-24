import math
from struct import unpack
from textwrap import wrap


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

def dump_data(data: bytearray, input: bool, debug: bool) -> bytearray:
    if debug:
        lines = [f"{line.ljust(48)}# {str(bytearray.fromhex(line))}" for line in wrap(data.hex(" "), width=48)]
        print(f"{"<-" if input else "->"} {"\n   ".join(lines)}")
    return data

def dump_in(data: bytearray, debug: bool) -> bytearray:
    return dump_data(data, True, debug)


def dump_out(data: bytearray, debug: bool) -> bytearray:
    return dump_data(data, False, debug)
