"""Streamlit front end.  Run:  streamlit run app.py"""
from dataclasses import asdict

import streamlit as st

from hinttutor import assignment, config, pipeline, runner
from hinttutor.diagnose import number_code

st.set_page_config(page_title="Hint Tutor", layout="wide")
st.title("Hint Tutor")
st.caption("Test-grounded hints for Python assignments. Local model through Ollama. No code leaves this machine.")

names = assignment.list_assignments()
with st.sidebar:
    name = st.selectbox("Assignment", names, format_func=lambda n: "%s (%s)" % (assignment.load(n).title, n))
    model = st.text_input("Ollama model", config.MODEL)
    ta_view = st.checkbox("Show under-the-hood panel (TA view)", value=True,
                          help="Contains the guard's match details, which reveal the fix. Turn off for students.")

asg = assignment.load(name)
if ta_view:
    left, right = st.columns([3, 2])
else:
    left, right = st.container(), None

with left:
    with st.expander("Problem", expanded=True):
        st.markdown(asg.problem)
        st.caption("Function: `%s`  |  %d tests" % (asg.function, len(asg.tests)))
    code = st.text_area("Student code", value=asg.buggy_example or "", height=300, key="code_" + name)
    if st.button("Run tests and get hint", type="primary"):
        with st.spinner("Running tests and asking %s ..." % model):
            st.session_state["result"] = (name, code, pipeline.run(asg, code, model))

stored = st.session_state.get("result")
res = stored[2] if stored and stored[0] == name else None

if res:
    with left:
        if res.report and res.report.results:
            rows = []
            for r in res.report.results:
                shown = r.actual if r.kind in ("ok", "wrong") else r.error
                rows.append({"call": runner.call_repr(asg.function, r.args), "expected": repr(r.expected),
                             "result": repr(shown) if r.kind in ("ok", "wrong") else shown,
                             "status": "PASS" if r.passed else "FAIL"})
            st.dataframe(rows, hide_index=True)
            st.write("**%d / %d tests pass**" % (res.report.n_passed, len(res.report.results)))
        if res.status == "passed":
            st.success(res.message)
        elif res.status == "hint":
            st.info("**Hint:** " + res.message)
        else:
            st.error(res.message)

    if right is not None:
        with right:
            st.subheader("Under the hood")
            st.write("Model: `%s`  |  total: %.1fs" % (res.model, res.total_seconds))
            if res.diagnosis:
                d = asdict(res.diagnosis)
                d.pop("raw", None)
                st.markdown("**Diagnosis (step 1)**")
                st.json(d)
            if res.hint:
                st.markdown("**Guard (step 2), one row per attempt**")
                st.dataframe([{"attempt": i, "verdict": "accepted" if a.ok else "rejected",
                               "reasons": ", ".join(a.reasons), "matched": ", ".join(a.detail),
                               "seconds": round(a.seconds, 1), "text": a.text}
                              for i, a in enumerate(res.hint.attempts, start=1)], hide_index=True)
                if res.hint.used_fallback:
                    st.warning("All attempts rejected. Fixed template used.")
            if res.calls:
                st.markdown("**Model calls**")
                st.dataframe([{"call": c.name, "seconds": round(c.seconds, 2), "ok": c.ok} for c in res.calls], hide_index=True)
            st.markdown("**Numbered code sent to the model**")
            st.code(number_code(stored[1]), language="text")
