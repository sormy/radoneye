import asyncio
import math
from struct import unpack

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from radoneye.interface import RadonEyeHistory, RadonEyeInterfaceBase, RadonEyeStatus

SERVICE_V1 = "00001523-1212-efde-1523-785feabcd123"
CHARACTERISTIC_V1_COMMAND = "00001524-1212-efde-1523-785feabcd123"
CHARACTERISTIC_V1_STATUS = "00001525-1212-efde-1523-785feabcd123"
COMMAND_V1_STATUS1 = [0x50]
COMMAND_V1_STATUS2 = [0x51]
COMMAND_V1_BEEP = [0xA1, 0x11]

BEEP_DELAY = 0.2  # sec


class RadonEyeMessageParserV1:
    @classmethod
    def parse_status(cls, data: bytearray, data2: bytearray, addr: str) -> RadonEyeStatus:
        latest_value = float(unpack("<f", data[2:6])[0])
        latest_pci_l = round(latest_value, 2)
        latest_bq_m3 = round(latest_value * 37)

        day_avg_value = float(unpack("<f", data[6:10])[0])
        day_avg_pci_l = round(day_avg_value, 2)
        day_avg_bq_m3 = round(day_avg_value * 37)

        month_avg_value = float(unpack("<f", data[10:14])[0])
        month_avg_pci_l = round(month_avg_value, 2)
        month_avg_bq_m3 = round(month_avg_value * 37)

        peak_value = float(unpack("<f", data2[12:16])[0])
        peak_pci_l = round(peak_value, 2)
        peak_bq_m3 = round(peak_value * 37)

        uptime_minutes = unpack("<I", data2[4:8])[0]
        uptime_days = math.floor(uptime_minutes / (60 * 24))
        uptime_hours = math.floor(uptime_minutes % (60 * 24) / 60)
        uptime_mins = uptime_minutes % 60
        uptime_str = f"{uptime_days}d{uptime_hours:02}h{uptime_mins:02}m"

        return {
            # serial is needed since it is used as unique device id
            # in absense of true serial, we have to use device address
            "serial": addr.replace(":", "").replace("-", "").upper(),
            "model": "RD200",
            "version": "?",
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
        data1: bytearray | None = None
        data2: bytearray | None = None

        def callback(char: BleakGATTCharacteristic, data: bytearray) -> None:
            nonlocal data1
            nonlocal data2
            if data[0] == COMMAND_V1_STATUS1[0]:
                data1 = data
            elif data[0] == COMMAND_V1_STATUS2[0]:
                data2 = data
            if data1 and data2:
                status = RadonEyeMessageParserV1.parse_status(data1, data2, client.address)
                future.set_result(status)

        await client.start_notify(CHARACTERISTIC_V1_STATUS, callback)  # type: ignore
        await client.write_gatt_char(CHARACTERISTIC_V1_COMMAND, bytearray(COMMAND_V1_STATUS1))
        await client.write_gatt_char(CHARACTERISTIC_V1_COMMAND, bytearray(COMMAND_V1_STATUS2))
        result = await asyncio.wait_for(future, timeout=self.status_read_timeout)
        await client.stop_notify(CHARACTERISTIC_V1_STATUS)
        return result

    async def history(self, client: BleakClient) -> RadonEyeHistory:
        raise NotImplementedError

    async def beep(self, client: BleakClient) -> None:
        await client.write_gatt_char(CHARACTERISTIC_V1_COMMAND, bytearray(COMMAND_V1_BEEP))
        # there is some delay needed before you can do next beep, otherwise it will be just one beep
        await asyncio.sleep(BEEP_DELAY)
