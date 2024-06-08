import asyncio
import sys

from radoneye.cli import main as cli_main


def main():
    asyncio.run(cli_main(sys.argv))


if __name__ == "__main__":
    main()
