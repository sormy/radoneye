import asyncio
import json
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from typing import Literal, NamedTuple

from radoneye.client import RadonEyeClient
from radoneye.scanner import RadonEyeScanner


class ListCommandArgs(NamedTuple):
    adapter: str | None
    timeout: int
    output: Literal["text", "json"]


async def cmd_list(args: ListCommandArgs):
    for dev in await RadonEyeScanner.discover(adapter=args.adapter, timeout=args.timeout):
        if args.output == "text":
            print(f"{dev.address}\t{dev.name}")
        else:
            print(json.dumps({"address": dev.address, "name": dev.name}, separators=(",", ":")))


class BeepCommandArgs(NamedTuple):
    adapter: str | None
    connect_timeout: int
    address: str


async def cmd_beep(args: BeepCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
    ) as client:
        print(f"Beeping on {args.address}")
        await client.beep()


class StatusCommandArgs(NamedTuple):
    adapter: str | None
    connect_timeout: int
    read_timeout: int
    output: Literal["text", "json"]
    address: str


async def cmd_status(args: StatusCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
        status_read_timeout=args.read_timeout,
    ) as client:
        status = await client.status()
        if args.output == "text":
            for key in sorted(status.keys()):
                print(f"{key} = {status.get(key)}")
        else:
            print(json.dumps(status, separators=(",", ":")))


class HistoryCommandArgs(NamedTuple):
    adapter: str | None
    connect_timeout: int
    read_timeout: int
    output: Literal["text", "json"]
    address: str


async def cmd_history(args: HistoryCommandArgs):
    async with RadonEyeClient(
        args.address,
        adapter=args.adapter,
        connect_timeout=args.connect_timeout,
        history_read_timeout=args.read_timeout,
    ) as client:
        history = await client.history()
        if args.output == "text":
            print("#\tBq/m3\tpCi/L")
            for index, value_bq_m3 in enumerate(history["values_bq_m3"]):
                value_pci_l = history["values_pci_l"][index]
                print(f"{index + 1}\t{value_bq_m3}\t{value_pci_l}")
        else:
            print(json.dumps(history, separators=(",", ":")))


async def main():
    parser = ArgumentParser(
        description="Ecosense RadonEye command line interface (currently supports RD200 v1/v2)",
        formatter_class=ArgumentDefaultsHelpFormatter,
        prog="radoneye",
    )

    parser.add_argument("--adapter", type=int, help="bluetooth adapter name (hci0 on Linux)")

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

    args = parser.parse_args()
    await args.func(args)


if __name__ == "__main__":
    asyncio.run(main())
