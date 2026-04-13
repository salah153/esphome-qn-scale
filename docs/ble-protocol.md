# QN Scale BLE Protocol Notes

Scale: KAMTRON CS20M (QN chipset)
MAC: A4:C1:38:D9:18:8A
Service: 0xFFE0

## Characteristics

| UUID  | Direction     | Purpose                  |
|-------|---------------|--------------------------|
| FFE1  | Scale → Host  | Weight frames, scale info (notify) |
| FFE2  | Scale → Host  | Acknowledgments (indicate) |
| FFE3  | Host → Scale  | Unit config, commands (write) |
| FFE4  | Host → Scale  | Time sync (write) |

## Opcodes (Scale → Host, on FFE1)

| Opcode | Name       | Description |
|--------|------------|-------------|
| 0x10   | Weight     | Live weight + impedance readings |
| 0x12   | Scale info | Sent on connect; contains MAC, protocol type, scale factor |
| 0x14   | Time req   | Scale requests time sync; host responds with 0x20 |
| 0x21   | Stored data| Scale requests historical data acknowledgment |

## 0x12 Scale Info Frame (15 bytes)

Captured from KAMTRON CS20M on 2026-04-13:

```
12 0F 15 8A 18 D9 38 C1 A4 38 01 38 00 10 CF
12 0F 15 8A 18 D9 38 C1 A4 38 01 38 01 10 D0
```

| Byte | Value | Meaning |
|------|-------|---------|
| [0]  | 0x12  | Opcode |
| [1]  | 0x0F  | Length (15) |
| [2]  | 0x15  | Protocol type |
| [3–8]| 8A 18 D9 38 C1 A4 | MAC address (reversed) |
| [9]  | 0x38  | Unknown (constant) |
| [10] | 0x01  | Scale factor: 1 = divide by 100, else divide by 10 |
| [11] | 0x38  | Unknown (constant) |
| [12] | 0x00/0x01 | Varies across connections — possibly session count or stored-data flag |
| [13] | 0x10  | Unknown (constant) |
| [14] | checksum | Sum of bytes [0–13] & 0xFF |

## 0x10 Weight Frame

```
[0]    [1]   [2]      [3-4]        [5]     [6-7]  [8-9]  [10]
0x10   len   proto    weight(u16)  stable  R1     R2     checksum
                      (BE, /100)   0/1     (Ω)    (Ω)
```

Stable = 1 means reading is settled. Weight is big-endian uint16 divided by scale_factor.

## Battery Level

**Not transmitted.** Exhaustive BLE frame capture on 2026-04-13 confirmed all frames from
the scale are handled by known opcodes (0x10, 0x12, 0x14, 0x21). No unknown opcodes appeared.
The CS20M does not expose battery level over BLE.

## Connection Lifecycle

```
Scale powers on → advertises
ESP32 detects MAC in advertisement → connect()
Scale sends 0x12 (scale info) → host sends unit config + time sync (FFE3, FFE4)
Scale streams 0x10 weight frames (~5/sec) until stable
On stable reading → host disconnects → scale sleeps
```

**Important**: Host must call `disconnect()` after a stable reading. If the connection
is held open, the scale stays powered on and drains batteries overnight.
Disconnect reason 0x16 = local (host-initiated). Scale then sends reason 0x13 (remote)
and powers off.
