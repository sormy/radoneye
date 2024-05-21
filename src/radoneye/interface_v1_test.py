from struct import unpack

from inline_snapshot import snapshot

from radoneye.interface_v1 import RadonEyeMessageParserV1


def hex_to_float(buffer: bytes) -> float:
    return float(unpack("<f", buffer[0:4])[0])


def test_message_parser_v1():
    # triggered by command 0x10
    status_a4 = b"\xA4\x0E\x32\x30\x32\x30\x31\x32\x30\x32\x53\x4E\x30\x31\x35\x39\x08\x00\x00\x00"  # ??20201202SN0159????
    status_a8 = b"\xA8\x06\x05\x52\x44\x32\x30\x30\x30\x32\x53\x4E\x30\x31\x35\x39\x08\x00\x00\x00"  # ???RD20002SN0159????
    status_ac = b"\xAC\x07\x00\x00\x00\x00\x40\x40\x06\x32\x53\x4E\x30\x31\x35\x39\x08\x00\x00\x00"  # ?????????2SN0159????
    status_50 = b"\x50\x10\xE1\x7A\x14\x3F\xF6\x28\xBC\x3F\x00\x00\x00\x00\x01\x00\x04\x00\x00\x00"
    status_51 = b"\x51\x0E\x02\x00\xC1\x2D\x00\x00\x3E\x40\x08\x00\x50\xB1\x0C\x40\x04\x00\x00\x00"

    # triggered by command 0xA6
    status_a6 = b"\xA6\x03\x52\x55\x32\x32\x2E\x34\x0A\x66\x66\x86\x3F\xB1\x0C\x40\x04\x00\x00\x00"  # ??RU22??????????????

    # triggered by command 0xAF
    status_af = b"\xAF\x07\x56\x31\x2E\x32\x2E\x34\x0A\x66\x66\x86\x3F\xB1\x0C\x40\x04\x00\x00\x00"  # ??V1.2.4????????????

    result = RadonEyeMessageParserV1.parse_status(
        bytearray(status_50),
        bytearray(status_51),
        bytearray(status_a4),
        bytearray(status_a6),
        bytearray(status_a8),
        bytearray(status_af),
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
            "counts_current": 0,
            "counts_previous": 0,
            "counts_str": "?/?",
            "uptime_minutes": 11713,
            "uptime_str": "8d03h13m",
        }
    )
