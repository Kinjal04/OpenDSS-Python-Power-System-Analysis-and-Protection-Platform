"""Project-wide settings for the Integrated Power System platform."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DSS_DIR = PROJECT_ROOT / "DSS"
MASTER_DSS = DSS_DIR / "Master.dss"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

VOLTAGE_MIN_PU = 0.95
VOLTAGE_MAX_PU = 1.05
NORMAL_LOADING_LIMIT_PCT = 100.0
EMERGENCY_LOADING_LIMIT_PCT = 100.0
CTI_MIN_S = 0.20

# Nameplate ratings used for transformer thermal checks.
TRANSFORMER_KVA = {
    "Transformer.T1": 150_000.0,
    "Transformer.T2": 40_000.0,
    "Transformer.T3": 40_000.0,
    "Transformer.GSU": 30_000.0,
    "Transformer.UAT": 10_000.0,
    "Transformer.SST": 10_000.0,
    "Transformer.TBESS": 60_000.0,
}

# Elements for thermal-limit reporting. Breaker proxy lines use a high switch
# rating and are therefore excluded from feeder conductor thermal checks.
THERMAL_LINES = [
    "Line.LINE230A", "Line.LINE230B",
    "Line.A01", "Line.A02", "Line.A03", "Line.A04", "Line.A05", "Line.A06",
    "Line.B01", "Line.B02", "Line.B03", "Line.B04", "Line.B05", "Line.B06",
    "Line.TIE_AB",
]

FAULT_BUSES = ["BUS230", "BUS115", "BUS27A", "BUS27B", "A03", "A06", "B03", "B06", "AUX416", "BESS34"]

# Synthetic interrupting ratings selected for the academic breaker-duty check.
# These are study assumptions, not utility specifications.
BREAKER_DUTY_KA = {
    "BUS230": 40.0,
    "BUS115": 31.5,
    "BUS27A": 25.0,
    "BUS27B": 25.0,
    "A03": 16.0,
    "A06": 16.0,
    "B03": 16.0,
    "B06": 16.0,
    "AUX416": 50.0,
    "BESS34": 25.0,
}

# TCC data exactly matching DSS/ProtectionCurves.dss.
TCC_CURVES = {
    "RELAY_NI": {
        "m": [1.10, 1.25, 1.50, 2.00, 3.00, 5.00, 8.00, 12.00, 20.00, 30.00],
        "t": [20.0, 10.0, 6.0, 3.0, 1.50, 0.70, 0.38, 0.25, 0.16, 0.12],
    },
    "REC_FAST": {
        "m": [1.10, 1.30, 1.60, 2.00, 3.00, 5.00, 8.00, 12.00, 20.00],
        "t": [2.00, 1.00, 0.50, 0.28, 0.13, 0.070, 0.045, 0.035, 0.030],
    },
    "REC_SLOW": {
        "m": [1.10, 1.30, 1.60, 2.00, 3.00, 5.00, 8.00, 12.00, 20.00],
        "t": [12.0, 6.00, 3.20, 1.80, 0.80, 0.35, 0.20, 0.14, 0.10],
    },
    "FUSE_A_CURVE": {
        "m": [1.20, 1.50, 2.00, 3.00, 5.00, 8.00, 12.00, 20.00, 30.00],
        "t": [30.0, 10.0, 3.50, 1.20, 0.40, 0.18, 0.10, 0.055, 0.040],
    },
}

# Study settings mirror DSS/Protection.dss. The delayed recloser shot is
# intentionally slower than the downstream fuse; feeder relay time dials are
# slower again to provide backup coordination.
PROTECTION = {
    "fuse_a": {
        "element": "Line.A05", "pickup": 250.0, "curve": "FUSE_A_CURVE",
    },
    "rec_a_phase_fast": {
        "element": "Line.A03", "pickup": 450.0, "curve": "REC_FAST", "td": 1.0,
        "instantaneous": 6000.0, "fixed_delay": 0.04,
    },
    "rec_a_phase_slow": {
        "element": "Line.A03", "pickup": 450.0, "curve": "REC_SLOW", "td": 2.0,
        "instantaneous": None, "fixed_delay": 0.04,
    },
    "rec_a_ground_slow": {
        "element": "Line.A03", "pickup": 180.0, "curve": "REC_SLOW", "td": 2.5,
        "instantaneous": None, "fixed_delay": 0.04,
    },
    "relay_a_phase": {
        "element": "Line.BRK_A", "pickup": 650.0, "curve": "RELAY_NI", "td": 1.2,
        "instantaneous": 8000.0, "fixed_delay": 0.05,
    },
    "relay_a_ground": {
        "element": "Line.BRK_A", "pickup": 220.0, "curve": "RELAY_NI", "td": 2.0,
        "instantaneous": 3000.0, "fixed_delay": 0.05,
    },
    "relay_230_phase": {
        "element": "Transformer.T1", "pickup": 500.0, "curve": "RELAY_NI", "td": 0.65,
        "instantaneous": 1200.0, "fixed_delay": 0.05,
    },
    "relay_230_ground": {
        "element": "Transformer.T1", "pickup": 120.0, "curve": "RELAY_NI", "td": 0.55,
        "instantaneous": 500.0, "fixed_delay": 0.05,
    },
}
