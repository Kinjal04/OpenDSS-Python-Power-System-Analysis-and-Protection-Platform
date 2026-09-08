"""SCADA-style fault detection, breaker trip, isolation and feeder restoration."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from opendssdirect import dss

from config import PROTECTION, VOLTAGE_MIN_PU
from dss_utils import (
    bus_phase_pu,
    close_element,
    compile_master,
    max_phase_current_a,
    open_element,
    solve_snap,
)


@dataclass
class ScadaResult:
    normal_current_a: float
    fault_current_a: float
    relay_pickup_a: float
    relay_status: str
    breaker_status: str
    sectionalizer_status: str
    tie_status: str
    upstream_voltage_pu: float
    downstream_voltage_pu: float
    restoration_status: str
    events: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def reset_system() -> None:
    compile_master()
    solve_snap()


def run_fault_scenario() -> dict:
    """Simulate a permanent fault on feeder section A04 and FLISR restoration.

    Sequence:
      1. detect fault from BRK_A current
      2. trip BRK_A
      3. isolate Line.A04 (faulted section proxy)
      4. clear the isolated fault object
      5. reclose BRK_A to restore A01-A03
      6. close the A06-B06 tie to backfeed A04-A06 from Feeder B
    """
    compile_master()
    dss.Command("Set ControlMode=Off")
    solve_snap()
    normal_current = max_phase_current_a("Line.BRK_A")
    pickup = PROTECTION["relay_a_phase"]["pickup"]

    # Create a temporary bolted 3-phase fault at the downstream end of the
    # section being treated as faulted. It is disabled after the section opens.
    dss.Command("New Fault.SCADA_A04 Phases=3 Bus1=A04 R=0.001 Enabled=Yes")
    solve_snap()
    fault_current = max_phase_current_a("Line.BRK_A")
    relay_picked = fault_current >= pickup

    events = [f"00.000 s  FAULT DETECTED on Feeder A section A04 ({fault_current:.0f} A at BRK_A)"]
    if not relay_picked:
        return ScadaResult(
            normal_current, fault_current, pickup, "NO PICKUP", "CLOSED", "CLOSED", "OPEN",
            min(bus_phase_pu("A03"), default=0.0), min(bus_phase_pu("A06"), default=0.0),
            "NO TRIP", events,
        ).to_dict()

    events.append("00.020 s  FEEDER RELAY 50/51 PICKUP")
    open_element("Line.BRK_A")
    events.append("00.120 s  CB-A OPEN / FEEDER A TRIPPED")

    open_element("Line.A04")
    events.append("01.000 s  LINE A04 ISOLATED")
    dss.Command("Edit Fault.SCADA_A04 Enabled=No")

    close_element("Line.BRK_A")
    events.append("01.200 s  CB-A RECLOSED; A01-A03 RESTORED")
    close_element("Line.TIE_AB")
    events.append("02.000 s  CB-TIE CLOSED; A04-A06 BACKFED FROM FEEDER B")
    solve_snap()

    up_v = min(bus_phase_pu("A03"), default=0.0)
    down_v = min(bus_phase_pu("A06"), default=0.0)
    restored = up_v >= VOLTAGE_MIN_PU and down_v >= VOLTAGE_MIN_PU
    events.append(
        f"02.100 s  RESTORATION CHECK: A03={up_v:.3f} pu, A06={down_v:.3f} pu -> "
        + ("RESTORED" if restored else "CHECK FAILED")
    )

    return ScadaResult(
        normal_current_a=normal_current,
        fault_current_a=fault_current,
        relay_pickup_a=pickup,
        relay_status="PICKUP/TRIP",
        breaker_status="RECLOSED",
        sectionalizer_status="A04 OPEN",
        tie_status="CLOSED",
        upstream_voltage_pu=up_v,
        downstream_voltage_pu=down_v,
        restoration_status="RESTORED" if restored else "FAILED",
        events=events,
    ).to_dict()


if __name__ == "__main__":
    result = run_fault_scenario()
    for event in result["events"]:
        print(event)
