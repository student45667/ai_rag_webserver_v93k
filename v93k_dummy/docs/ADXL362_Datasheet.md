# ADXL362 Datasheet
## Micropower, 3-Axis, ±2 g/±4 g/±8 g Digital Output MEMS Accelerometer

**Rev. G** | Analog Devices

---

## FEATURES

- **Ultra low power**
  - Power can be derived from coin cell battery
  - 1.8 µA at 100 Hz ODR, 2.0 V supply
  - 3.0 µA at 400 Hz ODR, 2.0 V supply
  - 270 nA motion activated wake-up mode
  - 10 nA standby current

- **High resolution:** 1 mg/LSB

- **Built-in features for system level power savings:**
  - Adjustable threshold sleep/wake modes for motion activation
  - Autonomous interrupt processing, without need for microcontroller intervention
  - Deep embedded FIFO minimizes host processor load
  - Awake state output enables implementation of standalone, motion activated switch

- **Low noise down to 175 µg/√Hz**

- **Wide supply and I/O voltage ranges:** 1.6 V to 3.5 V
  - Operates off 1.8 V to 3.3 V rails

- **Acceleration sample synchronization via external trigger**

- **On-chip temperature sensor**

- **SPI digital interface**

- **Measurement ranges selectable via SPI command**

- **Small and thin 3 mm × 3.25 mm × 1.06 mm package**

---

## APPLICATIONS

- Hearing aids
- Home healthcare devices
- Motion enabled power save switches
- Wireless sensors
- Motion enabled metering devices

---

## GENERAL DESCRIPTION

The ADXL362 is an ultralow power, 3-axis MEMS accelerometer that consumes less than 2 µA at a 100 Hz output data rate and 270 nA when in motion triggered wake-up mode. Unlike accelerometers that use power duty cycling to achieve low power consumption, the ADXL362 does not alias input signals by undersampling; it samples the full bandwidth of the sensor at all data rates.

The ADXL362 always provides 12-bit output resolution; 8 bit formatted data is also provided for more efficient single byte transfers when a lower resolution is sufficient. Measurement ranges of ±2 g, ±4 g, and ±8 g are available, with a resolution of 1 mg/LSB on the ±2 g range.

---

## SPECIFICATIONS

### Sensor Input
- **Measurement Range:** User selectable ±2, ±4, ±8 g
- **Nonlinearity:** ±0.5 % of full scale
- **Sensor Resonant Frequency:** 3000 Hz
- **Cross Axis Sensitivity:** ±1.5 %

### Output Resolution
- **All g Ranges:** 12 Bits

### Sensitivity
- **Sensitivity Calibration Error:** ±10 %
- **Sensitivity at XOUT, YOUT, ZOUT:**
  - 2 g range: 1 mg/LSB
  - 4 g range: 2 mg/LSB
  - 8 g range: 4.255 mg/LSB

### Scale Factor
- **2 g range:** 1000 LSB/g
- **4 g range:** 500 LSB/g
- **8 g range:** 235 LSB/g

### 0 g Offset
- **XOUT, YOUT:** -150 to +150 mg
- **ZOUT:** -250 to +250 mg

### Noise Performance
- **Normal Operation:**
  - XOUT, YOUT: 550 µg/√Hz
  - ZOUT: 920 µg/√Hz
- **Low Noise Mode:**
  - XOUT, YOUT: 400 µg/√Hz
  - ZOUT: 550 µg/√Hz
- **Ultra Low Noise Mode (VS = 3.5 V):**
  - XOUT, YOUT: 175 µg/√Hz
  - ZOUT: 250 µg/√Hz

### Bandwidth
- **Low Pass (Antialiasing) Filter, −3 dB Corner:**
  - HALF_BW = 0: ODR/2 Hz
  - HALF_BW = 1: ODR/4 Hz

### Output Data Rate (ODR)
- **User selectable in 8 steps:** 12.5 to 400 Hz

### Power Supply
- **Operating Voltage Range (VS):** 1.6 V to 3.5 V
- **I/O Voltage Range (VDD I/O):** 1.6 V to VS

### Supply Current
- **Measurement Mode (100 Hz ODR, 50 Hz bandwidth):**
  - Normal Operation: 1.8 µA
  - Low Noise Mode: 3.3 µA
  - Ultra Low Noise Mode: 13 µA
- **Wake-Up Mode:** 0.27 µA
- **Standby:** 0.01 µA

### Temperature Sensor
- **Resolution:** 12 Bits
- **Sensitivity Average:** 0.065 °C/LSB
- **Sensitivity Repeatability:** ±0.5 °C

### Environmental
- **Operating Temperature Range:** -40°C to +85°C

---

## ABSOLUTE MAXIMUM RATINGS

| Parameter | Rating |
|-----------|--------|
| Acceleration (Any Axis, Unpowered) | 5000 g |
| Acceleration (Any Axis, Powered) | 5000 g |
| VS | -0.3 V to +3.6 V |
| VDD I/O | -0.3 V to +3.6 V |
| All Other Pins | -0.3 V to VS |
| ESD | 2000 V (HBM) |
| Temperature Range (Powered) | -50°C to +150°C |

---

## PIN CONFIGURATION

### 16-Terminal LGA Pinout

| Pin | Mnemonic | Description |
|-----|----------|-------------|
| 1 | VDD I/O | Supply Voltage for Digital I/O |
| 4 | SCLK | SPI Communications Clock |
| 6 | MOSI | Master Output, Slave Input (SPI data input) |
| 7 | MISO | Master Input, Slave Output (SPI data output) |
| 8 | CS | SPI Chip Select, Active Low |
| 9 | INT2 | Interrupt 2 Output / Sync Sampling Input |
| 11 | INT1 | Interrupt 1 Output / External Clock Input |
| 12, 13, 16 | GND | Ground |
| 14 | VS | Supply Voltage |

---

## OPERATING MODES

### Measurement Mode
- Normal operating mode
- Continuous wide bandwidth sensing
- Acceleration data read continuously
- Consumes less than 3 µA across entire range of ODR up to 400 Hz

### Wake-Up Mode
- Ideal for simple motion detection
- Extremely low power consumption: 270 nA at 2.0 V
- Useful for motion activated on/off switch
- Measures acceleration only about 6 times per second

### Standby
- Suspends measurement
- Reduces current consumption to 10 nA (typical)
- Preserves pending interrupts and data

---

## SELECTABLE MEASUREMENT RANGES

- **±2 g** (Default) - 1 mg/LSB sensitivity
- **±4 g** - 2 mg/LSB sensitivity
- **±8 g** - 4.255 mg/LSB sensitivity

Acceleration samples always converted by 12-bit ADC; sensitivity scales with g range.

---

## OUTPUT DATA RATES

User selectable from 12.5 Hz to 400 Hz:
- 12.5 Hz
- 25 Hz
- 50 Hz
- 100 Hz (default)
- 200 Hz
- 400 Hz

---

## MOTION DETECTION

### Activity Detection
- Detected when acceleration remains above specified threshold for specified time
- **Referenced Configuration:** Detects deviation from reference point (removes gravity effect)
- **Absolute Configuration:** Compares acceleration to user-set threshold

### Inactivity Detection
- Detected when acceleration remains below specified threshold for specified time
- Useful for eliminating effects of static acceleration due to gravity
- Timer can range from 2.5 ms to almost 90 minutes

### Linking Activity and Inactivity Detection
- **Default Mode:** Both enabled, interrupts serviced by host processor
- **Linked Mode:** Only one enabled at a time
- **Loop Mode:** Only one enabled at a time, interrupts internally acknowledged
- **Autosleep:** Device enters wake-up mode autonomously upon inactivity detection

---

## FIFO (First In, First Out)

- **Capacity:** 512-sample buffer
- **Equivalent to:** 170 sample sets of 3-axis data, or 128 sample sets with temperature

### FIFO Modes
- **Disabled:** No data stored
- **Oldest Saved Mode:** Accumulates data until full, then stops
- **Stream Mode:** Always contains most recent data, oldest discarded when full
- **Triggered Mode:** Saves samples surrounding activity detection event

---

## SERIAL COMMUNICATIONS

### SPI Interface
- **4-wire SPI**
- **Slave operation**
- **Recommended clock speeds:** 1 MHz to 8 MHz
- **Timing scheme:** CPHA = CPOL = 0

### SPI Commands
- **0x0A:** Write register
- **0x0B:** Read register
- **0x0D:** Read FIFO

### Multibyte Transfers (Burst)
- Supported for all SPI commands
- Register read/write auto-increment
- Halts at invalid Register Address 63 (0x3F)

---

## REGISTER MAP

### Key Registers

| Address | Name | Description |
|---------|------|-------------|
| 0x00 | DEVID_AD | Device ID (0xAD) |
| 0x01 | DEVID_MST | MEMS Device ID (0x1D) |
| 0x02 | PARTID | Part ID (0xF2) |
| 0x0B | STATUS | Status register (activity, inactivity, FIFO) |
| 0x0E-0x13 | XDATA, YDATA, ZDATA | 12-bit acceleration data (LSB, MSB) |
| 0x14-0x15 | TEMP | 12-bit temperature data |
| 0x20-0x21 | THRESH_ACT | Activity threshold registers |
| 0x22 | TIME_ACT | Activity time register |
| 0x23-0x24 | THRESH_INACT | Inactivity threshold registers |
| 0x25-0x26 | TIME_INACT | Inactivity time registers (16-bit) |
| 0x27 | ACT_INACT_CTL | Activity/inactivity control |
| 0x28 | FIFO_CONTROL | FIFO enable and mode selection |
| 0x29 | FIFO_SAMPLES | Number of samples to store in FIFO |
| 0x2A | INTMAP1 | INT1 function map |
| 0x2B | INTMAP2 | INT2 function map |
| 0x2C | FILTER_CTL | Range, bandwidth, ODR selection |
| 0x2D | POWER_CTL | Power mode, noise mode, measurement |
| 0x2E | SELF_TEST | Self test enable |

---

## STATUS REGISTER (0x0B)

| Bit | Name | Description |
|-----|------|-------------|
| 7 | ERR_USER_REGS | SEU error detect |
| 6 | AWAKE | Active/inactive state |
| 5 | INACT | Inactivity detected |
| 4 | ACT | Activity detected |
| 3 | FIFO_OVERRUN | FIFO overrun |
| 2 | FIFO_WATERMARK | FIFO watermark |
| 1 | FIFO_READY | FIFO ready |
| 0 | DATA_READY | New valid sample available |

---

## FILTER CONTROL REGISTER (0x2C)

| Bits | Name | Settings |
|------|------|----------|
| [7:6] | RANGE | 00: ±2g (default), 01: ±4g, 1X: ±8g |
| 4 | HALF_BW | 1: ODR/4 filter (default), 0: ODR/2 filter |
| 3 | EXT_SAMPLE | 1: Use INT2 for external sync |
| [2:0] | ODR | Output data rate selection |

---

## POWER CONTROL REGISTER (0x2D)

| Bits | Name | Settings |
|------|------|----------|
| 6 | EXT_CLK | 1: Use external clock on INT1 |
| [5:4] | LOW_NOISE | 00: Normal, 01: Low noise, 10: Ultra low noise |
| 3 | WAKEUP | 1: Wake-up mode enabled |
| 2 | AUTOSLEEP | 1: Autosleep enabled |
| [1:0] | MEASURE | 10: Measurement mode, 00: Standby |

---

## APPLICATIONS

### Autonomous Motion Switch
Uses activity/inactivity detection to control power to downstream circuitry via INT2 (AWAKE signal).

### Free Fall Detection
Implemented using inactivity detection in absolute mode:
- Set THRESH_INACT between 300-600 mg
- Set TIME_INACT between 100-350 ms
- Enables autonomous free fall detection

### Using External Triggering
- **INT1:** Can be configured as external clock input
- **INT2:** Can be configured as external trigger for synchronized sampling

---

## POWER SUPPLY

### Decoupling
- 0.1 µF ceramic capacitor at VS (close to device)
- 0.1 µF ceramic capacitor at VDD I/O (close to device)
- Recommended: Separate VS and VDD I/O supplies

### Power Supply Requirements
- Always start up from 0 V
- Discharge supplies completely before reapplication
- **VRESET:** ≤ 100 mV before power reapplication
- **Hold Time:** ≤ 200 ms below VRESET
- **Rise Time:** ≤ 250 µs from VRESET to 1.6 V

---

## THERMAL CHARACTERISTICS

| Package Type | θJA | θJC | Device Weight |
|--------------|-----|-----|---------------|
| 16-Terminal LGA | 150°C/W | 85°C/W | 18 mg |

---

## MECHANICAL CONSIDERATIONS

- Mount near hard mounting point of PCB to case
- Mounting at unsupported PCB location causes large measurement errors
- Multiple mounting points and thicker PCB reduce system resonance effects

---

## PACKAGE INFORMATION

- **Package Type:** 16-Terminal LGA (Land Grid Array)
- **Dimensions:** 3 mm × 3.25 mm × 1.06 mm
- **Branding:** Device ID (362), Pb-free designator, date code, factory lot code

---

## ORDERING GUIDE

| Model | Temperature Range | Package | Packing |
|-------|-------------------|---------|---------|
| ADXL362BCCZ-R2 | -40°C to +85°C | 16-Lead LGA | Reel, 250 |
| ADXL362BCCZ-RL | -40°C to +85°C | 16-Lead LGA | Reel, 5000 |
| ADXL362BCCZ-RL7 | -40°C to +85°C | 16-Lead LGA | Reel, 1500 |

---

## EVALUATION BOARDS

- **EVAL-ADXL362Z:** Breakout Board
- **EVAL-ADXL362Z-DB:** Datalogger and Development Board
- **EVAL-ADXL362Z-MLP:** Low Power Real-Time Evaluation System
- **EVAL-ADXL362Z-S:** Satellite Board for Evaluation System

---

## DOCUMENT INFORMATION

- **Revision:** G
- **Last Updated:** May 15, 2023
- **Manufacturer:** Analog Devices, Inc.
- **Website:** analog.com

---

## NOTES

- Specifications subject to change without notice
- No license granted by implication under any patent or patent rights
- For complete technical details, refer to the full datasheet
- All values at TA = 25°C unless otherwise noted
