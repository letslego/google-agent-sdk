from __future__ import annotations

import pandas as pd
import streamlit as st

from enterprise_rag.evals import run_eval_suite
from enterprise_rag.service import RAGService
from enterprise_rag.tracing import read_traces


st.set_page_config(page_title="Google Agent SDK RAG UI", layout="wide")
st.title("Google Agent SDK - Enterprise RAG UI")
st.caption("Showcasing RAG answers, execution traces, and evaluation runs.")


@st.cache_resource
def get_service() -> RAGService:
    return RAGService()


service = get_service()
tab_rag, tab_traces, tab_evals = st.tabs(["RAG", "Traces", "Evals"])

with tab_rag:
    st.subheader("Ask the RAG assistant")
    query = st.text_area(
        "Customer query",
        value="Acme says Claim API latency violates SLA. What should support do?",
        height=120,
    )
    col1, col2 = st.columns(2)
    customer_id = col1.text_input("Customer ID (optional)", value="C1001")
    top_k = col2.slider("Top K retrieval", min_value=1, max_value=10, value=5)

    if st.button("Run RAG Query", type="primary"):
        response = service.answer_query(
            query=query,
            customer_id=customer_id or None,
            top_k=top_k,
        )
        st.markdown("### Grounded Answer")
        st.write(response.answer)
        with st.expander("Retrieved Context"):
            st.text(response.context)
        with st.expander("Trace Metadata"):
            st.json(response.trace)

with tab_traces:
    st.subheader("Trace explorer")
    traces = read_traces(limit=200)
    if not traces:
        st.info("No traces yet. Run a query in the RAG tab first.")
    else:
        df = pd.DataFrame(
            [
                {
                    "trace_id": t.get("trace_id", ""),
                    "timestamp_utc": t.get("timestamp_utc", ""),
                    "query": t.get("query", ""),
                    "customer_id": t.get("customer_id", ""),
                    "selected_skill": t.get("selected_skill", ""),
                    "latency_ms": t.get("latency_ms", 0),
                }
                for t in traces
            ]
        )
        st.dataframe(df, use_container_width=True)
        selected_trace = st.selectbox(
            "Inspect trace details",
            options=[t.get("trace_id", "") for t in traces],
            index=0,
        )
        details = next((t for t in traces if t.get("trace_id") == selected_trace), None)
        if details:
            st.json(details)

with tab_evals:
    st.subheader("Evaluation suite")
    st.caption("Runs sample benchmark queries and scores keyword coverage from grounded answers.")
    if st.button("Run Evals"):
        results = run_eval_suite(service)
        if not results:
            st.warning("No eval cases found. Add cases to data/evals/eval_cases.json.")
        else:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            pass_rate = (df["passed"].sum() / len(df)) * 100
            avg_latency = df["latency_ms"].mean()
            c1, c2 = st.columns(2)
            c1.metric("Pass Rate", f"{pass_rate:.1f}%")
            c2.metric("Average Latency", f"{avg_latency:.1f} ms")

