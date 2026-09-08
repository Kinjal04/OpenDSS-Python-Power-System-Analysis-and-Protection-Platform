"""Operating scenarios and contingency topology changes."""
from __future__ import annotations

from opendssdirect import dss

from dss_utils import close_element, compile_master, open_element, solve_snap


def _cmd(command: str) -> None:
    dss.Command(command)


def apply_operating_case(case: str) -> None:
    compile_master()
    case = case.lower()

    if case == "normal":
        _cmd("Set LoadMult=1.00")
        _cmd("Edit Load.RAIL kW=4000 PF=0.97")
        _cmd("Edit PVSystem.PV5MW Irradiance=1.00")
        _cmd("Edit Generator.GEN13 Enabled=Yes kW=20000")
        _cmd("Edit Storage.BESS State=Idling kW=0 kvar=0")
    elif case == "peak":
        _cmd("Set LoadMult=1.20")
        _cmd("Edit Load.RAIL kW=8000 PF=0.97")
        _cmd("Edit PVSystem.PV5MW Irradiance=0.60")
        _cmd("Edit Generator.GEN13 Enabled=Yes kW=20000")
        _cmd("Edit Storage.BESS State=Idling kW=0 kvar=0")
    elif case == "light":
        _cmd("Set LoadMult=0.60")
        _cmd("Edit Load.RAIL kW=1000 PF=0.97")
        _cmd("Edit PVSystem.PV5MW Irradiance=1.00")
        _cmd("Edit Generator.GEN13 Enabled=Yes kW=20000")
        _cmd("Edit Storage.BESS State=Idling kW=0 kvar=0")
    elif case == "peak_bess_charge":
        _cmd("Set LoadMult=1.20")
        _cmd("Edit Load.RAIL kW=8000 PF=0.97")
        _cmd("Edit PVSystem.PV5MW Irradiance=0.60")
        _cmd("Edit Generator.GEN13 Enabled=Yes kW=20000")
        _cmd("Edit Storage.BESS State=Charging kW=-50000 kvar=0")
    elif case == "light_bess_discharge":
        _cmd("Set LoadMult=0.60")
        _cmd("Edit Load.RAIL kW=1000 PF=0.97")
        _cmd("Edit PVSystem.PV5MW Irradiance=1.00")
        _cmd("Edit Generator.GEN13 Enabled=Yes kW=20000")
        _cmd("Edit Storage.BESS State=Discharging kW=50000 kvar=0")
    else:
        raise ValueError(f"Unknown operating case: {case}")

    _cmd("Edit Transformer.UAT Enabled=Yes")
    _cmd("Edit Transformer.SST Enabled=No")
    open_element("Line.TIE_AB")
    solve_snap()


def apply_n1_case(case: str) -> None:
    compile_master()
    case = case.lower()

    if case == "line230a":
        open_element("Line.LINE230A")
    elif case == "line230b":
        open_element("Line.LINE230B")
    elif case == "t2_transfer":
        open_element("Transformer.T2")
        open_element("Line.BRK_A")
        close_element("Line.TIE_AB")
    elif case == "t3_transfer":
        open_element("Transformer.T3")
        open_element("Line.BRK_B")
        close_element("Line.TIE_AB")
    elif case == "generator":
        _cmd("Edit Generator.GEN13 Enabled=No")
        open_element("Transformer.GSU")
        _cmd("Edit Transformer.UAT Enabled=No")
        _cmd("Edit Transformer.SST Enabled=Yes")
    elif case == "feeder_a":
        open_element("Line.BRK_A")
        close_element("Line.TIE_AB")
    else:
        raise ValueError(f"Unknown N-1 case: {case}")

    solve_snap()
