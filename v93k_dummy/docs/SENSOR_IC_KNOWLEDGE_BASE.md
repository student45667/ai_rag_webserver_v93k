# SENSOR_IC V93000 Test Program — Knowledge Base
## Dummy SPI Accelerometer · Advantest V93000 PS1600 · SmarTest 7

---

## Overview

This knowledge base documents a complete, self-consistent V93000 SmarTest 7 test program for a fictional 3-axis SPI accelerometer (`SENSOR_IC`). It is structured to serve as a RAG corpus for AI-assisted test program development, migration, and debugging.

All files are interconnected — test methods pull pin groups from the pin config, voltage levels from the levelset, timing parameters from the timing file, limits from the spec file, and report results through the testflow bin table.

---

## Device Under Test

| Attribute | Value |
|---|---|
| Device name | SENSOR_IC |
| Type | 3-axis MEMS accelerometer |
| Interface | SPI (CPOL=0, CPHA=0) |
| Supply voltage | 1.8V (AVDD, DVDD, IOVDD) |
| Resolution | 16-bit per axis |
| ODR range | 12.5 Hz to 400 Hz |
| Self-test | Electrostatic force, per axis |
| Package | QFP100 (40 active pins used) |

---

## File Architecture

```
SENSOR_IC/
│
├── pinconfig/
│   └── SENSOR_IC.pin          ← Channel map, pin groups
│
├── levels/
│   └── SENSOR_IC.lvl          ← VIL/VIH/VOL/VOH/DPS — 4 levelsets
│
├── timing/
│   └── SENSOR_IC.tim          ← Period, drive/compare edges — 4 timingsets
│
├── spec/
│   └── SENSOR_IC.spec         ← Test limits table — all tests
│
├── vectors/
│   └── SENSOR_IC_vectors.vec  ← ASCII pattern definitions
│
├── testmethods/
│   └── SENSOR_IC_testmethods.cpp  ← All C++ test method classes
│
└── testflow/
    └── SENSOR_IC.tf           ← Main testflow, bin table, test sequence
```

---

## File Interconnection Map

```
SENSOR_IC.pin  ──────────────────────────────────────────────────────┐
  defines: pin groups (ALL_INPUTS, SPI_PINS, CONT_inputs, etc.)      │
  used by: every test method via PPMU.pins() / DIGITAL / DPS.pin()   │
                                                                      │
SENSOR_IC.lvl  ──────────────────────────────────────────────────────┤
  defines: levelsets (nom_1v8, lo_1v62, hi_1v98, dc_only)            │
  used by: test method calls LEVEL.select(levelset_name)             │
  references: pin groups from .pin for EQUATIONS                     │
                                                                      │
SENSOR_IC.tim  ──────────────────────────────────────────────────────┤
  defines: timingsets (func_50mhz, spi_10mhz, slow_debug, cont_dc)  │
  used by: test method calls TIMING.select(timingset_name)           │
  references: pin groups from .pin for edge assignments              │
                                                                      │
SENSOR_IC.spec ──────────────────────────────────────────────────────┤
  defines: named lo/hi limits for every test                         │
  used by: SPEC.getLoLimit(name) / SPEC.getHiLimit(name) in C++     │
                                                                      │
SENSOR_IC_vectors.vec ───────────────────────────────────────────────┤
  defines: ASCII patterns (iddq_quiescent, spi_transaction, etc.)    │
  references: timingset device_cycle names                           │
  used by: DIGITAL.loadPattern() / executePattern() in C++          │
                                                                      │
SENSOR_IC_testmethods.cpp ───────────────────────────────────────────┤
  implements: all TestMethod classes                                  │
  pulls from: .pin (groups), .lvl (levelset), .tim (timingset)       │
              .spec (limits), .vec (patterns)                        │
  reports to: TESTSET().judgeAndLog_*() → STDF datalog              │
              SET_SOFTBIN() / SET_HARDBIN() → wafer map             │
                                                                      │
SENSOR_IC.tf (testflow) ─────────────────────────────────────────────┘
  orchestrates: test sequence, parameters, bin table
  calls: each TESTSUITE with levelset/timingset/spec parameters
  defines: BIN_TABLE mapping soft → hard bins → PASS/FAIL
```

---

## Levelsets

| Levelset | AVDD/DVDD/IOVDD | VIL | VIH | VOL | VOH | Use case |
|---|---|---|---|---|---|---|
| `nom_1v8` | 1.80V | 0.36V | 1.26V | 0.4V | 1.4V | Standard production |
| `lo_1v62` | 1.62V | 0.32V | 1.13V | 0.4V | 1.2V | Low voltage corner |
| `hi_1v98` | 1.98V | 0.40V | 1.39V | 0.4V | 1.6V | High voltage corner |
| `dc_only` | 1.80V | — | — | — | — | DC parametric / IDDQ |

---

## Timingsets

| Timingset | Period | CLK freq | Use case |
|---|---|---|---|
| `func_50mhz` | 20ns | 50MHz | Functional, scan tests |
| `spi_10mhz` | 100ns | 10MHz | SPI register R/W, self-test |
| `slow_debug` | 1000ns | 1MHz | Debug, first silicon, margin |
| `cont_dc` | 10000ns | 0.1MHz | Continuity, IDDQ, DC parametric |

---

## Test Method Classes

### 1. `ContinuityTest`
- **Purpose:** Verify pin contact via ESD diode forward bias
- **Instruments:** PPMU (per-pin parametric measurement)
- **Method:** Force -100µA, measure voltage
- **Expected:** ~-0.6V (GND diode) or ~+0.6V (VDD diode)
- **Levelset:** `cont_dc` — DPS on, all digital pins tristated
- **Timingset:** `cont_dc`
- **Spec refs:** `CONT_inputs_low`, `CONT_inputs_high`, `CONT_outputs_low`, `CONT_outputs_high`
- **Bins:** 10 (input open/short), 11 (output open/short)
- **Flow:** STOP on fail — downstream tests meaningless without contact

### 2. `IddTest`
- **Purpose:** Measure supply current in specified operating mode
- **Instruments:** DPS (device power supply current measurement)
- **Method:** Apply supply, run mode-setting pattern, wait settle, measure DPS current
- **Levelset:** `nom_1v8`
- **Timingset:** `cont_dc`
- **Spec refs:** `IDD_active_avdd`, `IDD_active_dvdd`, `IDD_standby_avdd`
- **Bins:** 20–24

### 3. `IddqTest`
- **Purpose:** Quiescent leakage current — detects stuck-on transistors
- **Instruments:** DPS
- **Method:** Drive all nodes to quiescent state, long settle, measure residual current
- **Spec refs:** `IDDQ_avdd`, `IDDQ_dvdd`, `IDDQ_iovdd`
- **Bins:** 30–32

### 4. `InputLeakageTest`
- **Purpose:** Verify input pin leakage at VIL and VIH
- **Instruments:** PPMU (force voltage, measure current)
- **Method:** Force VIL → measure IIL; force VIH → measure IIH
- **Spec refs:** `IIL_spi_inputs`, `IIH_spi_inputs`, `IIL_ctrl_inputs`, `IIH_ctrl_inputs`
- **Bins:** 42–43

### 5. `OutputLevelTest`
- **Purpose:** Verify output drive strength VOL and VOH
- **Instruments:** PPMU (force current, measure voltage)
- **Method:** Sink IOL → measure VOL; source IOH → measure VOH
- **Spec refs:** `VOL_spi_miso`, `VOH_spi_miso`, `VOL_data_bus`, `VOH_data_bus`
- **Bins:** 40–41

### 6. `ScanTest`
- **Purpose:** Structural fault coverage via scan chain
- **Instruments:** DIGITAL (pattern execution, pass/fail capture)
- **Method:** Load ATPG scan pattern, execute, compare
- **Pattern:** `scan_full_chain.vec` (WGL/STIL converted)
- **Spec refs:** `SCAN_full_chain`
- **Bins:** 50

### 7. `FunctionalTest`
- **Purpose:** Generic functional pattern execution
- **Instruments:** DIGITAL
- **Method:** Load pattern, execute, compare all outputs
- **Patterns:** `func_reset_sequence.vec`, `func_interrupt_test.vec`
- **Bins:** 51–54

### 8. `SpiRegisterTest`
- **Purpose:** SPI register read/write integrity
- **Instruments:** DIGITAL (SPI pattern stream)
- **Method:** Write test pattern, read back, verify match; check device ID
- **Pattern:** `spi_transaction.vec` (parameterized per transaction)
- **Spec refs:** `SPI_reg_read_id`, `SPI_reg_rw_check`
- **Bins:** 51–52

### 9. `SelfTestMEMS`
- **Purpose:** MEMS accelerometer electrostatic self-test
- **Instruments:** DIGITAL (SPI), then analog readback
- **Method:** Read baseline, enable self-test bit, read delta, verify range
- **Register map:** REG_SELFTEST=0x2D, XDATA=0x08, YDATA=0x0A, ZDATA=0x0C
- **Spec refs:** `SELFTEST_x_mg`, `SELFTEST_y_mg`, `SELFTEST_z_mg`
- **Bins:** 60–62

---

## Bin Table Summary

| Soft Bin | Hard Bin | Result | Category |
|---|---|---|---|
| 1 | 1 | PASS | All tests passed |
| 10–12 | 0 | FAIL | Continuity (contact) |
| 20–24 | 0 | FAIL | IDD supply current |
| 30–32 | 0 | FAIL | IDDQ leakage |
| 40–43 | 0 | FAIL | I/O levels (VOL/VOH/IIL/IIH) |
| 50–54 | 0 | FAIL | Functional / scan |
| 60–62 | 0 | FAIL | MEMS self-test |
| 70–72 | 0 | FAIL | Timing margin |
| 255 | 0 | FAIL | Untested / abort |

---

## Test Execution Flow

```
POWER ON
    │
    ▼
[1] CONTINUITY ──FAIL──► BIN 10/11/12 ──► STOP (no downstream)
    │ PASS
    ▼
[2] IDD ACTIVE (AVDD, DVDD) ──FAIL──► BIN 20/21 ──► CONTINUE
    │
    ▼
[3] IDD STANDBY ──FAIL──► BIN 24 ──► CONTINUE
    │
    ▼
[4] IDDQ (AVDD, DVDD) ──FAIL──► BIN 30/31 ──► CONTINUE
    │
    ▼
[5] INPUT LEAKAGE (IIL/IIH) ──FAIL──► BIN 42/43 ──► CONTINUE
    │
    ▼
[6] OUTPUT LEVELS (VOL/VOH) ──FAIL──► BIN 40/41 ──► CONTINUE
    │
    ▼
[7] SCAN FULL CHAIN ──FAIL──► BIN 50 ──► CONTINUE
    │
    ▼
[8] SPI ID READ + R/W ──FAIL──► BIN 51/52 ──► CONTINUE
    │
    ▼
[9] FUNCTIONAL (RESET, INT) ──FAIL──► BIN 53/54 ──► CONTINUE
    │
    ▼
[10] MEMS SELF-TEST (X/Y/Z) ──FAIL──► BIN 60/61/62 ──► CONTINUE
    │
    ▼
ALL PASS ──► BIN 1 (PASS)
```

---

## Key Design Decisions

**Why continuity first?**
No contact = no valid data from any downstream test. Catching it early saves ~500ms of test time per bad contact site.

**Why `CONTINUE` on most failures?**
Production yield analysis needs full test data per device — knowing which tests failed (not just that it failed) drives process improvement and bin definition.

**Why separate levelsets per corner?**
Same test method C++ code runs at nom/lo/hi corners without modification. The testflow calls `ts_idd_active` three times with different `levelset` parameters to cover all PVT corners.

**Why PPMU for continuity vs digital pins?**
PPMU provides per-pin parametric measurement — you get an actual voltage number (e.g., -0.65V) not just pass/fail. This helps distinguish open circuits (near 0V) from shorts to supply (near VDD) from good diode drops.

**Why SPI pattern in vectors vs test method C++?**
SPI protocol timing is fixed by device spec — putting it in a pattern ensures hardware-accurate timing down to nanoseconds. Test method C++ handles logic (what to write, what to compare) while the vector handles timing (exactly when each bit toggles).

---

## Datalog Output (STDF PTR Record Example)

Each `TESTSET().judgeAndLog_ParametricTest()` call generates one PTR per site:

```
PTR  site=1  test="CONT_V"        lo=-0.90  result=-0.652  hi=-0.30  PASS
PTR  site=2  test="CONT_V"        lo=-0.90  result=-0.661  hi=-0.30  PASS
PTR  site=3  test="CONT_V"        lo=-0.90  result=0.012   hi=-0.30  FAIL  → BIN 10
PTR  site=4  test="CONT_V"        lo=-0.90  result=-0.648  hi=-0.30  PASS

PTR  site=1  test="IDD_active_avdd"  lo=0.0  result=0.0452  hi=0.08  PASS
PTR  site=1  test="IDDQ_avdd"        lo=0.0  result=0.00000082  hi=0.000001  PASS
PTR  site=1  test="VOL"              lo=0.0  result=0.182  hi=0.4   PASS
PTR  site=1  test="VOH"              lo=1.4  result=1.623  hi=2.0   PASS
FTR  site=1  test="SCAN_full_chain"  result=PASS
FTR  site=1  test="SPI_reg_read_id"  result=PASS
PTR  site=1  test="SELFTEST_x_mg"    lo=100.0  result=487.3  hi=1200.0  PASS
```

Site 3 fails continuity → hard bin 0, soft bin 10. Sites 1/2/4 continue to downstream tests.

---

## SPI Register Map (Partial)

| Address | Register | R/W | Default | Description |
|---|---|---|---|---|
| 0x00 | DEVID | R | 0x1F | Device ID — read-only, always 0x1F |
| 0x08 | XDATA_H | R | 0x00 | X-axis acceleration MSB |
| 0x09 | XDATA_L | R | 0x00 | X-axis acceleration LSB |
| 0x0A | YDATA_H | R | 0x00 | Y-axis acceleration MSB |
| 0x0B | YDATA_L | R | 0x00 | Y-axis acceleration LSB |
| 0x0C | ZDATA_H | R | 0x00 | Z-axis acceleration MSB |
| 0x0D | ZDATA_L | R | 0x00 | Z-axis acceleration LSB |
| 0x2C | BW_RATE | R/W | 0x0A | ODR and power mode control |
| 0x2D | SELFTEST | R/W | 0x00 | Self-test enable (bit[2:0] = Z/Y/X) |
| 0x2E | INT_ENABLE | R/W | 0x00 | Interrupt enable register |
| 0x30 | INT_MAP | R/W | 0x00 | Interrupt pin mapping |
| 0x38 | THRESH_ACT | R/W | 0x00 | Activity threshold |

---

## References

- Agilent/HP 93000 SOC Series Mixed-Signal Training Manual (ManualsLib)
- CIC Newsletter #153 — Advantest V93000 PS1600 Introduction (National Chip Implementation Center, Taiwan)
- Advantest V93000 Training Agenda Rev 7.2.2 (Scribd)
- Inflection Technologies V93000 Applications (inflectech.com)
- Origen-SDK/origen_std_lib (GitHub — open source V93000 test method library)
- gitfoxi/antikc (GitHub — 93k open source tooling)
- VTRAN by Source III — SmarTest 8 vector translation
- Solstice by TSSI — WGL/STIL → SmarTest 8 conversion

---

*This is a fictional test program created for AI knowledge base and training purposes.
All register addresses, limits, and configurations are representative examples only.*
