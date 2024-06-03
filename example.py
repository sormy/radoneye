import asyncio
import json
from sys import stderr

from radoneye import RadonEyeClient, RadonEyeScanner


async def main():
    for dev in await RadonEyeScanner.discover():
        print(f"Device: {dev}")

        async with RadonEyeClient(dev) as client:
            try:
                await client.beep()
                print("Beep: ok")
            except Exception:
                print("Unable to beep due to error", file=stderr)

            try:
                print(f"Status: {json.dumps(await client.status())}")
            except Exception:
                print("Unable to obtain status due to error", file=stderr)

            try:
                print(f"History: {json.dumps(await client.history())}")
            except Exception:
                print("Unable to obtain history due to error", file=stderr)

            try:
                print("Setting up alarm")
                await client.set_alarm(enabled=True, level=2.0, unit="pci/l", interval=60)
            except Exception:
                print("Unable to set alarm due to error", file=stderr)

            try:
                print("Setting up unit")
                await client.set_unit("pci/l")
            except Exception:
                print("Unable to set unit due to error", file=stderr)


if __name__ == "__main__":
    asyncio.run(main())
