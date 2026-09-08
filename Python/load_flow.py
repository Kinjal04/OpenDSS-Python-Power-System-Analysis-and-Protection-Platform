"""Normal / peak / light load-flow studies with automated limit checks."""
from __future__ import annotations

import pandas as pd

from config import VOLTAGE_MAX_PU, VOLTAGE_MIN_PU
from dss_utils import (
    bus_voltage_rows,
    circuit_power_and_losses,
    ensure_output_dir,
    line_loading_rows,
    transformer_loading_rows,
)
from study_cases import apply_operating_case


def analyze_case(case: str, save: bool = True) -> dict:
    apply_operating_case(case)

    vdf = pd.DataFrame(bus_voltage_rows())
    ldf = pd.DataFrame(line_loading_rows())
    tdf = pd.DataFrame(transformer_loading_rows())
    power = circuit_power_and_losses()

    vdf["status"] = vdf.apply(
        lambda r: "PASS" if r["min_pu"] >= VOLTAGE_MIN_PU and r["max_pu"] <= VOLTAGE_MAX_PU else "FAIL",
        axis=1,
    )
    if not ldf.empty:
        ldf["status"] = ldf["normal_loading_pct"].apply(lambda x: "PASS" if x <= 100.0 else "OVERLOAD")
    if not tdf.empty:
        tdf["status"] = tdf["loading_pct"].apply(lambda x: "PASS" if x <= 100.0 else "OVERLOAD")

    summary = {
        "case": case,
        "min_voltage_pu": float(vdf["min_pu"].min()),
        "max_voltage_pu": float(vdf["max_pu"].max()),
        "max_line_loading_pct": float(ldf["normal_loading_pct"].max()) if not ldf.empty else 0.0,
        "max_transformer_loading_pct": float(tdf["loading_pct"].max()) if not tdf.empty else 0.0,
        "voltage_pass": bool((vdf["status"] == "PASS").all()),
        "thermal_pass": bool((ldf["status"] == "PASS").all() and (tdf["status"] == "PASS").all()),
        **power,
    }
    summary["overall_status"] = "PASS" if summary["voltage_pass"] and summary["thermal_pass"] else "FAIL"

    if save:
        out = ensure_output_dir("load_flow", case)
        vdf.to_csv(out / "bus_voltages.csv", index=False)
        ldf.to_csv(out / "line_loading.csv", index=False)
        tdf.to_csv(out / "transformer_loading.csv", index=False)
        pd.DataFrame([summary]).to_csv(out / "summary.csv", index=False)

    return {"summary": summary, "voltages": vdf, "lines": ldf, "transformers": tdf}


def run_all_load_flow() -> pd.DataFrame:
    rows = [analyze_case(case)["summary"] for case in ("normal", "peak", "light")]
    df = pd.DataFrame(rows)
    out = ensure_output_dir("load_flow")
    df.to_csv(out / "all_cases_summary.csv", index=False)
    return df


if __name__ == "__main__":
    print(run_all_load_flow().to_string(index=False))
