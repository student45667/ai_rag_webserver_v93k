// =============================================================================
// FILE:        SENSOR_IC_testmethods.cpp
// DEVICE:      SENSOR_IC — Dummy SPI Accelerometer
// TESTER:      Advantest V93000 PS1600 / SmarTest 7
// DESCRIPTION: All test method class implementations
//              Each class maps to one TESTSUITE call in the testflow
//              All methods use multisite macros for parallel site execution
// COMPILE:     g++ -m32 -shared -fPIC -o SENSOR_IC_testmethods.so
//                  SENSOR_IC_testmethods.cpp -I/opt/hp93000/soc/include
// REVISION:    1.0
// =============================================================================

#include "testmethod.hpp"    // SmarTest base class + all instrument APIs
#include <string>
#include <cmath>
#include <vector>

using namespace std;


// =============================================================================
// TEST METHOD 1: ContinuityTest
// Purpose:  Verify pin connectivity via ESD protection diode
// Method:   Force small current (-100uA) into pin, measure resulting voltage
// Expected: Forward diode drop ~-0.6V (to GND) or ~0.6V (to VDD)
// Refs:     levelset=cont_dc, timingset=cont_dc
//           spec: CONT_inputs_low / CONT_inputs_high
// =============================================================================
class ContinuityTest : public TestMethod {
public:
    // ── parameters set from testflow ──────────────────────────
    string pin_group;           // e.g. "CONT_inputs" or "CONT_outputs"
    string spec_lo;             // spec name for lo limit
    string spec_hi;             // spec name for hi limit (diode high side)
    double force_curr;          // A — current to force (typically -100e-6)

    void init() {
        force_curr = -100e-6;   // default -100uA
    }

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            // Apply DC levelset — pins tristated, DPS active
            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            // Power up DUT
            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(1e-3);  // 1ms powerup settle

            // Force current into each pin serially (ESD diode forward bias)
            FOR_EACH_SITE_BEGIN();
                PPMU.pins(pin_group)
                    .iforce(force_curr)     // force -100uA
                    .vclamp(3.0)            // clamp voltage protection
                    .execute();
            FOR_EACH_SITE_END();

        ON_FIRST_INVOCATION_END();

        // Fetch limits from spec table
        double lo = SPEC.getLoLimit(spec_lo);
        double hi = SPEC.getHiLimit(spec_hi);

        // Measure voltage — runs in parallel across all active sites
        double vmeas = PPMU.pins(pin_group).vmeas();

        // Log and judge — one PTR record per site per pin in datalog
        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     pin_group,          // pin name in datalog
                     "CONT_V",           // test name in datalog
                     lo,                 // lo limit from spec
                     vmeas,              // measured value
                     hi                  // hi limit from spec
                 );

        // Assign wafer sort bin on failure
        bool pass = (vmeas >= lo && vmeas <= hi);
        if (!pass) {
            SET_SOFTBIN(soft_bin_fail);
            SET_HARDBIN(0);
        }
    }

    TP_PARAMETERS
        TP_PARAMETER(pin_group)
        TP_PARAMETER(spec_lo)
        TP_PARAMETER(spec_hi)
        TP_PARAMETER(force_curr)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("ContinuityTest", ContinuityTest);


// =============================================================================
// TEST METHOD 2: IddTest
// Purpose:  Measure supply current in specified operating mode
// Method:   Apply supply via DPS, run mode-setting pattern, measure current
// Refs:     levelset=nom_1v8, spec: IDD_active_avdd etc.
// =============================================================================
class IddTest : public TestMethod {
public:
    string dps_pin;             // e.g. "AVDD"
    string spec_name;           // spec limit name e.g. "IDD_active_avdd"
    string pattern;             // pattern to set operating mode
    double settle_us;           // us — settle time after powerup

    void init() {
        settle_us = 100.0;
    }

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            // Apply all power rails
            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(settle_us * 1e-6);

            // Load and execute mode-setting pattern
            // This puts DUT into correct operating state (active/standby)
            DIGITAL.loadPattern(pattern);
            DIGITAL.executePattern(pattern);
            WAIT(200e-6);   // allow mode transition to settle

        ON_FIRST_INVOCATION_END();

        double lo = SPEC.getLoLimit(spec_name);
        double hi = SPEC.getHiLimit(spec_name);

        // Measure current from specified DPS pin — parallel all sites
        double idd = DPS.pin(dps_pin).imeas();

        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     dps_pin, spec_name,
                     lo, idd, hi
                 );

        bool pass = (idd >= lo && idd <= hi);
        if (!pass) {
            SET_SOFTBIN(soft_bin_fail);
            SET_HARDBIN(0);
        }
    }

    TP_PARAMETERS
        TP_PARAMETER(dps_pin)
        TP_PARAMETER(spec_name)
        TP_PARAMETER(pattern)
        TP_PARAMETER(settle_us)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("IddTest", IddTest);


// =============================================================================
// TEST METHOD 3: IddqTest
// Purpose:  Measure quiescent (static) leakage current
// Method:   Force quiescent state via pattern, measure after long settle
//           IDDQ detects stuck-on transistors, shorts, excessive leakage
// Refs:     levelset=nom_1v8, spec: IDDQ_avdd etc.
// =============================================================================
class IddqTest : public TestMethod {
public:
    string dps_pin;
    string spec_name;
    string pattern;             // pattern to drive DUT to quiescent state
    double settle_us;

    void init() {
        settle_us = 200.0;
    }

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(1e-3);

            // Execute quiescent state pattern
            // All internal nodes driven to known stable state
            DIGITAL.loadPattern(pattern);
            DIGITAL.executePattern(pattern);

            // Long settle — allow all transients to decay
            WAIT(settle_us * 1e-6);

        ON_FIRST_INVOCATION_END();

        double lo = SPEC.getLoLimit(spec_name);
        double hi = SPEC.getHiLimit(spec_name);

        // Measure quiescent current — should be very small (nA/uA range)
        double iddq = DPS.pin(dps_pin).imeas();

        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     dps_pin, spec_name,
                     lo, iddq, hi
                 );

        bool pass = (iddq >= lo && iddq <= hi);
        if (!pass) {
            SET_SOFTBIN(soft_bin_fail);
            SET_HARDBIN(0);
        }
    }

    TP_PARAMETERS
        TP_PARAMETER(dps_pin)
        TP_PARAMETER(spec_name)
        TP_PARAMETER(pattern)
        TP_PARAMETER(settle_us)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("IddqTest", IddqTest);


// =============================================================================
// TEST METHOD 4: InputLeakageTest
// Purpose:  Measure input pin leakage current at VIL and VIH
// Method:   Force VIL, measure current (IIL); force VIH, measure (IIH)
//           Uses PPMU per-pin measurement unit
// Refs:     levelset=nom_1v8, spec: IIL_spi_inputs / IIH_spi_inputs
// =============================================================================
class InputLeakageTest : public TestMethod {
public:
    string pin_group;
    string spec_iil;            // spec name for IIL (low input leakage)
    string spec_iih;            // spec name for IIH (high input leakage)

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(500e-6);

            // Force RESET_N high to ensure DUT is active
            PPMU.pins("RESET_N").vforce(1.8).execute();
            WAIT(100e-6);

        ON_FIRST_INVOCATION_END();

        // ── IIL measurement — force VIL, measure leakage ─────
        double vil = SPEC.getValue("vil");       // from levelset equations
        double iil_lo = SPEC.getLoLimit(spec_iil);
        double iil_hi = SPEC.getHiLimit(spec_iil);

        PPMU.pins(pin_group).vforce(vil).execute();
        WAIT(10e-6);
        double iil = PPMU.pins(pin_group).imeas();

        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     pin_group, "IIL",
                     iil_lo, iil, iil_hi
                 );

        // ── IIH measurement — force VIH, measure leakage ─────
        double vih = SPEC.getValue("vih");
        double iih_lo = SPEC.getLoLimit(spec_iih);
        double iih_hi = SPEC.getHiLimit(spec_iih);

        PPMU.pins(pin_group).vforce(vih).execute();
        WAIT(10e-6);
        double iih = PPMU.pins(pin_group).imeas();

        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     pin_group, "IIH",
                     iih_lo, iih, iih_hi
                 );

        bool pass = (iil >= iil_lo && iil <= iil_hi &&
                     iih >= iih_lo && iih <= iih_hi);
        if (!pass) {
            SET_SOFTBIN(soft_bin_fail);
            SET_HARDBIN(0);
        }
    }

    TP_PARAMETERS
        TP_PARAMETER(pin_group)
        TP_PARAMETER(spec_iil)
        TP_PARAMETER(spec_iih)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("InputLeakageTest", InputLeakageTest);


// =============================================================================
// TEST METHOD 5: OutputLevelTest
// Purpose:  Verify output drive strength — VOL (output low) and VOH (output high)
// Method:   Force load current into output, measure resulting voltage
//           VOL: sink iol from output, measure voltage (should be low)
//           VOH: source ioh from output, measure voltage (should be high)
// Refs:     levelset=nom_1v8, spec: VOL_spi_miso / VOH_spi_miso
// =============================================================================
class OutputLevelTest : public TestMethod {
public:
    string out_pin;
    string spec_vol;
    string spec_voh;
    double iol;                 // A — sink current for VOL test
    double ioh;                 // A — source current for VOH test
    string pattern;             // pattern to drive output to known state

    void init() {
        iol = 4e-3;
        ioh = 4e-3;
    }

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(500e-6);

            // Drive DUT to state where output is in known condition
            DIGITAL.loadPattern(pattern);
            DIGITAL.executePattern(pattern);
            WAIT(50e-6);

        ON_FIRST_INVOCATION_END();

        // ── VOL measurement ───────────────────────────────────
        // Sink current from output pin (DUT drives low against load)
        double vol_lo = SPEC.getLoLimit(spec_vol);
        double vol_hi = SPEC.getHiLimit(spec_vol);

        PPMU.pins(out_pin).iforce(iol).execute();    // sink +iol (positive = sink)
        WAIT(5e-6);
        double vol = PPMU.pins(out_pin).vmeas();

        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     out_pin, "VOL",
                     vol_lo, vol, vol_hi
                 );

        // ── VOH measurement ───────────────────────────────────
        // Source current from output pin (DUT drives high against load)
        double voh_lo = SPEC.getLoLimit(spec_voh);
        double voh_hi = SPEC.getHiLimit(spec_voh);

        PPMU.pins(out_pin).iforce(-ioh).execute();   // source -ioh (negative = source)
        WAIT(5e-6);
        double voh = PPMU.pins(out_pin).vmeas();

        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     out_pin, "VOH",
                     voh_lo, voh, voh_hi
                 );

        bool pass = (vol >= vol_lo && vol <= vol_hi &&
                     voh >= voh_lo && voh <= voh_hi);
        if (!pass) {
            SET_SOFTBIN(soft_bin_fail);
            SET_HARDBIN(0);
        }
    }

    TP_PARAMETERS
        TP_PARAMETER(out_pin)
        TP_PARAMETER(spec_vol)
        TP_PARAMETER(spec_voh)
        TP_PARAMETER(iol)
        TP_PARAMETER(ioh)
        TP_PARAMETER(pattern)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("OutputLevelTest", OutputLevelTest);


// =============================================================================
// TEST METHOD 6: ScanTest
// Purpose:  Structural scan test — detect stuck-at faults via scan chain
// Method:   Load scan pattern (WGL/STIL converted), execute, capture results
// Refs:     levelset=nom_1v8, timingset=func_50mhz, spec: SCAN_full_chain
// =============================================================================
class ScanTest : public TestMethod {
public:
    string pattern;
    string spec_name;
    int    pass_bin;

    void init() {
        pass_bin = 1;
    }

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(1e-3);

            // Load and arm scan pattern in parallel
            DIGITAL.loadPattern(pattern);
            DIGITAL.armPattern(pattern);

        ON_FIRST_INVOCATION_END();

        // Execute scan — runs in parallel across all active sites
        DIGITAL.executePattern(pattern);

        // Get pass/fail result — 1=pass, 0=fail
        int result = DIGITAL.getPassFail("ALL_DIGITAL");

        double lo = SPEC.getLoLimit(spec_name);
        double hi = SPEC.getHiLimit(spec_name);

        TESTSET().cont(true)
                 .judgeAndLog_FunctionalTest(
                     spec_name,
                     result          // 1=pass, 0=fail
                 );

        SET_SOFTBIN(result ? pass_bin : soft_bin_fail);
        SET_HARDBIN(result ? 1 : 0);
    }

    TP_PARAMETERS
        TP_PARAMETER(pattern)
        TP_PARAMETER(spec_name)
        TP_PARAMETER(pass_bin)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("ScanTest", ScanTest);


// =============================================================================
// TEST METHOD 7: FunctionalTest
// Purpose:  Generic functional pattern test
// Method:   Load named pattern, execute, capture pass/fail
// Refs:     levelset=nom_1v8, various patterns and specs
// =============================================================================
class FunctionalTest : public TestMethod {
public:
    string pattern;
    string spec_name;

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(1e-3);

            DIGITAL.loadPattern(pattern);
            DIGITAL.armPattern(pattern);

        ON_FIRST_INVOCATION_END();

        DIGITAL.executePattern(pattern);
        int result = DIGITAL.getPassFail("ALL_DIGITAL");

        TESTSET().cont(true)
                 .judgeAndLog_FunctionalTest(spec_name, result);

        SET_SOFTBIN(result ? 1 : soft_bin_fail);
        SET_HARDBIN(result ? 1 : 0);
    }

    TP_PARAMETERS
        TP_PARAMETER(pattern)
        TP_PARAMETER(spec_name)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("FunctionalTest", FunctionalTest);


// =============================================================================
// TEST METHOD 8: SpiRegisterTest
// Purpose:  Verify SPI register read/write integrity
// Method:   Write known value via SPI, read back, compare
//           Catches SPI communication faults, stuck registers, wrong ID
// Refs:     levelset=nom_1v8, timingset=spi_10mhz
// =============================================================================
class SpiRegisterTest : public TestMethod {
public:
    int    reg_addr;            // register address to read/write
    int    expected;            // expected read-back value
    int    write_val;           // value to write (READ_WRITE mode)
    string rw_mode;             // "READ" or "READ_WRITE"
    string spec_name;

    void init() {
        rw_mode = "READ";
        expected = 0;
        write_val = 0;
    }

    // SPI helper — builds 16-bit SPI transaction
    // Bit 7 of first byte: R/W (0=write, 1=read)
    // Bits 6:0: register address
    // Byte 2: data
    int spiTransaction(int addr, int data, bool read) {
        int cmd = (read ? 0x80 : 0x00) | (addr & 0x3F);
        // In real implementation: load into SPI pattern via DMA or PPMU shift
        // Here represented as a pattern parameter load
        DIGITAL.setPatternParam("SPI_ADDR", cmd);
        DIGITAL.setPatternParam("SPI_DATA", data);
        DIGITAL.executePattern("spi_transaction.vec");
        return DIGITAL.getPatternResult("SPI_MISO_BYTE");
    }

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(5e-3);   // SPI device boot time

            DIGITAL.loadPattern("spi_transaction.vec");

        ON_FIRST_INVOCATION_END();

        int result_val = 0;
        bool pass = false;

        if (rw_mode == "READ") {
            // Read register and compare to expected
            result_val = spiTransaction(reg_addr, 0x00, true);
            pass = (result_val == expected);

            double lo = SPEC.getLoLimit(spec_name);
            double hi = SPEC.getHiLimit(spec_name);

            TESTSET().cont(true)
                     .judgeAndLog_ParametricTest(
                         "SPI_REG", spec_name,
                         lo, (double)result_val, hi
                     );

        } else if (rw_mode == "READ_WRITE") {
            // Write test pattern, read back, verify
            spiTransaction(reg_addr, write_val, false);  // write
            WAIT(10e-6);
            result_val = spiTransaction(reg_addr, 0x00, true);  // read back
            pass = (result_val == write_val);

            // Restore register default
            spiTransaction(reg_addr, 0x00, false);

            TESTSET().cont(true)
                     .judgeAndLog_FunctionalTest(spec_name, pass ? 1 : 0);
        }

        SET_SOFTBIN(pass ? 1 : soft_bin_fail);
        SET_HARDBIN(pass ? 1 : 0);
    }

    TP_PARAMETERS
        TP_PARAMETER(reg_addr)
        TP_PARAMETER(expected)
        TP_PARAMETER(write_val)
        TP_PARAMETER(rw_mode)
        TP_PARAMETER(spec_name)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("SpiRegisterTest", SpiRegisterTest);


// =============================================================================
// TEST METHOD 9: SelfTestMEMS
// Purpose:  Verify MEMS accelerometer mechanical response via self-test mode
// Method:   Enable self-test via SPI register write
//           Read baseline acceleration, enable self-test, read delta
//           Delta should fall within expected electrostatic force range
// Refs:     levelset=nom_1v8, timingset=spi_10mhz
//           spec: SELFTEST_x_mg / _y_mg / _z_mg
// =============================================================================
class SelfTestMEMS : public TestMethod {
public:
    string axis;                // "X", "Y", or "Z"
    string spec_name;           // spec limit name
    double sensitivity;         // mg/LSB — sensor sensitivity

    // Register map (from datasheet)
    static const int REG_SELFTEST   = 0x2D;   // self-test enable register
    static const int REG_XDATA_H    = 0x08;   // X-axis MSB
    static const int REG_YDATA_H    = 0x0A;   // Y-axis MSB
    static const int REG_ZDATA_H    = 0x0C;   // Z-axis MSB

    int getAxisReg() {
        if (axis == "X") return REG_XDATA_H;
        if (axis == "Y") return REG_YDATA_H;
        return REG_ZDATA_H;
    }

    int readAxisData() {
        DIGITAL.setPatternParam("SPI_ADDR", 0x80 | getAxisReg());
        DIGITAL.executePattern("spi_transaction.vec");
        int msb = DIGITAL.getPatternResult("SPI_MISO_BYTE");
        DIGITAL.setPatternParam("SPI_ADDR", 0x80 | (getAxisReg() + 1));
        DIGITAL.executePattern("spi_transaction.vec");
        int lsb = DIGITAL.getPatternResult("SPI_MISO_BYTE");
        return (int16_t)((msb << 8) | lsb);  // signed 16-bit
    }

    void writeSpiReg(int addr, int data) {
        DIGITAL.setPatternParam("SPI_ADDR", addr & 0x3F);
        DIGITAL.setPatternParam("SPI_DATA", data);
        DIGITAL.executePattern("spi_transaction.vec");
    }

    void run() {
        ON_FIRST_INVOCATION_BEGIN();

            LEVEL.select(levelset_name);
            TIMING.select(timingset_name);

            DPS.pin("AVDD").execute();
            DPS.pin("DVDD").execute();
            DPS.pin("IOVDD").execute();
            WAIT(10e-3);   // MEMS requires longer powerup settle

            DIGITAL.loadPattern("spi_transaction.vec");

            // Ensure device in measurement mode, self-test off
            writeSpiReg(REG_SELFTEST, 0x00);
            WAIT(5e-3);

        ON_FIRST_INVOCATION_END();

        // Read baseline (self-test off)
        int baseline = readAxisData();
        WAIT(1e-3);

        // Enable self-test on this axis
        int st_bit = (axis == "X") ? 0x01 :
                     (axis == "Y") ? 0x02 : 0x04;
        writeSpiReg(REG_SELFTEST, st_bit);
        WAIT(10e-3);   // MEMS electrostatic force settle time

        // Read with self-test active
        int st_reading = readAxisData();

        // Disable self-test
        writeSpiReg(REG_SELFTEST, 0x00);

        // Compute delta in mg
        int delta_lsb = abs(st_reading - baseline);
        double delta_mg = delta_lsb * sensitivity;

        double lo = SPEC.getLoLimit(spec_name);
        double hi = SPEC.getHiLimit(spec_name);

        TESTSET().cont(true)
                 .judgeAndLog_ParametricTest(
                     axis + "_AXIS", spec_name,
                     lo, delta_mg, hi
                 );

        bool pass = (delta_mg >= lo && delta_mg <= hi);
        SET_SOFTBIN(pass ? 1 : soft_bin_fail);
        SET_HARDBIN(pass ? 1 : 0);
    }

    TP_PARAMETERS
        TP_PARAMETER(axis)
        TP_PARAMETER(spec_name)
        TP_PARAMETER(sensitivity)
        TP_PARAMETER(soft_bin_fail)
    TP_PARAMETERS_END
};
REGISTER_TESTMETHOD("SelfTestMEMS", SelfTestMEMS);

// =============================================================================
// END SENSOR_IC_testmethods.cpp
// =============================================================================
