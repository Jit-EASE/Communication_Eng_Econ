# app.py — Stable Version (no overlays) with Data Hub, Cleaning, Inspector AI, Logs

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

# ------------------------------------------
# TAB CONFIG
# ------------------------------------------

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

# ------------------------------------------
# LOGGING
# ------------------------------------------

def init_log_ctx():
    if "logs" not in st.session_state:
        st.session_state["logs"] = []

def _log(level: str, msg: str):
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
    for entry in logs[-200:]:
        icon = "🟢" if entry["level"] == "INFO" else (
            "🟡" if entry["level"] == "WARN" else "🔴"
        )
        st.write(f"{icon} **{entry['level']}** — {entry['msg']}")

# ------------------------------------------
# OPENAI CLIENT
# ------------------------------------------

def get_openai_client():
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        api_key = None

    if api_key:
        return OpenAI(api_key=api_key)
    return OpenAI()

# ------------------------------------------
# PLOTLY CONFIG
# ------------------------------------------

def make_plotly_template(accent: str):
    pio.templates["spectre"] = go.layout.Template(
        layout=dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0f3ff"),
            hoverlabel=dict(
                bgcolor="rgba(10,10,20,0.85)",
                bordercolor=accent,
                font=dict(color="white"),
            ),
            xaxis=dict(
                showspikes=True,
                spikemode="across",
                spikecolor=accent,
                gridcolor="rgba(255,255,255,0.1)",
                zeroline=False,
            ),
            yaxis=dict(
                showspikes=True,
                spikemode="across",
                spikecolor=accent,
                gridcolor="rgba(255,255,255,0.1)",
                zeroline=False,
            ),
        )
    )
    pio.templates.default = "spectre"

def get_figure(accent: str):
    make_plotly_template(accent)
    return go.Figure()

# ------------------------------------------
# DATA HUB / CLEANING / INSPECTOR
# ------------------------------------------

def init_data_ctx():
    if "data_ctx" not in st.session_state:
        st.session_state["data_ctx"] = {
            "df": None,
            "name": None,
            "numeric_cols": [],
            "datetime_cols": [],
            "categorical_cols": [],
            "profile": {},
        }

def load_uploaded_file(uploaded):
    if uploaded is None:
        return None, None

    name = uploaded.name.lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(uploaded, engine="openpyxl")
        elif name.endswith(".json"):
            df = pd.read_json(uploaded)
        else:
            st.error("Unsupported format. Please upload CSV, Excel, or JSON.")
            log_warn(f"Unsupported file type attempted: {uploaded.name}")
            return None, None

        log_info(f"Loaded dataset '{uploaded.name}' with shape {df.shape}.")
        return df, uploaded.name
    except Exception as e:
        msg = f"Error reading file '{uploaded.name}': {e}"
        st.error(msg)
        log_error(msg)
        return None, None

def profile_dataset(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    profile = {
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "n_numeric": len(numeric_cols),
        "n_datetime": len(datetime_cols),
        "n_categorical": len(categorical_cols),
        "primary_numeric": numeric_cols[0] if numeric_cols else None,
    }

    return numeric_cols, datetime_cols, categorical_cols, profile

def rebuild_data_ctx(df: pd.DataFrame, name: str):
    numeric_cols, datetime_cols, categorical_cols, profile = profile_dataset(df)
    return {
        "df": df,
        "name": name,
        "numeric_cols": numeric_cols,
        "datetime_cols": datetime_cols,
        "categorical_cols": categorical_cols,
        "profile": profile,
    }

def apply_cleaning(df: pd.DataFrame, mode: str):
    clean_df = df.copy()

    if mode == "None":
        log_info("No cleaning applied.")
        return clean_df

    if mode == "Drop rows with missing values":
        clean_df = clean_df.dropna()
        log_info("Dropped rows with any NA.")

    elif mode == "Fill numeric NA with median":
        num_cols = clean_df.select_dtypes(include="number").columns
        for c in num_cols:
            med = clean_df[c].median()
            clean_df[c] = clean_df[c].fillna(med)
        log_info("Filled numeric NA with median.")

    elif mode == "Fill numeric NA with 0":
        num_cols = clean_df.select_dtypes(include="number").columns
        for c in num_cols:
            clean_df[c] = clean_df[c].fillna(0)
        log_info("Filled numeric NA with 0.")

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
        st.error("OpenAI client initialisation failed.")
        log_error(f"OpenAI init failed (Inspector): {e}")
        return

    summary = {
        "name": data_ctx.get("name"),
        "shape": df.shape,
        "numeric_cols": data_ctx.get("numeric_cols", []),
        "categorical_cols": data_ctx.get("categorical_cols", []),
        "datetime_cols": data_ctx.get("datetime_cols", []),
        "primary_numeric": data_ctx.get("profile", {}).get("primary_numeric"),
    }

    st.markdown("#### 🔍 Dataset Inspector AI")
    q = st.text_area(
        "Ask about model choices, patterns, or how this dataset could feed the five modules:",
        height=80,
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
                            "You are a data scientist helping an applied econometrician. "
                            "Given a dataset summary, suggest suitable models and how it can be used "
                            "for control systems, cycle analysis, network modelling, queueing, and policy tuning."
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

    st.markdown("### 📁 Data Hub — Global Dataset for All Modules")

    uploaded = st.file_uploader(
        "Upload dataset (CSV, Excel, JSON)",
        type=["csv", "xlsx", "xls", "json"],
        key="global_uploader",
    )

    if uploaded is not None:
        df, name = load_uploaded_file(uploaded)
        if df is not None:
            st.session_state["data_ctx"] = rebuild_data_ctx(df, name)
            data_ctx = st.session_state["data_ctx"]

    df = data_ctx.get("df")

    if df is None:
        st.info("No dataset loaded. Modules will run on synthetic data / internal simulations.")
        st.markdown("---")
        return

    # Preview
    st.success(
        f"Loaded dataset: **{data_ctx['name']}** "
        f"({df.shape[0]} rows × {df.shape[1]} columns)"
    )
    st.dataframe(df.head(10), use_container_width=True)

    st.markdown(
        f"**Numeric columns:** {', '.join(data_ctx['numeric_cols']) or '_None_'}  \n"
        f"**Datetime columns:** {', '.join(data_ctx['datetime_cols']) or '_None_'}  \n"
        f"**Categorical columns:** {', '.join(data_ctx['categorical_cols']) or '_None_'}"
    )

    # Cleaning
    st.markdown("#### 🧹 Dataset Cleaning")
    cleaning_mode = st.selectbox(
        "Missing value strategy",
        ["None", "Drop rows with missing values", "Fill numeric NA with median", "Fill numeric NA with 0"],
        key="cleaning_mode",
    )

    if st.button("Apply cleaning / rebuild dataset context", key="apply_cleaning_btn"):
        clean_df = apply_cleaning(df, cleaning_mode)
        st.session_state["data_ctx"] = rebuild_data_ctx(clean_df, data_ctx["name"])
        data_ctx = st.session_state["data_ctx"]
        st.success("Cleaning applied and dataset context rebuilt.")
        log_info(f"Cleaning mode applied: {cleaning_mode}")

    # Inspector AI
    with st.expander("🔍 Dataset Inspector AI", expanded=False):
        render_dataset_inspector_ai(data_ctx, accent)

    st.markdown("---")

# ------------------------------------------
# CSS (No overlays, no blocking)
# ------------------------------------------

def inject_css(accent: str):
    st.markdown(
        f"""
        <style>
        body {{
            background: radial-gradient(circle at top, #14141f 0%, #08080d 40%, #020205 100%) !important;
        }}

        .block-container {{
            padding-top: 0.4rem !important;
        }}

        :root {{
            --accent: {accent};
        }}

        .page-container {{
            width: 100%;
            max-width: 1100px;
            margin: 0 auto;
            background: rgba(8,8,14,0.82);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 10px 35px rgba(0,0,0,0.45);
            padding: 1.2rem 1.4rem;
            animation: flipIn 0.6s ease both;
        }}

        @keyframes flipIn {{
            0% {{
                opacity: 0;
                transform: translateY(30px) rotateX(-35deg);
            }}
            100% {{
                opacity: 1;
                transform: translateY(0px) rotateX(0deg);
            }}
        }}

        .page-header {{
            color: var(--accent);
            font-size: 1.2rem;
            font-weight: 650;
            border-right: 2px solid var(--accent);
            white-space: nowrap;
            overflow: hidden;
            width: 0;
            animation: typing 2s steps(60, end) forwards, caret 0.7s step-end infinite;
        }}

        @keyframes typing {{
            from {{ width: 0; }}
            to {{ width: 100%; }}
        }}

        @keyframes caret {{
            50% {{ border-color: transparent; }}
        }}

        .page-divider {{
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            margin: 0.7rem 0 1.0rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------
# MAIN
# ------------------------------------------

def main():
    st.set_page_config(page_title="CDEPM – Quantum Policy Codex", layout="wide")

    init_log_ctx()

    st.sidebar.title("CDEPM Orchestrator")

    tab_name = st.sidebar.radio("Module", list(TAB_MAP.keys()))
    accent = TAB_COLORS[tab_name]

    show_logs = st.sidebar.checkbox("Show system log")
    agent_on = st.sidebar.checkbox("Enable AI Margin Analyst")

    inject_css(accent)
    init_data_ctx()

    # Outer container
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-header">{tab_name}</div><div class="page-divider"></div>',
        unsafe_allow_html=True,
    )

    # Data hub (global dataset)
    render_data_hub(accent)
    data_ctx = st.session_state["data_ctx"]

    # Render selected module
    module = TAB_MAP[tab_name]
    try:
        module.render(accent, get_figure, data_ctx)
    except Exception as e:
        st.error(f"Error inside module '{tab_name}': {e}")
        log_error(f"Tab '{tab_name}' error: {e}")

    st.markdown("</div>", unsafe_allow_html=True)  # close page-container

    # Margin AI Analyst (explains current module)
    if agent_on:
        try:
            client = get_openai_client()
            st.markdown("### 🤖 Spectre.AI – Margin Analyst")
            q = st.text_area(
                "Ask about this module, its logic, or how to interpret its outputs:",
                key="module_ai_q",
            )
            if st.button("Explain Module", key="module_ai_btn") and q.strip():
                completion = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a precise, technical explainer for an engineer–economist. "
                                "Explain without fluff, focusing on logic, control intuition, and policy meaning."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Module: {tab_name}\n\nQuestion: {q}",
                        },
                    ],
                )
                st.write(completion.choices[0].message.content)
                log_info("Margin Analyst AI answered a module query.")
        except Exception as e:
            st.error(f"Margin Analyst error: {e}")
            log_error(f"Margin Analyst error: {e}")

    # System log
    if show_logs:
        st.markdown("---")
        st.markdown("### System Log")
        render_log_panel()

if __name__ == "__main__":
    main()
