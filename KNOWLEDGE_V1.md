## Knowledge V1

Information below is obtained using reverse engineering. It might be not 100% correct.

## General

-   Service UUID: 00001523-1212-efde-1523-785feabcd123
-   Command Write Characteristic: 00001524-1212-efde-1523-785feabcd123
-   Status Read Characteristic: 00001525-1212-efde-1523-785feabcd123
-   History Read Characteristic: 00001526-1212-efde-1523-785feabcd123

All write operations are performed on command characteristic without response.

All read operations are performed using notifications on status read characteristic with exception
to history, history is read using notifications on history read characteristic.

## Full status request (OUTGOING)

Example:

```
0x00: 10 11 00 00 00 00 00 00  00 00 00 00 00 00 00 00
0x10: 00 00 00 00
```

Sending just `10` is enough to request responses 0xA4, 0xA8, 0xAC, 0x50, 0x51.

## Radon levels/particle counts request (0x50) (OUTGOING)

Example:

```
0x00: 50 11 00 00 00 00 00 00  00 00 00 00 00 00 00 00
0x10: 00 00 00 00
```

Sending just `50` is enough to trigger response.

## Radon levels/particle counts response (0x50) (INCOMING)

Triggered by commands 0x10, 0x50.

Example:

```
0x00: 50 10 E1 7A 14 3F F6 28  BC 3F 00 00 00 00 01 00
0x10: 04 00 00 00
```

Format:

-   0x00: code 0x50
-   0x01: buffer length: 0x10
-   0x02: current radon level in pci/l: float32
-   0x06: day average radon level in pci/l: float32
-   0x0A: month average radon level in pci/l: float32
-   0x0E: current particle count, uint16
-   0x10: previous particle count, uint16
-   0x12: unused, 2 bytes

## Device uptime/peak radon request (0x51) (OUTGOING)

Example:

```
0x00: 51 11 00 00 00 00 00 00  00 00 00 00 00 00 00 00
0x10: 00 00 00 00
```

Sending just `51` is enough to trigger response.

## Device uptime/peak radon response (0x51) (INCOMING)

Triggered by commands 0x10, 0x51.

Example:

```
0x00: 51 0E 02 00 C1 2D 00 00  3E 40 08 00 50 B1 0C 40
0x10: 04 00 00 00
```

Format:

-   0x00: code 0x51
-   0x01: buffer length: 0x0E
-   0x02: unknown: 2 bytes
-   0x04: uptime in minutes, uint16
-   0x08: unknown: 4 bytes
-   0x0C: peak radon level in pci/l: float32
-   0x10: unused, 4 bytes

## Device serial response (0xA4) (INCOMING)

Triggered by command 0x10.

This status message contains device unique string that is used to build device serial name.

Example:

```
0x00: A4 0E 32 30 32 30 31 32  30 32 53 4E 30 31 35 39
0x10: 08 00 00 00
```

Format:

-   0x00: code 0xA4
-   0x01: buffer length: 0x0E
-   0x02: manufacturing date: 6 bytes, ascii, YYMMDD
-   0x08: unknown, 2 bytes, ascii
-   0x0A: reserved, ascii, "SN"
-   0x0C: serial within day, 4 bytes, ascii
-   0x10: unused, 4 bytes

## Device series request (0xA6) (OUTGOING)

Example:

```
0x00: A6 11 00 00 00 00 00 00  00 00 00 00 00 00 00 00
0x10: 00 00 00 00
```

Sending just `A6` is enough to trigger response.

## Device series response (0xA6) (INCOMING)

Triggered by command 0xA6.

Example:

```
0x00: A6 03 52 55 32 32 2E 34  0A 66 66 86 3F B1 0C 40
0x10: 04 00 00 00
```

Format:

-   0x00: code 0xA6
-   0x01: buffer length: 0x03
-   0x02: device series, 3 bytes, ascii
-   0x05: unused, 15 bytes

Device series looks like `RU2`

## Device model response (0xA8) (INCOMING)

Triggered by command 0x10.

Example:

```
0x00: A8 06 05 52 44 32 30 30  30 32 53 4E 30 31 35 39
0x10: 08 00 00 00
```

Format:

-   0x00: code 0xA8
-   0x01: buffer length: 0x06
-   0x02: reserved 0x05? looks like the length of next string
-   0x03: device name, 5 bytes, ascii
-   0x09: unused, 12 bytes

## Device software version request (0xAF) (OUTGOING)

Example:

```
0x00: AF 11 00 00 00 00 00 00  00 00 00 00 00 00 00 00
0x10: 00 00 00 00
```

Sending just `AF` is enough to trigger response.

## Device software version response (0xAF) (INCOMING)

Triggered by command 0xAF.

Example:

```
0x00: AF 07 56 31 2E 32 2E 34  0A 66 66 86 3F B1 0C 40
0x10: 04 00 00 00
```

Format:

-   0x00: code 0xAF
-   0x01: buffer length: 0x07
-   0x02: software version, 7 bytes, ascii, ends with new line (\n)
-   0x0A: unused, 11 bytes

Software version looks like `V1.2.4\n`

## History metadata request (0xE8) (OUTGOING)

Example:

```
0x00: E8 11 00 00 00 00 00 00  00 00 00 00 00 00 00 00
0x10: 00 00 00 00
```

Sending just `E8` is enough to trigger response.

## History metadata response (0xE8) (INCOMING)

Triggered by command 0xE8.

Example:

```
0x00: E8 0B 45 00 37 29 5C 4F  3F 66 66 86 3F B1 0C 40
0x10: 04 00 00 00
```

Format:

-   0x00: code 0xE8
-   0x01: buffer length: 0x0B
-   0x02: number of data points in history, uint16
-   0x04: unknown, 9 bytes
-   0x0D: unused, 7 bytes

## History request (0xE9) (OUTGOING)

Example:

```
0x00: E9 11 00 00 00 00 00 00  00 00 00 00 00 00 00 00
0x10: 00 00 00 00
```

Sending just `E9` is enough to request history data, however, you need to read `E8` message to get
know number of entries in history to be able to properly retrieve and decode `E9` response.

## History response (0xE9) (INCOMING)

Triggered by command 0xE9.

There are multiple responses returned to cover full history. All responses are delivered to
dedicated characteristic. You need to know number of data points to get know when to stop waiting
for history data and to truncate last message this it has some unused data.

Example:

```
0x00: 85 00 46 00 5E 00 7C 00  85 00 5E 00 82 00 79 00
0x10: 58 00 82 00

0x00: 8E 00 73 00 4F 00 61 00  93 00 8B 00 93 00 AE 00
0x10: 9F 00 93 00

0x00: 82 00 8B 00 85 00 8E 00  67 00 79 00 79 00 85 00
0x10: A5 00 73 00

0x00: A5 00 82 00 67 00 73 00  8B 00 70 00 46 00 6A 00
0x10: 58 00 6A 00

0x00: C3 00 6A 00 73 00 85 00  67 00 8E 00 93 00 79 00
0x10: B1 00 B7 00

0x00: B7 00 BA 00 9C 00 9C 00  CC 00 82 00 61 00 58 00
0x10: 96 00 8B 00

0x00: 8B 00 C0 00 A5 00 A8 00  73 00 70 00 61 00 4C 00
0x10: 46 00 43 00
```

This message contains history data points, uint16 for each data point. Each data point can be
converted to value in pci/l as: `rawValue / 37 / 2.7`. Number `37` here is needed to convert bq/m3
to pci/l but `2.7` (experimentally found) is magic. Every message is fixed to be 20 bytes, so last
message might contain some unused data in the end. You need to know number of entries in history to
determine unused part of the last message.

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

Example: `AA 11 00 00 00 40 40 24`

Format:

-   0x00: code 0xAA
-   0x01: reserved 0x11?
-   0x02: alarm status: uint8 (0x00 - disabled, 0x01 - enabled)
-   0x03: alarm level in pci/l: float32
-   0x07: alarm interval in 10min increments: uint8 (1 - 10 mins, 6 - 1 hour, 36 - 6 hours)

## Set unit request (0x??) (OUTGOING)

???

## Settings response (0xAC) (INCOMING)

Triggered by commands 0x10, 0xA1, 0xAA.

Example:

```
0x00: AC 07 00 01 00 00 40 40  06 32 53 4E 30 31 35 39
0x10: 08 00 00 00
```

Format:

-   0x00: code 0xAC
-   0x01: buffer length: 0x07
-   0x02: display unit: uint8 (0x00 - pci/l, 0x01 - bq/m3)
-   0x03: alarm status: uint8 (0x00 - disabled, 0x01 - enabled)
-   0x04: alarm level in pci/l: float32
-   0x08: alarm interval in 10min increments: uint8 (1 - 10 mins, 6 - 1 hour, 36 - 6 hours)
-   0x09: unused, 11 bytes
