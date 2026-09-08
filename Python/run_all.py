"""Run every study required by the six resume bullets."""
from __future__ import annotations

import json
from pathlib import Path

from contingency_bess import run_bess_assessment, run_n1
from fault_study import run_fault_study
from load_flow import run_all_load_flow
from protection_coordination import run_protection_coordination
from scada_logic import run_fault_scenario
from smoke_test import main as smoke_test


def main() -> None:
    print("\n[1/6] Smoke test")
    smoke_test()

    print("\n[2/6] Normal / peak / light load flow")
    print(run_all_load_flow().to_string(index=False))

    print("\n[3/6] Fault study + breaker duty")
    print(run_fault_study().to_string(index=False))

    print("\n[4/6] Protection coordination")
    prot = run_protection_coordination()
    print(prot.to_string(index=False))
    if (prot["status"] != "PASS").any():
        print("WARNING: at least one CTI failed. Review outputs/protection/coordination_intervals.csv before claiming final coordination.")

    print("\n[5/6] N-1 + BESS")
    print(run_n1().to_string(index=False))
    print(run_bess_assessment().to_string(index=False))

    print("\n[6/6] SCADA / FLISR")
    scada = run_fault_scenario()
    print("\n".join(scada["events"]))
    out = Path(__file__).resolve().parents[1] / "outputs" / "scada"
    out.mkdir(parents=True, exist_ok=True)
    (out / "scada_result.json").write_text(json.dumps(scada, indent=2), encoding="utf-8")

    print("\nDONE. Results are in the project outputs/ folder.")


if __name__ == "__main__":
    main()
