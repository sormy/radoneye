from bleak import BleakClient

from radoneye.interface import RadonEyeInterfaceBase
from radoneye.interface_v1 import RadonEyeAdapterV1
from radoneye.interface_v2 import RadonEyeAdapterV2


class RadonEyeInterfaceFactory:
    @classmethod
    def create(
        cls, client: BleakClient, status_read_timeout: float, history_read_timeout: float
    ) -> RadonEyeInterfaceBase:
        if RadonEyeAdapterV1.supports(client):
            return RadonEyeAdapterV1(
                status_read_timeout=status_read_timeout,
            )
        if RadonEyeAdapterV2.supports(client):
            return RadonEyeAdapterV2(
                status_read_timeout=status_read_timeout,
                history_read_timeout=history_read_timeout,
            )
        else:
            raise NotImplementedError("Unsupported device version")
