"""Streamlit front end for the SCADA / restoration demonstration."""
import streamlit as st

from scada_logic import reset_system, run_fault_scenario

st.set_page_config(page_title="Power System Operations Simulator", layout="wide")
st.title("Power System Operations Simulator")
st.caption("27.6 kV Feeder A fault detection, isolation and service restoration")

if "result" not in st.session_state:
    st.session_state.result = None

c1, c2 = st.columns(2)
with c1:
    if st.button("Simulate Feeder A Fault", type="primary", use_container_width=True):
        try:
            st.session_state.result = run_fault_scenario()
        except Exception as exc:
            st.exception(exc)
with c2:
    if st.button("Reset System", use_container_width=True):
        try:
            reset_system()
            st.session_state.result = None
            st.success("System reset to normal state.")
        except Exception as exc:
            st.exception(exc)

r = st.session_state.result
if r is None:
    st.info("Run the fault scenario to view relay, breaker, sectionalizing and restoration logic.")
else:
    st.subheader("Measurements")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Normal BRK_A current", f"{r['normal_current_a']:.0f} A")
    m2.metric("Fault current", f"{r['fault_current_a']:.0f} A")
    m3.metric("Relay pickup", f"{r['relay_pickup_a']:.0f} A")
    m4.metric("Restored A06 voltage", f"{r['downstream_voltage_pu']:.3f} pu")

    st.subheader("Status")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Relay", r["relay_status"])
    s2.metric("CB-A", r["breaker_status"])
    s3.metric("Isolation", r["sectionalizer_status"])
    s4.metric("Tie", r["tie_status"])

    if r["restoration_status"] == "RESTORED":
        st.success("Healthy feeder sections successfully restored.")
    else:
        st.error("Restoration voltage criterion was not met.")

    st.subheader("Sequence of Events")
    for e in r["events"]:
        st.code(e, language=None)
