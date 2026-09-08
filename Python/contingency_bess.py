"""Automated N-1 analysis and 50-MW BESS interconnection assessment."""
from __future__ import annotations

import pandas as pd

from config import VOLTAGE_MAX_PU, VOLTAGE_MIN_PU
from dss_utils import bus_voltage_rows, ensure_output_dir, line_loading_rows, transformer_loading_rows
from study_cases import apply_n1_case, apply_operating_case


def _assess(label: str, runner, use_emergency_line_rating: bool = False) -> dict:
    runner()
    v = pd.DataFrame(bus_voltage_rows())
    l = pd.DataFrame(line_loading_rows())
    t = pd.DataFrame(transformer_loading_rows())

    min_v = float(v["min_pu"].min())
    max_v = float(v["max_pu"].max())
    line_col = "emergency_loading_pct" if use_emergency_line_rating else "normal_loading_pct"
    max_line = float(l[line_col].max()) if not l.empty else 0.0
    max_tx = float(t["loading_pct"].max()) if not t.empty else 0.0
    voltage_ok = min_v >= VOLTAGE_MIN_PU and max_v <= VOLTAGE_MAX_PU
    thermal_ok = max_line <= 100.0 and max_tx <= 100.0

    if voltage_ok and thermal_ok:
        finding = "No voltage or normal-rating constraint identified."
    else:
        issues = []
        if not voltage_ok:
            issues.append("voltage")
        if not thermal_ok:
            issues.append("thermal loading")
        finding = "Constraint identified: " + " and ".join(issues) + "."

    return {
        "case": label,
        "min_voltage_pu": min_v,
        "max_voltage_pu": max_v,
        "max_line_loading_pct": max_line,
        "max_transformer_loading_pct": max_tx,
        "voltage_status": "PASS" if voltage_ok else "FAIL",
        "thermal_status": "PASS" if thermal_ok else "FAIL",
        "overall_status": "PASS" if voltage_ok and thermal_ok else "CONSTRAINT",
        "engineering_finding": finding,
    }


def run_n1() -> pd.DataFrame:
    cases = [
        ("C01 LINE230A outage", lambda: apply_n1_case("line230a")),
        ("C02 LINE230B outage", lambda: apply_n1_case("line230b")),
        ("C03 T2 outage + transfer", lambda: apply_n1_case("t2_transfer")),
        ("C04 T3 outage + transfer", lambda: apply_n1_case("t3_transfer")),
        ("C05 Generator outage + SST", lambda: apply_n1_case("generator")),
        ("C06 Feeder A outage + tie", lambda: apply_n1_case("feeder_a")),
    ]
    df = pd.DataFrame([_assess(label, runner, use_emergency_line_rating=True) for label, runner in cases])
    out = ensure_output_dir("contingency")
    df.to_csv(out / "n1_summary.csv", index=False)
    return df


def run_bess_assessment() -> pd.DataFrame:
    cases = [
        ("Peak load + BESS charging 50 MW", lambda: apply_operating_case("peak_bess_charge")),
        ("Light load + BESS discharging 50 MW", lambda: apply_operating_case("light_bess_discharge")),
        ("Normal base reference", lambda: apply_operating_case("normal")),
    ]
    df = pd.DataFrame([_assess(label, runner) for label, runner in cases])
    out = ensure_output_dir("bess")
    df.to_csv(out / "bess_interconnection_summary.csv", index=False)
    return df


if __name__ == "__main__":
    print("N-1\n", run_n1().to_string(index=False))
    print("\nBESS\n", run_bess_assessment().to_string(index=False))
