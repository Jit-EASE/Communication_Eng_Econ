# app.py — DRAG-TO-CURL VERSION with Data Hub, Cleaning, Inspector AI, Error Panel

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
# TAB MAP & COLORS
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
# LOGGING HELPERS
# -------------------------------

def init_log_ctx():
    if "logs" not in st.session_state:
        st.session_state["logs"] = []  # list of dicts: {"level":..., "msg":...}

def _log(level: str, msg: str):
    if "logs" not in st.session_state:
        st.session_state["logs"] = []
    st.session_state["logs"].append({"level": level.upper(), "msg": msg})

def log_info(msg: str):
    _log("INFO", msg)

def log_warn(msg: str):
    _log("WARN", msg)

def log_error(msg: str):
    _log("ERROR", msg)

def render_log_panel():
    logs = st.session_state.get("logs", [])
    if not logs:
        st.info("No log entries yet.")
        return
    for entry in logs[-200:]:  # show last 200
        prefix = "🟢" if entry["level"] == "INFO" else "🟡" if entry["level"] == "WARN" else "🔴"
        st.write(f"{prefix} **{entry['level']}** — {entry['msg']}")

# -------------------------------
# OPENAI CLIENT
# -------------------------------

def get_openai_client():
    api_key = None
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

def make_plotly_template(accent: str):
    pio.templates["spectre"] = go.layout.Template(
        layout=dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0f3ff"),
            hoverlabel=dict(
                bgcolor="rgba(10,10,20,0.80)",
                bordercolor=accent,
                font=dict(color="white"),
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

def get_figure(accent: str):
    make_plotly_template(accent)
    return go.Figure()

# -------------------------------
# DATA HUB / PROFILE / CLEANING
# -------------------------------

def init_data_ctx():
    if "data_ctx" not in st.session_state:
        st.session_state["data_ctx"] = {
            "df": None,
            "name": None,
            "numeric_cols": [],
            "datetime_cols": [],
            "categorical_cols": [],
            "n_rows": 0,
            "n_cols": 0,
            "profile": {},
        }

def load_uploaded_file(uploaded):
    """Safe loader for CSV, Excel, JSON with explicit engines."""
    if uploaded is None:
        return None, None
    name = uploaded.name
    lname = name.lower()
    try:
        if lname.endswith(".csv"):
            df = pd.read_csv(uploaded)
        elif lname.endswith(".xlsx") or lname.endswith(".xls"):
            df = pd.read_excel(uploaded, engine="openpyxl")
        elif lname.endswith(".json"):
            df = pd.read_json(uploaded)
        else:
            st.error("Unsupported file type. Please upload CSV, Excel, or JSON.")
            log_error(f"Unsupported file type attempted: {name}")
            return None, None
        log_info(f"Loaded dataset '{name}' with shape {df.shape}.")
        return df, name
    except Exception as e:
        msg = f"Error loading file '{name}': {e}"
        st.error(msg)
        log_error(msg)
        return None, None

def profile_dataset(df: pd.DataFrame):
    """Build automatic model-selection hints for tabs."""
    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    profile = {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "n_numeric": len(numeric_cols),
        "n_datetime": len(datetime_cols),
        "n_categorical": len(categorical_cols),
        "is_time_series": False,
        "time_col": None,
        "primary_numeric": None,
        "edge_source_col": None,
        "edge_target_col": None,
    }

    # Time-series heuristic
    if datetime_cols:
        profile["is_time_series"] = True
        profile["time_col"] = datetime_cols[0]
    else:
        # Try first column as time index if monotonic index
        if n_cols > 1 and df.iloc[:, 0].dropna().index.is_monotonic_increasing:
            profile["is_time_series"] = True
            profile["time_col"] = df.columns[0]

    # Primary numeric column: choose by largest variance
    if numeric_cols:
        var_series = df[numeric_cols].var(numeric_only=True).sort_values(ascending=False)
        if not var_series.empty:
            profile["primary_numeric"] = var_series.index[0]

    # Edge-like structure: first two categorical/string columns
    if len(categorical_cols) >= 2:
        profile["edge_source_col"] = categorical_cols[0]
        profile["edge_target_col"] = categorical_cols[1]

    return numeric_cols, datetime_cols, categorical_cols, profile

def rebuild_data_ctx(df: pd.DataFrame, name: str):
    numeric_cols, datetime_cols, categorical_cols, profile = profile_dataset(df)
    return {
        "df": df,
        "name": name,
        "numeric_cols": numeric_cols,
        "datetime_cols": datetime_cols,
        "categorical_cols": categorical_cols,
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "profile": profile,
    }

def apply_cleaning(df: pd.DataFrame, numeric_cols, cleaning_mode: str, scaling_mode: str, cols_to_scale):
    """Apply missing value handling + scaling on a copy."""
    clean_df = df.copy()

    # Missing value handling
    if cleaning_mode == "Drop rows with any NA":
        clean_df = clean_df.dropna()
        log_info("Applied cleaning: drop rows with any NA.")
    elif cleaning_mode == "Fill numeric NA with median":
        for c in numeric_cols:
            med = clean_df[c].median()
            clean_df[c] = clean_df[c].fillna(med)
        log_info("Applied cleaning: fill numeric NA with median.")
    elif cleaning_mode == "Fill numeric NA with mean":
        for c in numeric_cols:
            mean = clean_df[c].mean()
            clean_df[c] = clean_df[c].fillna(mean)
        log_info("Applied cleaning: fill numeric NA with mean.")
    elif cleaning_mode == "Fill numeric NA with 0":
        for c in numeric_cols:
            clean_df[c] = clean_df[c].fillna(0)
        log_info("Applied cleaning: fill numeric NA with 0.")

    # Scaling
    if scaling_mode != "None" and cols_to_scale:
        for c in cols_to_scale:
            if c not in numeric_cols:
                continue
            col = clean_df[c].astype(float)
            if scaling_mode == "Standardise (z-score)":
                mu = col.mean()
                sigma = col.std(ddof=0)
                if sigma != 0:
                    clean_df[c] = (col - mu) / sigma
            elif scaling_mode == "Min-Max [0,1]":
                mn = col.min()
                mx = col.max()
                if mx != mn:
                    clean_df[c] = (col - mn) / (mx - mn)
        log_info(f"Applied scaling '{scaling_mode}' to columns: {cols_to_scale}.")

    return clean_df

def render_dataset_inspector_ai(data_ctx, accent: str):
    df = data_ctx.get("df")
    if df is None:
        st.info("Dataset Inspector AI: Load a dataset first.")
        return

    client = None
    try:
        client = get_openai_client()
    except Exception as e:
        st.error("OpenAI client could not be initialised.")
        log_error(f"OpenAI init failed for dataset inspector: {e}")
        return

    profile = data_ctx.get("profile", {})
    numeric_cols = data_ctx.get("numeric_cols", [])
    datetime_cols = data_ctx.get("datetime_cols", [])
    categorical_cols = data_ctx.get("categorical_cols", [])

    # Lightweight summary (we do NOT send the full df)
    summary = {
        "name": data_ctx.get("name"),
        "shape": [data_ctx.get("n_rows"), data_ctx.get("n_cols")],
        "numeric_cols": numeric_cols,
        "datetime_cols": datetime_cols,
        "categorical_cols": categorical_cols,
        "profile": profile,
        "numeric_head": df[numeric_cols].head(5).to_dict(orient="list") if numeric_cols else {},
    }

    st.markdown("#### Dataset Inspector AI")
    q = st.text_area(
        "Ask about patterns, model choices, or what this dataset is good for:",
        height=90,
        key="dataset_ai_q",
    )

    if st.button("Ask Dataset AI", key="dataset_ai_btn"):
        if not q.strip():
            st.warning("Enter a question first.")
            return
        try:
            completion = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a data scientist helping to profile an economic/policy dataset. "
                            "You will be given a structured Python dict describing columns, types, "
                            "and a small numeric preview. Suggest suitable models for: "
                            "control systems, cycle analysis/FFT, network flows, queueing, and policy tuning."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"DATA SUMMARY: {summary}\n\nQUESTION: {q}",
                    },
                ],
            )
            answer = completion.choices[0].message.content
            st.write(answer)
            log_info("Dataset Inspector AI answered a query.")
        except Exception as e:
            msg = f"Dataset Inspector AI error: {e}"
            st.error(msg)
            log_error(msg)

def render_data_hub(accent: str):
    init_data_ctx()
    data_ctx = st.session_state["data_ctx"]

    st.markdown("### Data Hub — Global Dataset for All Modules")

    uploaded = st.file_uploader(
        "Upload dataset",
        type=["csv", "xlsx", "xls", "json"],
        key="global_uploader",
        help="This dataset will be available to all tabs (control, cycles, network, queue, tuner).",
    )

    if uploaded is not None:
        df, name = load_uploaded_file(uploaded)
        if df is not None:
            new_ctx = rebuild_data_ctx(df, name)
            st.session_state["data_ctx"] = new_ctx
            data_ctx = new_ctx

    df = data_ctx.get("df")

    if df is None:
        st.info("No dataset loaded. Modules will fall back to synthetic simulations.")
        st.markdown("---")
        return

    # Preview
    st.success(
        f"Loaded dataset: **{data_ctx['name']}** "
        f"({data_ctx['n_rows']} rows × {data_ctx['n_cols']} columns)"
    )
    st.dataframe(df.head(10), use_container_width=True)

    st.markdown(
        f"**Numeric columns:** {', '.join(data_ctx['numeric_cols']) or '_None_'}  \n"
        f"**Datetime columns:** {', '.join(data_ctx['datetime_cols']) or '_None_'}  \n"
        f"**Categorical columns:** {', '.join(data_ctx['categorical_cols']) or '_None_'}"
    )

    # Cleaning controls
    st.markdown("#### Dataset Cleaning & Transformations")
    cleaning_mode = st.selectbox(
        "Missing value strategy",
        [
            "None",
            "Drop rows with any NA",
            "Fill numeric NA with median",
            "Fill numeric NA with mean",
            "Fill numeric NA with 0",
        ],
        key="cleaning_mode",
    )

    scaling_mode = st.selectbox(
        "Scaling/normalisation",
        ["None", "Standardise (z-score)", "Min-Max [0,1]"],
        key="scaling_mode",
    )

    cols_to_scale = []
    if scaling_mode != "None" and data_ctx["numeric_cols"]:
        cols_to_scale = st.multiselect(
            "Columns to scale",
            data_ctx["numeric_cols"],
            default=[data_ctx["profile"].get("primary_numeric")]
            if data_ctx["profile"].get("primary_numeric") in data_ctx["numeric_cols"]
            else [],
            key="cols_to_scale",
        )

    if st.button("Apply cleaning/transformations", key="apply_cleaning_btn"):
        clean_df = apply_cleaning(
            df,
            data_ctx["numeric_cols"],
            cleaning_mode,
            scaling_mode,
            cols_to_scale,
        )
        st.session_state["data_ctx"] = rebuild_data_ctx(clean_df, data_ctx["name"])
        data_ctx = st.session_state["data_ctx"]
        df = data_ctx["df"]
        st.success("Cleaning and transformations applied. Dataset context updated.")
        log_info("Dataset cleaned and context rebuilt.")

    # Dataset inspector AI
    with st.expander("🔍 Dataset Inspector AI", expanded=False):
        render_dataset_inspector_ai(data_ctx, accent)

    st.markdown("---")

# -------------------------------
# BOOK CSS (Drag-to-Curl)
# -------------------------------

def inject_css(accent: str):
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
# DRAG-TO-CURL JS
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
# MAIN
# -------------------------------

def main():
    st.set_page_config(page_title="CDEPM – Quantum Policy Codex", layout="wide")

    init_log_ctx()

    st.sidebar.title("CDEPM Orchestrator")
    tab_name = st.sidebar.radio("Module", list(TAB_MAP.keys()))
    accent = TAB_COLORS[tab_name]

    show_logs = st.sidebar.checkbox("Show Error/Activity Log")

    inject_css(accent)
    inject_drag_curl_js()
    init_data_ctx()

    agent_on = st.sidebar.checkbox("Enable AI Margin Commentator")

    # Book shell
    st.markdown('<div class="book-shell">', unsafe_allow_html=True)
    st.markdown('<div class="page stack4"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack3"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack2"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack1"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page active-page flip-in"><div class="page-inner">', unsafe_allow_html=True)

    st.markdown(f'<div class="page-header">{tab_name}</div><div class="page-divider"></div>', unsafe_allow_html=True)

    # Data hub
    render_data_hub(accent)
    data_ctx = st.session_state["data_ctx"]

    # Render tab
    module = TAB_MAP[tab_name]
    try:
        module.render(accent, get_figure, data_ctx)
    except Exception as e:
        msg = f"Error in tab '{tab_name}': {e}"
        st.error(msg)
        log_error(msg)

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Margin AI for tab explanation
    if agent_on:
        client = None
        try:
            client = get_openai_client()
        except Exception as e:
            log_error(f"OpenAI init failed for margin AI: {e}")
            st.error("OpenAI client initialisation failed.")
        if client:
            st.markdown('<div class="agent-box">', unsafe_allow_html=True)
            st.markdown('<div class="agent-title">Spectre.AI – Margin Analyst</div>', unsafe_allow_html=True)
            query = st.text_area("Ask about this module:", key="module_ai_q")
            if st.button("Explain", key="module_ai_btn") and query.strip():
                try:
                    completion = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    f"You are explaining the module '{tab_name}' which mixes "
                                    "communication engineering and econometrics. Be clear, rigorous, "
                                    "and non-fluffy."
                                ),
                            },
                            {"role": "user", "content": query},
                        ],
                    )
                    answer = completion.choices[0].message.content
                    st.write(answer)
                    log_info("Margin Analyst AI answered a query.")
                except Exception as e:
                    msg = f"Margin AI error: {e}"
                    st.error(msg)
                    log_error(msg)
            st.markdown("</div>", unsafe_allow_html=True)

    # Error / activity log panel at bottom
    if show_logs:
        st.markdown("---")
        st.markdown("### System Log")
        render_log_panel()

if __name__ == "__main__":
    main()
