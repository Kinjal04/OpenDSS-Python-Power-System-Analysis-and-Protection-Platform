"""Installation/model smoke test. Run this before any engineering study."""
from opendssdirect import dss

from config import MASTER_DSS
from dss_utils import compile_master, solve_snap

REQUIRED = [
    "Line.LINE230A", "Line.LINE230B", "Transformer.T1", "Transformer.T2", "Transformer.T3",
    "Line.BRK_A", "Line.BRK_B", "Line.A03", "Line.A05", "Line.TIE_AB",
    "Generator.GEN13", "PVSystem.PV5MW", "Transformer.TBESS", "Storage.BESS",
    "Transformer.UAT", "Transformer.SST", "Load.RAIL",
]


def main() -> None:
    print(f"Master file: {MASTER_DSS}")
    compile_master()
    solve_snap()
    print(f"Circuit: {dss.Circuit.Name()}")
    print(f"Buses: {len(dss.Circuit.AllBusNames())}")
    print(f"Elements: {dss.Circuit.NumCktElements()}")

    missing = [name for name in REQUIRED if dss.Circuit.SetActiveElement(name) <= 0]
    if missing:
        raise RuntimeError("Missing required elements: " + ", ".join(missing))
    if not dss.Solution.Converged():
        raise RuntimeError("Base model did not converge.")

    print("SMOKE TEST PASS: model compiled, converged, and required elements were found.")


if __name__ == "__main__":
    main()
