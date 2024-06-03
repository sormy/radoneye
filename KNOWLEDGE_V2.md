# Knowledge V2

Information below is obtained using reverse engineering. It might be not 100% correct.

## General

-   Service UUID: 00001523-0000-1000-8000-00805f9b34fb
-   Command Write Characteristic: 00001524-0000-1000-8000-00805f9b34fb
-   Status Read Characteristic: 00001525-0000-1000-8000-00805f9b34fb
-   History Read Characteristic: 00001526-0000-1000-8000-00805f9b34fb

All write operations are performed on command characteristic without response.

All read operations are performed using notifications on status read characteristic with exception
to history, history is read using notifications on history read characteristic.

## Full status request (0x40) (OUTGOING)

Example: `40`

Format:

-   0x00: code 0x40

## Full status response (0x40) (INCOMING)

Example:

```
0x00: 40 42 32 32 30 31 30 33 52 55 32 30 33 38 33 06
0x10: 52 44 32 30 30 4e 56 32 2e 30 2e 32 00 01 4a 00
0x20: 06 0a 00 08 00 00 00 03 00 01 00 79 30 00 00 e0
0x30: 11 08 00 1c 00 02 00 00 00 38 22 00 5c 8f 42 3f
0x40: a4 70 9d 3f
```

Format:

-   0x00: code 0x40
-   0x01: buffer length: 0x42
-   0x02: serial: manufacturing date: 6 bytes, ascii, YYMMDD
-   0x08: serial: series: 3 bytes, ascii
-   0x0B: serial: serial within day: 4 bytes, ascii
-   0x0F: reserved 0x06?
-   0x10: model: 6 bytes, ascii
-   0x16: software version: 6 bytes, ascii
-   0x1C: display unit: uint8 (0x00 - pci/l, 0x01 - bq/m3)
-   0x1D: alarm status: uint8 (0x00 - disabled, 0x01 - enabled)
-   0x1E: alarm level in bq/m3: uint16
-   0x20: alarm interval in 10min increments: uint8 (1 - 10 mins, 6 - 1 hour, 36 - 6 hours)
-   0x21: current radon level in bq/m3, uint16
-   0x23: day average radon level in bq/m3, uint16
-   0x25: month average radon level in bq/m3, uint16
-   0x27: current particle count, uint16
-   0x29: previous particle count, uint16
-   0x2B: uptime in minutes, uint16
-   0x2D: unknown, 6 bytes
-   0x33: peak radon level in bq/m3, uint16
-   0x35: unknown, 4 bytes
-   0x39: number of data points in history, uint16
-   0x3B: unknown, 9 bytes

15-4-2

## History request (0x41) (OUTGOING)

Example: `41`

Format:

-   0x00: code 0x41

## History response (0x41) (INCOMING)

There are multiple messages received for history if history can't fit in one message.

Example: `41 24 01 fa 00 ...`

Format:

-   0x00: code 0x41
-   0x01: total message count, uint8
-   0x02: this message number: uint8
-   0x03: value count in this message: uint8
-   0x04: values in bq/m3, array of uint16

## Beep request (0xA1) (OUTGOING)

Example: `A1 11 18 06 02 01 19 2C`

-   0x00: code 0xA1
-   0x01: reserved 0x11?
-   0x02: timestamp of request, two digit year, uint8
-   0x03: timestamp of request, month (1-12), uint8
-   0x04: timestamp of request, day of the month (1-31), uint8
-   0x05: reserved 0x01?
-   0x06: timestamp of request, number of minutes (0-59), uint8
-   0x07: timestamp of request, number of seconds (0-59), uint8

Sending just `A1` is enough to trigger beep.

## Set alarm request (0xAA) (OUTGOING)

Example: `AA 11 01 4A 00 06`

Format:

-   0x00: code 0xAA
-   0x01: reserved 0x11?
-   0x02: alarm status: uint8 (0x00 - disabled, 0x01 - enabled)
-   0x03: alarm level in bq/m3: uint16
-   0x05: alarm interval in 10min increments: uint8 (1 - 10 mins, 6 - 1 hour, 36 - 6 hours)

## Set unit request (0xA2) (OUTGOING)

Example: `A2 11 01`

Format:

-   0x00: code 0xA2
-   0x01: reserved 0x11?
-   0x02: display unit: uint8 (0x00 - pci/l, 0x01 - bq/m3)

## Settings response (0xAC) (INCOMING)

Triggered by 0xAA or 0xA2 requests.

Example: `AC 05 00 01 4A 00 06`

Format:

-   0x00: code 0xAC
-   0x01: buffer length: 0x05
-   0x02: display unit: uint8 (0x00 - pci/l, 0x01 - bq/m3)
-   0x03: alarm status: uint8 (0x00 - disabled, 0x01 - enabled)
-   0x04: alarm level in bq/m3: uint16
-   0x06: alarm interval in 10min increments: uint8 (1 - 10 mins, 6 - 1 hour, 36 - 6 hours)
