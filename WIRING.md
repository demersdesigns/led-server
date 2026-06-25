# SK9822 LED Strip Wiring Guide

---

## What You'll Need

| Item | Notes |
|---|---|
| Raspberry Pi 3B+ | Already set up |
| GPIO breakout board + ribbon cable | 40-pin |
| Breadboard | For making connections |
| SK9822 LED strip | 60 LEDs, has 4 wires |
| External 5V power supply | **Minimum 3A** — the strip can draw up to 3.6A at full brightness |
| Jumper wires | Male-to-male |

---

## Before You Wire Anything

**Why an external PSU?**
At full white, 60 LEDs draw up to 3.6A. The Pi's 5V pins are fused at ~1A and would be destroyed. Always power the strip from a dedicated 5V supply.

**Why a common ground?**
The Pi and the external PSU must share a ground reference or the SPI data signal has nothing to reference — the strip won't respond.

---

## Step 1 — Identify Your Strip's Wires

SK9822 strips have 4 wires. Colors vary by manufacturer — check the labels printed on the strip itself near the connector. Common color schemes:

```
Most common:          Some manufacturers:
┌─────────────┐       ┌─────────────┐
│ RED   = 5V  │       │ RED   = 5V  │
│ BLACK = GND │       │ WHITE = GND │
│ GREEN = DAT │       │ BLUE  = DAT │
│ BLUE  = CLK │       │ YELLOW= CLK │
└─────────────┘       └─────────────┘
```

> **Always verify against the markings on your strip — do not rely on color alone.**

The input end of the strip has arrows or markings indicating signal direction. Wire to the **input end** (arrows point away from the connector).

---

## Step 2 — Pi GPIO Pin Reference

Connect your ribbon cable and breakout board. The 3 pins you need are highlighted:

```
Pi 3B+ GPIO Header — viewed from above
(ribbon cable notch faces the SD card side)

        LEFT COLUMN          RIGHT COLUMN
        (odd pins)           (even pins)

 3V3    [ 1] ─── [ 2]  5V
 GPIO2  [ 3] ─── [ 4]  5V
 GPIO3  [ 5] ─── [ 6]  GND  ◄━━━━━━━━━━━━┓
 GPIO4  [ 7] ─── [ 8]  TXD               ┃ ① GND
 GND    [ 9] ─── [10]  RXD               ┃ (use any GND;
 GPIO17 [11] ─── [12]  GPIO18            ┃  Pin 6 shown)
 GPIO27 [13] ─── [14]  GND               ┃
 GPIO22 [15] ─── [16]  GPIO23            ┃
 3V3    [17] ─── [18]  GPIO24            ┃
 MOSI   [19] ─── [20]  GND   ◄━━━━━━━━━━━┫
 MISO   [21] ─── [22]  GPIO25            ┃ ② DATA
 SCLK   [23] ─── [24]  CE0   ◄━━━━━━━━━━━┫
 GND    [25] ─── [26]  CE1               ┃ ③ CLOCK
 GPIO0  [27] ─── [28]  GPIO1             ┃
 GPIO5  [29] ─── [30]  GND               ┃
 GPIO6  [31] ─── [32]  GPIO12            ┃
 GPIO13 [33] ─── [34]  GND               ┃
 GPIO19 [35] ─── [36]  GPIO16            ┃
 GPIO26 [37] ─── [38]  GPIO20            ┃
 GND    [39] ─── [40]  GPIO21            ┃
                                         ┃
 ① Pin 6   = GND  ━━━━━━━━━━━━━━━━━━━━━━┛
 ② Pin 19  = SPI0 MOSI  →  strip DATA
 ③ Pin 23  = SPI0 SCLK  →  strip CLOCK
```

---

## Step 3 — Full Wiring Diagram

```
  ┌─────────────────┐          ┌──────────────────────┐
  │  External 5V    │          │    Raspberry Pi 3B+  │
  │  Power Supply   │          │                      │
  │                 │          │  Pin 6   (GND)  ─────┼──┐
  │  (+) 5V ────────┼──────────┼──────────────────┐   │  │
  │                 │          │  Pin 19  (MOSI) ──┼───┼──┼──► DATA
  │  (-) GND ───────┼──┐       │  Pin 23  (SCLK) ──┼───┼──┼──► CLOCK
  │                 │  │       │                      │  │  │
  └─────────────────┘  │       └──────────────────────┘  │  │
                       │                                  │  │
                       └──────────────────────────────────┘  │
                       │  (common ground)                     │
                       │                                      │
  ┌────────────────────┼──────────────────────────────────────┼───┐
  │   SK9822 Strip     │                                      │   │
  │                    │                                      │   │
  │   GND  ────────────┘                                      │   │
  │   5V   ─────────────────────── (+) from PSU               │   │
  │   DATA ───────────────────────────────────────────────────┘   │
  │   CLOCK ──────────────────── (see DATA line above)            │
  └───────────────────────────────────────────────────────────────┘
```

---

## Step 4 — Breadboard Layout

Using your GPIO breakout board:

```
  Breakout Board                    Breadboard
  ┌──────────────┐                 ┌──────────────────────┐
  │              │                 │  + rail  - rail      │
  │  GND (Pin6) ─┼─────────────────┼► col A   (black wire)┼──► Strip GND
  │              │                 │                      │
  │  MOSI (P19) ─┼─────────────────┼► col B   (any color) ┼──► Strip DATA
  │              │                 │                      │
  │  SCLK (P23) ─┼─────────────────┼► col C   (any color) ┼──► Strip CLOCK
  │              │                 │                      │
  └──────────────┘                 │  + rail ◄────────────┼──── PSU 5V (+)
                                   │  - rail ◄────────────┼──── PSU GND (-)
                                   │          ────────────┼──► Strip 5V
                                   └──────────────────────┘
```

---

## Step 5 — Connection Checklist

Make each connection in this order — **with everything powered off**:

- [ ] PSU `(-)` GND → breadboard negative rail
- [ ] PSU `(+)` 5V → breadboard positive rail
- [ ] Pi Pin 6 `GND` → breadboard negative rail (common ground)
- [ ] Strip `GND` wire → breadboard negative rail
- [ ] Strip `5V` wire → breadboard positive rail
- [ ] Pi Pin 19 `MOSI` → strip `DATA` wire
- [ ] Pi Pin 23 `SCLK` → strip `CLOCK` wire

---

## Step 6 — Power On Order

1. Power on the Pi first and let it fully boot
2. Power on the external PSU second

Powering the strip before the Pi can send garbage data down the SPI line while the Pi boots, sometimes causing the first few LEDs to flicker or latch a random color.

---

## Safety Notes

> ⚠ **Never connect the strip's 5V wire to the Pi's 5V pins.** You will damage the Pi.

> ⚠ **Double-check GND before powering on.** A missing common ground means the strip won't respond and you'll spend time debugging software that's actually fine.

> ⚠ **Make sure the strip's arrow markings point away from your connector.** Wiring to the output end of the strip does nothing.

---

## Optional: Level Shifter (74AHCT125)

The Pi's SPI runs at 3.3V; the SK9822 officially wants 5V data. In practice most strips work fine at 3.3V, but if you see corrupted colors or flickering at higher speeds, add a 74AHCT125 between the Pi and the strip:

```
  74AHCT125 (14-pin DIP)

        ┌────┬────┐
   1OE ─┤ 1  │ 14 ├─ VCC (5V from PSU)
   Pi   │    │    │
  MOSI ─┤ 2  │ 13 ├─ 4OE ─── GND
        │    │    │
  DATA ─┤ 3  │ 12 ├─ 4A  (unused)
  out   │    │    │
   2OE ─┤ 4  │ 11 ├─ 4Y  (unused)
  GND   │    │    │
   Pi   │    │    │
  SCLK ─┤ 5  │ 10 ├─ 3OE ─── GND
        │    │    │
 CLOCK ─┤ 6  │  9 ├─ 3A  (unused)
  out   │    │    │
   GND ─┤ 7  │  8 ├─ 3Y  (unused)
        └────┴────┘

  Pins 1 and 4 (OE) → GND  (enable both channels)
  Pin 14 (VCC) → 5V from external PSU
  Pin 7  (GND) → GND
```

Start without the level shifter — only add it if you see corrupted colors or flickering that can't be explained by software.
