# Ecosense RadonEye CLI and API for Python

Provides simple and convinient Python API to communicate with RadonEye bluetooth devices.

Built as an alternative to half done similar projects where either 1 or 2 version is supported, not
all status properties are decoded, no history support, no beep support etc.

Supported devices:

| Name   | Version | Supported | Tested by        |
| ------ | ------- | --------- | ---------------- |
| RD200  | 1       | YES?      | Pending testing  |
| RD200N | 2       | YES       | Tested by author |
| RD200P | 2       | YES?      | Pending testing  |

Supported capabilites:

| Name                       | Version 1 | Version 2 |
| -------------------------- | --------- | --------- |
| Read serial number         | YES       | YES       |
| Read software version      | YES       | YES       |
| Read latest level          | YES       | YES       |
| Read daily average level   | YES       | YES       |
| Read monthly average level | YES       | YES       |
| Read peak historical level | YES       | YES       |
| Read raw particle counts   | YES       | YES       |
| Read uptime                | YES       | YES       |
| Read history               | YES       | YES       |
| Trigger Beep               | YES       | YES       |

## Usage (API)

Scan for all available devices, beep, read status and history:

```py
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


if __name__ == "__main__":
    asyncio.run(main())
```

## Usage (CLI)

```sh
$ pip3 install radoneye

$ radoneye --help

$ radoneye list --help
$ radoneye list
70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9	FR:RU22201030383
3775964E-C653-C00C-7F02-7C03F9F0122D	FR:RU22204180050

$ radoneye beep --help
$ radoneye beep 70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9
Beeping on 70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9

$ radoneye status --help
$ radoneye status 70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9
counts_current = 0
counts_previous = 1
counts_str = 0/1
day_avg_bq_m3 = 16
day_avg_pci_l = 0.43
latest_bq_m3 = 5
latest_pci_l = 0.14
model = RD200N
month_avg_bq_m3 = 0
month_avg_pci_l = 0.0
peak_bq_m3 = 32
peak_pci_l = 0.86
serial = RU22201030383
uptime_minutes = 3495
uptime_str = 2d10h1

$ radoneye history 70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9
#	Bq/m3	pCi/L
1	2	0.05
2	9	0.24
3	20	0.54
4	10	0.27
5	10	0.27
6	5	0.14
7	5	0.14
8	3	0.08
9	10	0.27
10	10	0.27
...
```

NOTE: On macOS bluetooth addresses are obfuscated to UUIDs.

## License

MIT
