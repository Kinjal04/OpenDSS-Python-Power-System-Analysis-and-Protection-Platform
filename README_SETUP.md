# Integrated Power System Analysis, Protection & Operations Platform

## Folder layout

- `DSS/` - OpenDSS electrical model and scenario files
- `Python/` - study automation and SCADA logic
- `outputs/` - generated CSV, PNG and JSON results
- `requirements.txt` - Python dependencies

## Recommended environment

Use Python 3.11 or 3.12 on Windows. OpenDSSDirect.py contains its own DSS engine, so the EPRI OpenDSS GUI is optional for this Python workflow.

## Install

From PowerShell in this project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run once for the current shell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Verify the model first

```powershell
cd Python
python smoke_test.py
```

You should see `SMOKE TEST PASS`.

## Run the full engineering project

```powershell
python run_all.py
```

This executes:

1. load-flow studies for normal, peak and light load
2. voltage and thermal limit checks
3. 3-phase, L-L and SLG fault calculations
4. breaker interrupting-duty checks
5. protection TCC/CTI calculations and TCC plot
6. six N-1 contingency cases
7. 50 MW BESS charging/discharging assessment
8. SCADA-style fault detection, isolation and feeder restoration

Results are written to `../outputs/`.

## Run individual studies

```powershell
python load_flow.py
python fault_study.py
python protection_coordination.py
python contingency_bess.py
python scada_logic.py
```

## Launch the SCADA dashboard

```powershell
streamlit run app.py
```

Your browser should open the local Streamlit application. Click **Simulate Feeder A Fault**.

## Important engineering rule

Do not claim a resume bullet is complete merely because the script exists. Run it, inspect the generated results, and make sure the expected PASS/CONSTRAINT behavior is technically sensible. In particular, inspect `outputs/protection/coordination_intervals.csv`; every coordination pair you claim as coordinated should meet the selected 0.20 s minimum CTI.


## OpenDSS convergence fix (September 2026)

The final DSS base case uses `Generator.GEN13 Model=1` (constant kW / fixed PF) and `Set Algorithm=Newton`. This avoids unnecessary P-V generator iteration in the base snapshot while retaining `Xd`, `Xdp`, and `Xdpp` for fault studies. Compile only `DSS/Master.dss`; all other DSS files are redirected automatically. A successful compile should report `Status = Solved`.
