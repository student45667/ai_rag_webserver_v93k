// =============================================================================
// FILE:        SENSOR_IC.spec
// DEVICE:      SENSOR_IC — Dummy SPI Accelerometer
// TESTER:      Advantest V93000 PS1600
// DESCRIPTION: Test Limits Table — lo/hi limits per test name
//              Referenced by test methods via SPEC.getLoLimit() / SPEC.getHiLimit()
//              Units noted in comments — test methods must convert to match
// REVISION:    1.0
// =============================================================================
//
// Limit Table Architecture:
//
//   SPEC file (this file)       <- stores named lo/hi limits
//        |
//   TESTSET.judgeAndLog()       <- test method calls with measured value
//        |
//   STDF PTR record             <- logged to datalog with pass/fail
//        |
//   BIN TABLE                   <- determines soft/hard bin assignment
//
// Format:  test_name  :  lo_limit ,  hi_limit ;   // unit — description
//
// =============================================================================

SPEC SENSOR_IC_limits {

    // =========================================================================
    // SECTION 1: CONTINUITY TESTS
    // Purpose: verify pin connectivity via forward-biased ESD diode
    // Method:  force -100uA into pin, measure resulting voltage
    // Expected: forward diode drop ~-0.6V to -0.7V
    // =========================================================================

    //                          lo (V)      hi (V)
    CONT_inputs_low  :          -0.90,      -0.30;    // V — input pin diode low (to GND)
    CONT_inputs_high :           0.30,       0.90;    // V — input pin diode high (to VDD)
    CONT_outputs_low :          -0.90,      -0.25;    // V — output pin diode low
    CONT_outputs_high:           0.25,       0.90;    // V — output pin diode high
    CONT_power_pins  :          -0.10,       0.10;    // V — power pin check (near 0V)


    // =========================================================================
    // SECTION 2: DC PARAMETRIC TESTS — SUPPLY CURRENT
    // Purpose: verify device draws expected current at nominal supply
    // Method:  force VDD, measure current from DPS
    // =========================================================================

    //                          lo (A)      hi (A)
    IDD_active_avdd  :           0.0,       80.0e-3;  // A — AVDD active mode current
    IDD_active_dvdd  :           0.0,       60.0e-3;  // A — DVDD active mode current
    IDD_active_iovdd :           0.0,       20.0e-3;  // A — IOVDD active mode current
    IDD_standby_avdd :           0.0,        5.0e-3;  // A — AVDD standby mode current
    IDD_standby_dvdd :           0.0,        3.0e-3;  // A — DVDD standby mode current
    IDD_total_active :           1.0e-3,   150.0e-3;  // A — total supply (all rails) active
    IDD_total_standby:           0.0,        8.0e-3;  // A — total supply standby


    // =========================================================================
    // SECTION 3: IDDQ — QUIESCENT LEAKAGE
    // Purpose: verify no excessive leakage in quiescent state
    // Method:  force VDD, run quiescent pattern, measure after settle
    // =========================================================================

    //                          lo (A)      hi (A)
    IDDQ_avdd        :           0.0,        1.0e-6;  // A — AVDD quiescent leakage
    IDDQ_dvdd        :           0.0,        1.0e-6;  // A — DVDD quiescent leakage
    IDDQ_iovdd       :           0.0,      500.0e-9;  // A — IOVDD quiescent leakage


    // =========================================================================
    // SECTION 4: INPUT LEAKAGE — IIL / IIH
    // Purpose: verify digital input pins not loading bus excessively
    // Method:  force VIL then VIH, measure resulting pin current via PPMU
    // =========================================================================

    //                          lo (A)      hi (A)
    IIL_spi_inputs   :        -10.0e-6,      0.0;    // A — input leakage at VIL
    IIH_spi_inputs   :          0.0,        10.0e-6; // A — input leakage at VIH
    IIL_ctrl_inputs  :        -10.0e-6,      0.0;    // A — control input leakage low
    IIH_ctrl_inputs  :          0.0,        10.0e-6; // A — control input leakage high


    // =========================================================================
    // SECTION 5: OUTPUT DRIVE LEVELS — VOL / VOH
    // Purpose: verify output drive strength meets spec
    // Method:  force load current, measure resulting output voltage
    // =========================================================================

    //                          lo (V)      hi (V)
    VOL_spi_miso     :          0.0,         0.4;    // V — MISO output low level
    VOH_spi_miso     :          1.4,         2.0;    // V — MISO output high level
    VOL_int_outputs  :          0.0,         0.4;    // V — INT1/INT2 output low
    VOH_int_outputs  :          1.4,         2.0;    // V — INT1/INT2 output high
    VOL_data_ready   :          0.0,         0.4;    // V — DATA_READY output low
    VOH_data_ready   :          1.4,         2.0;    // V — DATA_READY output high
    VOL_data_bus     :          0.0,         0.4;    // V — XDATA/YDATA/ZDATA bus low
    VOH_data_bus     :          1.4,         2.0;    // V — data bus high


    // =========================================================================
    // SECTION 6: FUNCTIONAL / SCAN TESTS
    // Purpose: verify digital logic correctness via pattern execution
    // Method:  execute vector pattern, capture pass/fail per pin
    // Values:  1 = PASS required, 0 = FAIL expected (for stuck-at fault)
    // =========================================================================

    //                          lo          hi
    SCAN_full_chain  :          1,           1;       // full scan chain pass
    SCAN_march_x     :          1,           1;       // MARCH-X memory test
    FUNC_spi_read    :          1,           1;       // SPI register read verify
    FUNC_spi_write   :          1,           1;       // SPI register write verify
    FUNC_reset_seq   :          1,           1;       // reset sequence functional
    FUNC_int_output  :          1,           1;       // interrupt output functional
    FUNC_data_ready  :          1,           1;       // data ready handshake


    // =========================================================================
    // SECTION 7: SPI PROTOCOL TESTS
    // Purpose: verify SPI interface read/write integrity
    // Method:  write known pattern, read back, compare
    // =========================================================================

    //                          lo          hi
    SPI_reg_read_id  :          0x1F,       0x1F;    // device ID register 0x1F
    SPI_reg_rw_check :          1,           1;       // read-write check pass
    SPI_timing_cs_ns :          8.0e-9,    100e-9;   // s — CS pulse width
    SPI_timing_clk_ns:          8.0e-9,    100e-9;   // s — CLK period


    // =========================================================================
    // SECTION 8: ACCELEROMETER SELF-TEST
    // Purpose: verify MEMS sensor response to internal self-test stimulus
    // Method:  enable self-test mode via SPI, read acceleration output
    // Expected: defined output change when self-test electrostatic force applied
    // =========================================================================

    //                          lo (LSB)    hi (LSB)
    SELFTEST_x_axis  :         100,         2000;     // LSB — X-axis self-test delta
    SELFTEST_y_axis  :         100,         2000;     // LSB — Y-axis self-test delta
    SELFTEST_z_axis  :         100,         2000;     // LSB — Z-axis self-test delta

    //                          lo (mg)     hi (mg)
    SELFTEST_x_mg    :         100.0,      1200.0;    // mg — X-axis (converted)
    SELFTEST_y_mg    :         100.0,      1200.0;    // mg — Y-axis (converted)
    SELFTEST_z_mg    :         100.0,      1200.0;    // mg — Z-axis (converted)


    // =========================================================================
    // SECTION 9: TIMING MARGIN TESTS
    // Purpose: verify setup/hold margin at system clock frequency
    // Method:  shmoo across timing edge, find pass/fail boundary
    // =========================================================================

    //                          lo (s)      hi (s)
    SETUP_margin_spi :          1.0e-9,    20.0e-9;  // s — SPI data setup margin
    HOLD_margin_spi  :          0.5e-9,    20.0e-9;  // s — SPI data hold margin
    PROP_delay_miso  :          1.0e-9,    15.0e-9;  // s — MISO propagation delay

}

// =============================================================================
// END SENSOR_IC.spec
// =============================================================================
