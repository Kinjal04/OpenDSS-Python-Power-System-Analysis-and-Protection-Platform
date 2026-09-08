INTEGRATED POWER SYSTEM - OPENDSS FILE SET
==========================================

START HERE
----------
Compile Master.dss for the normal base case.

The model follows this electrical architecture:
  230-kV external Thevenin grid
      -> two parallel 230-kV circuits
      -> T1 230/115 kV, 150 MVA
      -> 115-kV bus
      -> T2/T3 115/27.6-kV feeders
      -> normally-open A06-B06 tie
  plus:
      20-MW / 25-MVA generator at 13.8 kV through GSU
      UAT + backup SST supplying a 4.16-kV auxiliary bus
      5-MW PV at A05
      1/4/8-MW rail traction load at B04
      50-MW / 200-MWh BESS through a 115/34.5-kV, 60-MVA transformer

CORE DSS FILES
--------------
  Master.dss
  LineCodes.dss
  Lines.dss
  Transformers.dss
  LoadShapes.dss
  Loads.dss
  Generation.dss
  BESS.dss
  ProtectionCurves.dss
  Protection.dss
  Faults.dss
  Monitors.dss

SCENARIOS
---------
  Scenarios/Normal.dss
  Scenarios/Peak.dss
  Scenarios/Light.dss
  Scenarios/Peak_BESS_Charge.dss
  Scenarios/Light_BESS_Discharge.dss
  Scenarios/Aux_SST_Backup.dss
  Scenarios/Feeder_A_Restoration.dss
  Scenarios/Rail_Daily.dss

STUDIES
-------
  Studies/FaultStudy.dss
  Studies/N1_LINE230A.dss
  Studies/N1_LINE230B.dss
  Studies/N1_T2_With_Transfer.dss
  Studies/N1_T3_With_Transfer.dss
  Studies/N1_Generator.dss

BASE MODEL SUMMARY
------------------
  Physical buses:                22
  Base connected load:           40.0 MW
  Synchronous generation:        20 MW / 25 MVA
  PV:                            5 MW
  BESS:                          50 MW / 200 MWh / 60 MVA inverter
  Feeder line rating:            650 A normal / 720 A emergency
  Source:                        230 kV, 1.025 pu, 5000 MVA 3ph, 3500 MVA SLG

TOPOLOGY CONVENTIONS
--------------------
  CB-230A / CB-230B -> open Line.LINE230A / Line.LINE230B terminal 1
  CB-T1             -> open Transformer.T1 terminal 1
  CB-T2 / CB-T3     -> open Transformer.T2 / T3 terminal 1
  CB-GEN             -> open Transformer.GSU terminal 1
  CB-BESS            -> open Transformer.TBESS terminal 1
  CB-SST             -> represented by Transformer.SST Enabled=No/Yes
  CB-A / CB-B        -> Line.BRK_A / Line.BRK_B
  CB-TIE             -> Line.TIE_AB (normally open)
  Recloser A/B       -> control Line.A03 / Line.B03
  Fuse A             -> controls Line.A05

The high-voltage breaker labels do not require extra zero-length buses in the
OpenDSS network. Opening the associated line/transformer terminal represents the
same switching topology and keeps the project at the intended ~20-bus scale.

PROTECTION / STUDY BEHAVIOR
---------------------------
Master.dss uses ControlMode=Off intentionally. That allows Python to measure
pre-trip overloads/violations during load-flow, BESS, and N-1 studies. Relay,
recloser, fuse, and TCC objects are still fully defined in Protection*.dss for
coordination calculations and explicit protection/SCADA sequences.

Expected independent sanity-check results are in VALIDATION_REPORT.txt.
