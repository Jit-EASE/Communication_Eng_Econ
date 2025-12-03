# app.py — DRAG-TO-CURL VERSION (Apple Books Style)

import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

from tabs import (
    tab1_control,
    tab2_cycle,
    tab3_network,
    tab4_queue,
    tab5_rl,
)

# -------------------------------
# TAB MAP
# -------------------------------

TAB_MAP = {
    "Control System (v0.1)": tab1_control,
    "Cycle Analysis (v0.2)": tab2_cycle,
    "Network View (v0.3)": tab3_network,
    "Queueing / Congestion (v0.4)": tab4_queue,
    "Policy Tuner (v0.5)": tab5_rl,
}

TAB_COLORS = {
    "Control System (v0.1)": "#00eaff",
    "Cycle Analysis (v0.2)": "#ff47e8",
    "Network View (v0.3)": "#5bff62",
    "Queueing / Congestion (v0.4)": "#ffd447",
    "Policy Tuner (v0.5)": "#ff6c47",
}


# -------------------------------
# OPENAI NEW CLIENT
# -------------------------------

def get_openai_client():
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        api_key = None

    if api_key:
        return OpenAI(api_key=api_key)
    return OpenAI()


# -------------------------------
# PLOTLY THEME
# -------------------------------

def make_plotly_template(accent):
    pio.templates["spectre"] = go.layout.Template(
        layout=dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0f3ff"),
            hoverlabel=dict(
                bgcolor="rgba(10,10,20,0.80)",
                bordercolor=accent,
                font=dict(color="white")
            ),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.10)",
                zeroline=False,
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikecolor=accent,
                spikethickness=1.5,
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.10)",
                zeroline=False,
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikecolor=accent,
                spikethickness=1.5,
            ),
        )
    )
    pio.templates.default = "spectre"


def get_figure(accent):
    make_plotly_template(accent)
    return go.Figure()


# -------------------------------
# DATA HUB CORE
# -------------------------------

def init_data_ctx():
    if "data_ctx" not in st.session_state:
        st.session_state["data_ctx"] = {
            "df": None,
            "name": None,
            "numeric_cols": [],
            "datetime_cols": [],
            "n_rows": 0,
            "n_cols": 0,
        }


def load_uploaded_file(uploaded):
    if uploaded is None:
        return None
    name = uploaded.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(uploaded)
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(uploaded)
        elif name.endswith(".json"):
            return pd.read_json(uploaded)
        else:
            st.error("Unsupported format (use CSV, Excel, or JSON).")
            return None
    except Exception as e:
        st.error(f"File error: {e}")
        return None


def build_data_ctx(df, name):
    if df is None:
        return {
            "df": None,
            "name": None,
            "numeric_cols": [],
            "datetime_cols": [],
            "n_rows": 0,
            "n_cols": 0,
        }

    return {
        "df": df,
        "name": name,
        "numeric_cols": df.select_dtypes(include=["number"]).columns.tolist(),
        "datetime_cols": df.select_dtypes(include=["datetime64[ns]"]).columns.tolist(),
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
    }


def render_data_hub(accent):
    init_data_ctx()
    data_ctx = st.session_state["data_ctx"]

    st.markdown("### Data Hub — Global Dataset for All Modules")
    st.write(
        "Upload any real dataset (CSV, Excel, JSON). All modules can use it "
        "for overlays, cycle analysis, network construction, queue plots, and parameter tuning reference."
    )

    uploaded = st.file_uploader("Upload dataset", type=["csv","xlsx","xls","json"])

    if uploaded:
        df = load_uploaded_file(uploaded)
        if df is not None:
            st.session_state["data_ctx"] = build_data_ctx(df, uploaded.name)
            data_ctx = st.session_state["data_ctx"]

    df = data_ctx["df"]

    if df is not None:
        st.success(f"Loaded dataset: **{data_ctx['name']}**")
        st.dataframe(df.head(10), use_container_width=True)
        st.markdown("**Numeric columns detected:**")
        st.write(", ".join(data_ctx["numeric_cols"]) or "_None_")
    else:
        st.info("No dataset loaded. Modules will use synthetic simulations.")

    st.markdown("---")


# -------------------------------
# APPLE BOOKS STYLE PAGE CURL CSS
# -------------------------------

def inject_css(accent):
    st.markdown(
        f"""
        <style>

        body {{
            background: radial-gradient(circle at top, #14141f 0%, #08080d 40%, #020205 100%) !important;
        }}

        .block-container {{
            padding-top: 0.2rem !important;
        }}

        :root {{
            --accent: {accent};
            --curl-ry: 0deg;
            --curl-skew: 0deg;
            --curl-tx: 0px;
            --curl-scale: 1;
        }}

        .book-shell {{
            position: relative;
            width: 100%;
            max-width: 1100px;
            margin: 0.5rem auto 1.5rem auto;
            perspective: 1800px;
        }}

        .page {{
            position: absolute;
            inset: 0;
            border-radius: 18px;
            background: rgba(8,8,14,0.82);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 20px 40px rgba(0,0,0,0.55), 0 0 30px var(--accent);
            transform-origin: left center;
            transition: transform 0.18s ease-out,
                        box-shadow 0.18s ease-out,
                        filter 0.18s ease-out,
                        opacity 0.3s ease-out;
        }}

        .stack1 {{ z-index: 90; opacity: 0.85; transform: translateY(10px) scale(0.99) rotateY(-2deg); }}
        .stack2 {{ z-index: 80; opacity: 0.70; transform: translateY(20px) scale(0.98) rotateY(-4deg); }}
        .stack3 {{ z-index: 70; opacity: 0.55; transform: translateY(30px) scale(0.97) rotateY(-6deg); }}
        .stack4 {{ z-index: 60; opacity: 0.40; transform: translateY(40px) scale(0.96) rotateY(-8deg); }}

        .active-page {{
            z-index: 100;
            opacity: 1;
            transform:
                perspective(1600px)
                translateX(var(--curl-tx))
                rotateY(var(--curl-ry))
                skewY(var(--curl-skew))
                scale(var(--curl-scale));
            background: linear-gradient(
                90deg,
                rgba(255,255,255,0.04) 0%,
                rgba(255,255,255,0.10) 12%,
                rgba(0,0,0,0.20) 55%,
                rgba(0,0,0,0.50) 100%
            );
        }}

        .flip-in {{
            animation: pageCurlEntry 0.9s cubic-bezier(0.25,0.8,0.25,1);
        }}

        @keyframes pageCurlEntry {{
            0% {{
                transform: perspective(1600px) translateX(-40px) rotateY(-70deg) skewY(-10deg) scale(0.96);
                opacity: 0;
                filter: brightness(0.7);
            }}
            50% {{
                transform: perspective(1600px) translateX(-18px) rotateY(-25deg) skewY(-6deg) scale(1.03);
                opacity: 0.9;
            }}
            100% {{
                transform: perspective(1600px) translateX(0) rotateY(0) skewY(0) scale(1);
                opacity: 1;
            }}
        }}

        .page-inner {{
            height: 76vh;
            padding: 0.8rem 1.2rem;
            overflow-y: auto;
        }}

        .page-header {{
            font-size: 1.2rem;
            font-weight: 650;
            color: var(--accent);
            border-right: 2px solid var(--accent);
            width: 0;
            overflow: hidden;
            white-space: nowrap;
            animation: typing 2.4s steps(60,end) forwards, caret 0.7s step-end infinite;
        }}

        @keyframes typing {{ from {{width:0;}} to {{width:100%;}} }}
        @keyframes caret {{ 50% {{border-color:transparent;}} }}

        .page-divider {{
            height: 2px;
            background: linear-gradient(90deg, rgba(255,255,255,0), var(--accent), rgba(255,255,255,0));
            margin-bottom: 0.8rem;
        }}

        .agent-box {{
            position: fixed;
            right: 12px;
            top: 80px;
            width: 260px;
            background: rgba(18,18,26,0.92);
            border: 1px solid var(--accent);
            box-shadow: 0 0 25px var(--accent);
            padding: 0.8rem;
            border-radius: 14px;
            z-index: 9999;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------
# DRAG-TO-CURL JAVASCRIPT
# -------------------------------

def inject_drag_curl_js():
    st.markdown(
        """
        <script>
        (function() {
            function bindCurl() {
                const page = document.querySelector('.page.active-page');
                if (!page) return;
                if (page.dataset.curlBound === "1") return;
                page.dataset.curlBound = "1";

                let dragging = false;
                let startX = 0;
                let width = page.offsetWidth || 800;

                function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

                page.addEventListener('pointerdown', function(e) {
                    dragging = true;
                    startX = e.clientX;
                    width = page.offsetWidth || 800;
                    try { page.setPointerCapture(e.pointerId); } catch(_) {}
                    page.style.transition = "none";
                });

                page.addEventListener('pointermove', function(e) {
                    if (!dragging) return;
                    const dx = e.clientX - startX;
                    const ratio = clamp(dx / width, -1.0, 0.35);

                    const angle = ratio * -80;
                    const skew  = ratio * -12;
                    const tx    = ratio * -30;
                    const scale = 1 + Math.abs(ratio) * 0.04;

                    page.style.setProperty('--curl-ry', angle + 'deg');
                    page.style.setProperty('--curl-skew', skew + 'deg');
                    page.style.setProperty('--curl-tx', tx + 'px');
                    page.style.setProperty('--curl-scale', scale);
                });

                function release(e) {
                    if (!dragging) return;
                    dragging = false;
                    try { page.releasePointerCapture(e.pointerId); } catch(_) {}

                    page.style.transition =
                        "transform 0.22s ease-out, box-shadow 0.22s ease-out, filter 0.22s ease-out";

                    page.style.setProperty('--curl-ry', '0deg');
                    page.style.setProperty('--curl-skew', '0deg');
                    page.style.setProperty('--curl-tx', '0px');
                    page.style.setProperty('--curl-scale', '1');
                }

                page.addEventListener('pointerup', release);
                page.addEventListener('pointercancel', release);
                page.addEventListener('pointerleave', release);
            }

            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(bindCurl, 200);
            });

            setTimeout(bindCurl, 600);
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------
# MAIN APP
# -------------------------------

def main():
    st.set_page_config(page_title="CDEPM – Quantum Policy Codex", layout="wide")

    st.sidebar.title("CDEPM Orchestrator")
    tab_name = st.sidebar.radio("Module", list(TAB_MAP.keys()))
    accent = TAB_COLORS[tab_name]

    inject_css(accent)
    inject_drag_curl_js()
    init_data_ctx()

    agent_on = st.sidebar.checkbox("Enable AI Margin Commentator")

    st.markdown('<div class="book-shell">', unsafe_allow_html=True)

    st.markdown('<div class="page stack4"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack3"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack2"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack1"></div>', unsafe_allow_html=True)

    st.markdown('<div class="page active-page flip-in"><div class="page-inner">', unsafe_allow_html=True)

    st.markdown(f'<div class="page-header">{tab_name}</div><div class="page-divider"></div>', unsafe_allow_html=True)

    render_data_hub(accent)

    module = TAB_MAP[tab_name]
    module.render(accent, get_figure, st.session_state["data_ctx"])

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if agent_on:
        client = get_openai_client()
        st.markdown('<div class="agent-box">', unsafe_allow_html=True)
        st.markdown('<div class="agent-title">Spectre.AI – Margin Analyst</div>', unsafe_allow_html=True)

        query = st.text_area("Ask about this module:")
        if st.button("Explain") and query:
            try:
                r = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role":"system","content":f"Explain {tab_name} in a rigorous, calm, strategic tone."},
                        {"role":"user","content":query},
                    ]
                )
                st.write(r.choices[0].message.content)
            except Exception as e:
                st.error(str(e))

        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
