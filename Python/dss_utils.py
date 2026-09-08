"""Small, reusable OpenDSSDirect helpers."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from opendssdirect import dss

from config import MASTER_DSS, OUTPUT_DIR, THERMAL_LINES, TRANSFORMER_KVA


def ensure_output_dir(*parts: str) -> Path:
    path = OUTPUT_DIR.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def compile_master() -> None:
    if not MASTER_DSS.exists():
        raise FileNotFoundError(f"Master.dss not found: {MASTER_DSS}")
    dss.Command(f'Compile "{MASTER_DSS}"')
    if not dss.Circuit.Name():
        raise RuntimeError("OpenDSS did not create the circuit after Compile.")


def solve_snap() -> None:
    dss.Command("Set Mode=Snap")
    dss.Command("Set ControlMode=Off")
    dss.Solution.Solve()
    if not dss.Solution.Converged():
        raise RuntimeError("OpenDSS power-flow solution did not converge.")


def activate_element(name: str) -> None:
    if dss.Circuit.SetActiveElement(name) <= 0:
        raise KeyError(f"OpenDSS element not found: {name}")


def activate_bus(name: str) -> None:
    if dss.Circuit.SetActiveBus(name) < 0:
        raise KeyError(f"OpenDSS bus not found: {name}")


def complex_pairs(values: Iterable[float]) -> list[complex]:
    vals = list(values)
    if len(vals) % 2:
        raise ValueError("Expected a flat [real, imag, ...] complex array.")
    return [complex(vals[i], vals[i + 1]) for i in range(0, len(vals), 2)]


def bus_phase_pu(bus_name: str) -> list[float]:
    activate_bus(bus_name)
    mag_ang = list(dss.Bus.puVmagAngle())
    mags = mag_ang[0::2]
    return [float(v) for v in mags if math.isfinite(float(v)) and float(v) > 0]


def bus_voltage_rows() -> list[dict]:
    rows: list[dict] = []
    for bus in dss.Circuit.AllBusNames():
        vals = bus_phase_pu(bus)
        if not vals:
            continue
        rows.append({
            "bus": bus,
            "min_pu": min(vals),
            "max_pu": max(vals),
            "avg_pu": sum(vals) / len(vals),
        })
    return rows


def terminal_currents(element: str, terminal: int = 1) -> list[complex]:
    activate_element(element)
    currents = complex_pairs(dss.CktElement.Currents())
    ncond = dss.CktElement.NumConductors()
    start = (terminal - 1) * ncond
    return currents[start:start + ncond]


def terminal_phase_currents(element: str, terminal: int = 1) -> list[complex]:
    activate_element(element)
    nph = dss.CktElement.NumPhases()
    return terminal_currents(element, terminal)[:nph]


def max_phase_current_a(element: str, terminal: int = 1) -> float:
    vals = terminal_phase_currents(element, terminal)
    return max((abs(i) for i in vals), default=0.0)


def residual_current_a(element: str, terminal: int = 1) -> float:
    vals = terminal_phase_currents(element, terminal)
    return abs(sum(vals, 0j))


def terminal_complex_power_kva(element: str, terminal: int = 1) -> complex:
    activate_element(element)
    powers = complex_pairs(dss.CktElement.Powers())
    ncond = dss.CktElement.NumConductors()
    start = (terminal - 1) * ncond
    return sum(powers[start:start + ncond], 0j)


def line_loading_rows() -> list[dict]:
    rows: list[dict] = []
    for element in THERMAL_LINES:
        activate_element(element)
        if not dss.CktElement.Enabled():
            continue
        normal = float(dss.CktElement.NormalAmps())
        emergency = float(dss.CktElement.EmergAmps())
        current = max_phase_current_a(element)
        rows.append({
            "element": element,
            "current_a": current,
            "normal_a": normal,
            "emergency_a": emergency,
            "normal_loading_pct": 100.0 * current / normal if normal > 0 else math.nan,
            "emergency_loading_pct": 100.0 * current / emergency if emergency > 0 else math.nan,
        })
    return rows


def transformer_loading_rows() -> list[dict]:
    rows: list[dict] = []
    for element, rating_kva in TRANSFORMER_KVA.items():
        activate_element(element)
        if not dss.CktElement.Enabled():
            continue
        s = terminal_complex_power_kva(element, 1)
        rows.append({
            "element": element,
            "p_kw": s.real,
            "q_kvar": s.imag,
            "kva": abs(s),
            "rating_kva": rating_kva,
            "loading_pct": 100.0 * abs(s) / rating_kva,
        })
    return rows


def circuit_power_and_losses() -> dict:
    p = list(dss.Circuit.TotalPower())
    losses = list(dss.Circuit.Losses())  # W, var
    return {
        "source_p_kw_raw": p[0] if p else math.nan,
        "source_q_kvar_raw": p[1] if len(p) > 1 else math.nan,
        "loss_kw": (losses[0] / 1000.0) if losses else math.nan,
        "loss_kvar": (losses[1] / 1000.0) if len(losses) > 1 else math.nan,
    }


def is_open(element: str, terminal: int = 1) -> bool:
    activate_element(element)
    ncond = dss.CktElement.NumConductors()
    return all(bool(dss.CktElement.IsOpen(terminal, ph)) for ph in range(1, ncond + 1))


def open_element(element: str, terminal: int = 1) -> None:
    activate_element(element)
    dss.CktElement.Open(terminal, 0)


def close_element(element: str, terminal: int = 1) -> None:
    activate_element(element)
    dss.CktElement.Close(terminal, 0)
