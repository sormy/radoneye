import string


def is_printable(ch: str):
    return (
        ch in string.digits or ch in string.ascii_letters or ch in string.punctuation or ch == " "
    )


def print_byte(b: int) -> str:
    ch = chr(b)
    return ch if is_printable(ch) else "."


def split_data(data: bytearray, size: int):
    for i in range(0, len(data), size):
        yield data[i : i + size]


def dump_data_str(data: bytearray) -> str:
    return "".join([print_byte(b) for b in data])


def dump_data(data: bytearray, input: bool, debug: bool) -> bytearray:
    if debug:
        dir = "<-" if input else "->"
        text = "\n   ".join(
            [
                f"{chunk.hex(' ').ljust(48)}# {dump_data_str(chunk)}"
                for chunk in split_data(data, 16)
            ]
        )
        print(f"{dir} {text}")
    return data


def dump_in(data: bytearray, debug: bool) -> bytearray:
    return dump_data(data, True, debug)


def dump_out(data: bytearray, debug: bool) -> bytearray:
    return dump_data(data, False, debug)
