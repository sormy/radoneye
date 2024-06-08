from __future__ import annotations

import asyncio
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from typing import Literal, NamedTuple, TypedDict

from radoneye.client import RadonEyeClient
from radoneye.model import OutputType, RadonUnit
from radoneye.scanner import RadonEyeScanner
from radoneye.util import convert_radon_value, serialize_object


class RadonEyeAlarmStatus(TypedDict):
    alarm_enabled: int
    alarm_level_bq_m3: float
    alarm_level_pci_l: float
    alarm_interval_minutes: int


class ListCommandArgs(NamedTuple):
    adapter: str | None
    timeout: int
    output: OutputType


async def cmd_list(args: ListCommandArgs):
    devs = [
        {"address": dev.address, "name": dev.name}
        for dev in await RadonEyeScanner.discover(adapter=args.adapter, timeout=args.timeout)
    ]
    if args.output == "text":
        for dev in devs:
            print(f"{dev['address']}\t{dev['name']}")
    else:
        print(serialize_object(devs, "json"))


class BeepCommandArgs(NamedTuple):
    adapter: str | None
    debug: bool
    connect_timeout: int
    address: str


async def cmd_beep(args: BeepCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
        debug=args.debug,
    ) as client:
        print("beep")
        await client.beep()


class StatusCommandArgs(NamedTuple):
    adapter: str | None
    debug: bool
    connect_timeout: int
    read_timeout: int
    output: OutputType
    address: str


async def cmd_status(args: StatusCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
        status_read_timeout=args.read_timeout,
        debug=args.debug,
    ) as client:
        status = await client.status()
        print(serialize_object(status, args.output))


class HistoryCommandArgs(NamedTuple):
    adapter: str | None
    debug: bool
    connect_timeout: int
    read_timeout: int
    output: OutputType
    address: str


async def cmd_history(args: HistoryCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
        history_read_timeout=args.read_timeout,
        debug=args.debug,
    ) as client:
        history = await client.history()
        if args.output == "text":
            print("#\tBq/m3\tpCi/L")
            for index, value_bq_m3 in enumerate(history["values_bq_m3"]):
                value_pci_l = history["values_pci_l"][index]
                print(f"{index + 1}\t{value_bq_m3}\t{value_pci_l}")
        else:
            print(serialize_object(history, "json"))


class AlarmCommandArgs(NamedTuple):
    adapter: str | None
    debug: bool
    connect_timeout: int
    read_timeout: int
    output: OutputType
    address: str
    status: Literal["on", "off"] | None
    level: float | None  # in bq/m3 or pci/l
    unit: RadonUnit | None
    interval: int | None  # mins


async def cmd_alarm(args: AlarmCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
        status_read_timeout=args.read_timeout,
        debug=args.debug,
    ) as client:
        if args.status is None and args.level is None and args.interval is None:
            status = await client.status()

            alarm_status = {
                "alarm_enabled": status["alarm_enabled"],
                "alarm_level_bq_m3": status["alarm_level_bq_m3"],
                "alarm_level_pci_l": status["alarm_level_pci_l"],
                "alarm_interval_minutes": status["alarm_interval_minutes"],
            }

            print(serialize_object(alarm_status, args.output))
        elif (
            args.status is not None
            and args.level is not None
            and args.unit is not None
            and args.interval is not None
        ):
            new_alarm_status: RadonEyeAlarmStatus = {
                "alarm_enabled": args.status == "on",
                "alarm_level_bq_m3": convert_radon_value(args.level, args.unit, "bq/m3"),
                "alarm_level_pci_l": convert_radon_value(args.level, args.unit, "pci/l"),
                "alarm_interval_minutes": args.interval,
            }

            await client.set_alarm(
                enabled=args.status == "on",
                level=args.level,
                unit=args.unit,
                interval=args.interval,
            )

            print(serialize_object(new_alarm_status, args.output))
        else:
            status = await client.status()

            new_enabled = (
                args.status == "on" if args.status is not None else bool(status["alarm_enabled"])
            )

            if args.level is not None:
                new_unit = args.unit or status["display_unit"]
                new_level = args.level
            elif status["display_unit"] == "pci/l":
                new_level = status["alarm_level_pci_l"]
                new_unit = "pci/l"
            else:
                new_level = status["alarm_level_bq_m3"]
                new_unit = "bq/m3"

            new_interval = args.interval or status["alarm_interval_minutes"]

            await client.set_alarm(
                enabled=new_enabled,
                level=new_level,
                unit=new_unit,
                interval=new_interval,
            )

            new_alarm_status: RadonEyeAlarmStatus = {
                "alarm_enabled": new_enabled,
                "alarm_level_bq_m3": convert_radon_value(new_level, new_unit, "bq/m3"),
                "alarm_level_pci_l": convert_radon_value(new_level, new_unit, "pci/l"),
                "alarm_interval_minutes": new_interval,
            }

            print(serialize_object(new_alarm_status, args.output))


class UnitCommandArgs(NamedTuple):
    adapter: str | None
    debug: bool
    connect_timeout: int
    read_timeout: int
    output: OutputType
    address: str
    unit: RadonUnit | None


async def cmd_unit(args: UnitCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
        status_read_timeout=args.read_timeout,
        debug=args.debug,
    ) as client:
        if args.unit is None:
            status = await client.status()
            print(serialize_object(status["display_unit"], args.output))
        else:
            await client.set_unit(args.unit)
            print(serialize_object(args.unit, args.output))


async def main(argv: list[str]):
    parser = ArgumentParser(
        description="Ecosense RadonEye command line interface (currently supports RD200 v1/v2)",
        formatter_class=ArgumentDefaultsHelpFormatter,
        prog="radoneye",
    )

    parser.add_argument("--adapter", type=int, help="bluetooth adapter name (hci0 on Linux)")
    parser.add_argument(
        "-d", "--debug", action="store_true", default=False, help="enable to see message dumps"
    )

    subparsers = parser.add_subparsers(required=True, help="sub-command help")

    parser_list = subparsers.add_parser(
        "list",
        help="scan for devices available nearby",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser_list.add_argument("--timeout", type=int, help="scan timeout", default=5)
    parser_list.add_argument(
        "--output", choices=["json", "text"], help="output format", default="text"
    )
    parser_list.set_defaults(func=cmd_list)

    parser_beep = subparsers.add_parser(
        "beep",
        help="trigger beep",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser_beep.add_argument("--connect-timeout", type=int, help="connect timeout", default=10)
    parser_beep.add_argument("address", help="device address")
    parser_beep.set_defaults(func=cmd_beep)

    parser_status = subparsers.add_parser(
        "status",
        help="read status",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser_status.add_argument("--connect-timeout", type=int, help="connect timeout", default=10)
    parser_status.add_argument("--read-timeout", type=int, help="read timeout", default=5)
    parser_status.add_argument(
        "--output", choices=["json", "text"], help="output format", default="text"
    )
    parser_status.add_argument("address", help="device address")
    parser_status.set_defaults(func=cmd_status)

    parser_history = subparsers.add_parser(
        "history",
        help="read history",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser_history.add_argument("--connect-timeout", type=int, help="connect timeout", default=10)
    parser_history.add_argument("--read-timeout", type=int, help="read timeout", default=60)
    parser_history.add_argument(
        "--output", choices=["json", "text"], help="output format", default="text"
    )
    parser_history.add_argument("address", help="device address")
    parser_history.set_defaults(func=cmd_history)

    parser_alarm = subparsers.add_parser(
        "alarm",
        help="get/set alarm configuration",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser_alarm.add_argument("address", help="device address")
    parser_alarm.add_argument("--connect-timeout", type=int, help="connect timeout", default=10)
    parser_alarm.add_argument("--read-timeout", type=int, help="read timeout", default=5)
    parser_alarm.add_argument("--status", choices=["on", "off"], help="alarm status")
    parser_alarm.add_argument("--level", type=float, help="alarm level in bq/m3 or pci/l")
    parser_alarm.add_argument("--unit", choices=["bq/m3", "pci/l"], help="alarm level unit")
    parser_alarm.add_argument("--interval", type=int, help="alarm interval (in minutes)")
    parser_alarm.add_argument(
        "--output", choices=["json", "text"], help="output format", default="text"
    )
    parser_alarm.set_defaults(func=cmd_alarm)

    parser_unit = subparsers.add_parser(
        "unit",
        help="get/set display unit (bq/m3 or pci/l)",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser_unit.add_argument("address", help="device address")
    parser_unit.add_argument("--connect-timeout", type=int, help="connect timeout", default=10)
    parser_unit.add_argument("--read-timeout", type=int, help="read timeout", default=5)
    parser_unit.add_argument("--unit", choices=["bq/m3", "pci/l"], help="set new display unit")
    parser_unit.add_argument(
        "--output", choices=["json", "text"], help="output format", default="text"
    )
    parser_unit.set_defaults(func=cmd_unit)

    args = parser.parse_args(argv[1:])

    await args.func(args)


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
