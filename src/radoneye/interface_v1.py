import asyncio
import math
from struct import unpack

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from radoneye.interface import RadonEyeHistory, RadonEyeInterfaceBase, RadonEyeStatus

SERVICE_V1 = "00001523-1212-efde-1523-785feabcd123"
CHARACTERISTIC_V1_COMMAND = "00001524-1212-efde-1523-785feabcd123"
CHARACTERISTIC_V1_STATUS = "00001525-1212-efde-1523-785feabcd123"
CHARACTERISTIC_V1_HISTORY = "00001526-1212-efde-1523-785feabcd123"
COMMAND_V1_STATUS_10 = [0x10]  # requests status A4, A8, AC, 50, 51
COMMAND_V1_STATUS_A6 = [0xA6]  # requests status A6
COMMAND_V1_STATUS_AF = [0xAF]  # requests status AF
COMMAND_V1_STATUS_50 = [0x50]  # requests status 50
COMMAND_V1_STATUS_51 = [0x51]  # requests status 51
COMMAND_V1_BEEP = [0xA1]  # triggers beep

BEEP_DELAY = 0.2  # sec


class RadonEyeMessageParserV1:
    @classmethod
    def parse_status(
        cls,
        status_50: bytearray,
        status_51: bytearray,
        status_a4: bytearray,
        status_a6: bytearray,
        status_a8: bytearray,
        status_af: bytearray,
    ) -> RadonEyeStatus:
        # Example: RU22012020159
        # part1 > RU2 -> hex: 52 55 32, status: a6, offset: 2, length: 3 bytes
        # part2 > 201202 -> hex: 32 30 31 32 30 32: status: a4, offset: 4, length: 6 bytes
        # part3 > 0159 -> hex: 30 31 35 39, status: a4, offset: 12, length: 4 bytes
        serial_part1 = status_a6[2:5].decode()
        serial_part2 = status_a4[4:10].decode()
        serial_part3 = status_a4[12:16].decode()
        serial = serial_part1 + serial_part2 + serial_part3

        model = status_a8[3:8].decode()

        version = status_af[2:8].decode()

        latest_value = float(unpack("<f", status_50[2:6])[0])
        latest_pci_l = round(latest_value, 2)
        latest_bq_m3 = round(latest_value * 37)

        day_avg_value = float(unpack("<f", status_50[6:10])[0])
        day_avg_pci_l = round(day_avg_value, 2)
        day_avg_bq_m3 = round(day_avg_value * 37)

        month_avg_value = float(unpack("<f", status_50[10:14])[0])
        month_avg_pci_l = round(month_avg_value, 2)
        month_avg_bq_m3 = round(month_avg_value * 37)

        peak_value = float(unpack("<f", status_51[12:16])[0])
        peak_pci_l = round(peak_value, 2)
        peak_bq_m3 = round(peak_value * 37)

        uptime_minutes = unpack("<I", status_51[4:8])[0]
        uptime_days = math.floor(uptime_minutes / (60 * 24))
        uptime_hours = math.floor(uptime_minutes % (60 * 24) / 60)
        uptime_mins = uptime_minutes % 60
        uptime_str = f"{uptime_days}d{uptime_hours:02}h{uptime_mins:02}m"

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
            "counts_current": 0,
            "counts_previous": 0,
            "counts_str": "?/?",
            "uptime_minutes": uptime_minutes,
            "uptime_str": uptime_str,
        }


class RadonEyeAdapterV1(RadonEyeInterfaceBase):
    status_read_timeout: float

    def __init__(self, status_read_timeout: float) -> None:
        self.status_read_timeout = status_read_timeout

    @classmethod
    def supports(cls, client: BleakClient) -> bool:
        return bool(client.services.get_service(SERVICE_V1))

    async def status(self, client: BleakClient) -> RadonEyeStatus:
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        status_50: bytearray | None = None
        status_51: bytearray | None = None
        status_a4: bytearray | None = None
        status_a6: bytearray | None = None
        status_a8: bytearray | None = None
        status_af: bytearray | None = None

        def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
            nonlocal status_50
            nonlocal status_51
            nonlocal status_a4
            nonlocal status_a6
            nonlocal status_a8
            nonlocal status_af

            if data[0] == 0x50:
                status_50 = data
            elif data[0] == 0x51:
                status_51 = data
            elif data[0] == 0xA4:
                status_a4 = data
            elif data[0] == 0xA6:
                status_a6 = data
            elif data[0] == 0xA8:
                status_a8 = data
            elif data[0] == 0xAF:
                status_af = data

            if status_50 and status_51 and status_a4 and status_a6 and status_a8 and status_af:
                status = RadonEyeMessageParserV1.parse_status(
                    status_50,
                    status_51,
                    status_a4,
                    status_a6,
                    status_a8,
                    status_af,
                )
                future.set_result(status)

        await client.start_notify(CHARACTERISTIC_V1_STATUS, callback)  # type: ignore
        await client.write_gatt_char(CHARACTERISTIC_V1_COMMAND, bytearray(COMMAND_V1_STATUS_10))
        await client.write_gatt_char(CHARACTERISTIC_V1_COMMAND, bytearray(COMMAND_V1_STATUS_A6))
        await client.write_gatt_char(CHARACTERISTIC_V1_COMMAND, bytearray(COMMAND_V1_STATUS_AF))
        result = await asyncio.wait_for(future, timeout=self.status_read_timeout)
        await client.stop_notify(CHARACTERISTIC_V1_STATUS)
        return result

    async def history(self, client: BleakClient) -> RadonEyeHistory:
        raise NotImplementedError

    async def beep(self, client: BleakClient) -> None:
        await client.write_gatt_char(CHARACTERISTIC_V1_COMMAND, bytearray(COMMAND_V1_BEEP))
        # there is some delay needed before you can do next beep, otherwise it will be just one beep
        await asyncio.sleep(BEEP_DELAY)
