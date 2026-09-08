"""Protection coordination: TCCs, operating times and CTIs."""
from __future__ import annotations

import math

import matplotlib.pyplot as plt
import pandas as pd
from opendssdirect import dss

from config import CTI_MIN_S, PROTECTION, TCC_CURVES
from dss_utils import (
    compile_master,
    ensure_output_dir,
    max_phase_current_a,
    residual_current_a,
    solve_snap,
)


def curve_time(curve_name: str, multiple: float) -> float:
    curve = TCC_CURVES[curve_name]
    xs, ys = curve["m"], curve["t"]
    if multiple < xs[0]:
        return math.inf
    if multiple == xs[0]:
        return ys[0]

    # Log-log interpolation; extrapolate using the last segment at high current.
    for i in range(len(xs) - 1):
        if xs[i] <= multiple <= xs[i + 1]:
            x1, x2, y1, y2 = xs[i], xs[i + 1], ys[i], ys[i + 1]
            break
    else:
        x1, x2, y1, y2 = xs[-2], xs[-1], ys[-2], ys[-1]

    lx = math.log(multiple)
    ly = math.log(y1) + (lx - math.log(x1)) * (math.log(y2) - math.log(y1)) / (math.log(x2) - math.log(x1))
    return math.exp(ly)


def device_time(setting_name: str, current_a: float) -> float:
    s = PROTECTION[setting_name]
    if current_a < s["pickup"]:
        return math.inf
    inst = s.get("instantaneous")
    fixed = s.get("fixed_delay", 0.0)
    if inst is not None and current_a >= inst:
        return fixed
    base = curve_time(s["curve"], current_a / s["pickup"])
    if not math.isfinite(base):
        return math.inf
    return s.get("td", 1.0) * base + fixed


def _fault_currents(fault_command: str) -> dict:
    compile_master()
    dss.Command("Set ControlMode=Off")
    dss.Command(fault_command)
    solve_snap()
    return {
        "fuse_phase": max_phase_current_a("Line.A05"),
        "recloser_phase": max_phase_current_a("Line.A03"),
        "relay_phase": max_phase_current_a("Line.BRK_A"),
        "main_phase": max_phase_current_a("Transformer.T1"),
        "recloser_ground": residual_current_a("Line.A03"),
        "relay_ground": residual_current_a("Line.BRK_A"),
        "main_ground": residual_current_a("Transformer.T1"),
    }


def _plot_tcc(path) -> None:
    currents = [10 ** (2.0 + i * 0.01) for i in range(220)]  # 100 A to ~15.8 kA
    series = [
        ("Fuse A", "fuse_a"),
        ("Recloser A fast", "rec_a_phase_fast"),
        ("Recloser A delayed", "rec_a_phase_slow"),
        ("Feeder A relay", "relay_a_phase"),
    ]
    fig, ax = plt.subplots(figsize=(8, 6))
    for label, setting in series:
        y = [device_time(setting, i) for i in currents]
        x2, y2 = zip(*[(x, t) for x, t in zip(currents, y) if math.isfinite(t)])
        ax.loglog(x2, y2, label=label)
    ax.set_xlabel("Primary current (A)")
    ax.set_ylabel("Operating / clearing time (s)")
    ax.set_title("Feeder A Protection TCC")
    ax.grid(True, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_protection_coordination() -> pd.DataFrame:
    # Permanent 3-phase and SLG faults near the feeder-A end.
    ph = _fault_currents("Edit Fault.FLT_A06_3PH Enabled=Yes")
    gr = _fault_currents("Edit Fault.FLT_A06_SLG Enabled=Yes")

    rows = []
    # 3-phase permanent fault: fuse should clear before delayed recloser,
    # delayed recloser before feeder relay, feeder relay before 230-kV backup.
    t_fuse = device_time("fuse_a", ph["fuse_phase"])
    t_rec_slow = device_time("rec_a_phase_slow", ph["recloser_phase"])
    t_relay = device_time("relay_a_phase", ph["relay_phase"])
    t_main = device_time("relay_230_phase", ph["main_phase"])

    chain = [
        ("3PH", "Fuse A", t_fuse, "Recloser A delayed", t_rec_slow),
        ("3PH", "Recloser A delayed", t_rec_slow, "Feeder A relay", t_relay),
        ("3PH", "Feeder A relay", t_relay, "230-kV relay", t_main),
    ]

    t_rec_g = device_time("rec_a_ground_slow", gr["recloser_ground"])
    t_relay_g = device_time("relay_a_ground", gr["relay_ground"])
    t_main_g = device_time("relay_230_ground", gr["main_ground"])
    chain += [
        ("SLG", "Recloser A ground delayed", t_rec_g, "Feeder A ground relay", t_relay_g),
        ("SLG", "Feeder A ground relay", t_relay_g, "230-kV ground relay", t_main_g),
    ]

    for fault, primary, tp, backup, tb in chain:
        cti = tb - tp if math.isfinite(tp) and math.isfinite(tb) else math.nan
        rows.append({
            "fault": fault,
            "primary": primary,
            "primary_time_s": tp,
            "backup": backup,
            "backup_time_s": tb,
            "cti_s": cti,
            "minimum_cti_s": CTI_MIN_S,
            "status": "PASS" if math.isfinite(cti) and cti >= CTI_MIN_S else "FAIL",
        })

    df = pd.DataFrame(rows)
    out = ensure_output_dir("protection")
    df.to_csv(out / "coordination_intervals.csv", index=False)

    current_rows = [
        {"fault": "3PH", **ph},
        {"fault": "SLG", **gr},
    ]
    pd.DataFrame(current_rows).to_csv(out / "device_fault_currents.csv", index=False)
    _plot_tcc(out / "feeder_A_TCC.png")
    return df


if __name__ == "__main__":
    print(run_protection_coordination().to_string(index=False))
