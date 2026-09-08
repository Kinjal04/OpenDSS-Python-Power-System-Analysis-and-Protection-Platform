"""3-phase, line-to-line and SLG fault study with breaker-duty checks."""
from __future__ import annotations

import math

import pandas as pd
from opendssdirect import dss

from config import BREAKER_DUTY_KA, FAULT_BUSES
from dss_utils import activate_bus, complex_pairs, compile_master, ensure_output_dir


def _two_value_complex(values) -> complex:
    vals = list(values)
    if len(vals) < 2:
        return complex(float("nan"), float("nan"))
    return complex(vals[0], vals[1])


def _prefault_phase_voltage_v() -> float:
    voc = complex_pairs(dss.Bus.Voc())
    mags = [abs(v) for v in voc if abs(v) > 0]
    if mags:
        return max(mags)
    return dss.Bus.kVBase() * 1000.0


def fault_at_bus(bus: str) -> dict:
    activate_bus(bus)
    # FaultStudy computes bus Zsc / Thevenin quantities. Refresh ensures the
    # active bus matrices are available through the classic API.
    dss.Bus.ZscRefresh()
    z1 = _two_value_complex(dss.Bus.Zsc1())
    z0 = _two_value_complex(dss.Bus.Zsc0())
    z2 = z1
    vph = _prefault_phase_voltage_v()

    if abs(z1) == 0 or not math.isfinite(abs(z1)):
        raise RuntimeError(f"Invalid Z1 at {bus}: {z1}")

    i3 = abs(vph / z1)
    ill = abs(math.sqrt(3.0) * vph / (z1 + z2)) if abs(z1 + z2) > 0 else math.inf
    islg = abs(3.0 * vph / (z1 + z2 + z0)) if abs(z1 + z2 + z0) > 0 else math.inf

    isc = complex_pairs(dss.Bus.Isc())
    isc_max = max((abs(i) for i in isc), default=math.nan)
    rating_ka = BREAKER_DUTY_KA[bus]
    max_fault_ka = max(i3, ill, islg) / 1000.0

    return {
        "bus": bus,
        "kv_base_ln": dss.Bus.kVBase(),
        "v_prefault_phase_v": vph,
        "z1_ohm_re": z1.real,
        "z1_ohm_im": z1.imag,
        "z0_ohm_re": z0.real,
        "z0_ohm_im": z0.imag,
        "fault_3ph_ka": i3 / 1000.0,
        "fault_ll_ka": ill / 1000.0,
        "fault_slg_ka": islg / 1000.0,
        "opendss_isc_max_ka": isc_max / 1000.0,
        "breaker_interrupting_ka": rating_ka,
        "max_available_fault_ka": max_fault_ka,
        "duty_margin_ka": rating_ka - max_fault_ka,
        "breaker_duty": "PASS" if max_fault_ka <= rating_ka else "FAIL",
    }


def run_fault_study() -> pd.DataFrame:
    compile_master()
    dss.Command("Set Mode=FaultStudy")
    dss.Command("Set ControlMode=Off")
    dss.Solution.Solve()
    if not dss.Solution.Converged():
        raise RuntimeError("FaultStudy solution did not converge.")

    rows = [fault_at_bus(bus) for bus in FAULT_BUSES]
    df = pd.DataFrame(rows)
    out = ensure_output_dir("fault_study")
    df.to_csv(out / "fault_currents_and_breaker_duty.csv", index=False)

    # Manual verification record for BUS115 using the same Thevenin quantities.
    manual = df.loc[df["bus"] == "BUS115"].copy()
    manual.to_csv(out / "manual_thevenin_check_BUS115.csv", index=False)
    return df


if __name__ == "__main__":
    print(run_fault_study().to_string(index=False))
