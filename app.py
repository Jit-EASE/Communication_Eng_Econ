# app.py — Stable Version (No Drag Curl) with Data Hub, Cleaning, Inspector AI, Logs

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
# TAB MAP
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

def _log(level, msg):
    st.session_state["logs"].append({"level": level, "msg": msg})

def log_info(msg): _log("INFO", msg)
def log_warn(msg): _log("WARN", msg)
def log_error(msg): _log("ERROR", msg)

def render_log_panel():
    logs = st.session_state.get("logs", [])
    for entry in logs[-200:]:
        icon = "🟢" if entry["level"] == "INFO" else (
            "🟡" if entry["level"] == "WARN" else "🔴"
        )
        st.write(f"{icon} **{entry['level']}** — {entry['msg']}")

# ------------------------------------------
# OPENAI
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
# PLOTLY THEMES
# ------------------------------------------

def make_plotly_template(accent):
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
            ),
            yaxis=dict(
                showspikes=True,
                spikemode="across",
                spikecolor=accent,
                gridcolor="rgba(255,255,255,0.1)",
            ),
        )
    )
    pio.templates.default = "spectre"

def get_figure(accent):
    make_plotly_template(accent)
    return go.Figure()

# ------------------------------------------
# DATA HUB + CLEANING + AI INSPECTOR
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
            return pd.read_csv(uploaded), uploaded.name
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(uploaded, engine="openpyxl"), uploaded.name
        elif name.endswith(".json"):
            return pd.read_json(uploaded), uploaded.name
        else:
            st.error("Unsupported format (CSV, Excel, JSON).")
            return None, None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        log_error(str(e))
        return None, None

def profile_dataset(df):
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64[ns]"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    profile = {
        "n_numeric": len(numeric_cols),
        "n_datetime": len(datetime_cols),
        "n_categorical": len(categorical_cols),
        "primary_numeric": numeric_cols[0] if numeric_cols else None,
    }

    return numeric_cols, datetime_cols, categorical_cols, profile

def rebuild_data_ctx(df, name):
    numeric, dt, cat, prof = profile_dataset(df)
    return {
        "df": df,
        "name": name,
        "numeric_cols": numeric,
        "datetime_cols": dt,
        "categorical_cols": cat,
        "profile": prof,
    }

def apply_cleaning(df, mode):
    clean_df = df.copy()

    if mode == "Drop rows with missing values":
        clean_df = clean_df.dropna()
        log_info("Dropped rows with NA.")

    elif mode == "Fill NA with median":
        for col in clean_df.select_dtypes(include="number"):
            clean_df[col] = clean_df[col].fillna(clean_df[col].median())
        log_info("Filled NA with median.")

    elif mode == "Fill NA with 0":
        clean_df = clean_df.fillna(0)
        log_info("Filled NA with 0.")

    return clean_df

def render_dataset_inspector_ai(data_ctx, accent):
    df = data_ctx["df"]
    if df is None:
        st.info("Load a dataset first.")
        return

    client = get_openai_client()

    summary = {
        "name": data_ctx["name"],
        "shape": df.shape,
        "numeric_cols": data_ctx["numeric_cols"],
        "categorical_cols": data_ctx["categorical_cols"],
        "datetime_cols": data_ctx["datetime_cols"],
    }

    q = st.text_area("Dataset Inspector AI", "What models fit this data?")
    if st.button("Ask Inspector"):
        try:
            completion = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role":"system","content":"You are a data-profiling expert."},
                    {
                        "role":"user",
                        "content": f"SUMMARY: {summary}\nQUESTION: {q}",
                    },
                ],
            )
            st.write(completion.choices[0].message.content)
        except Exception as e:
            st.error(str(e))
            log_error(str(e))

def render_data_hub(accent):
    init_data_ctx()
    data_ctx = st.session_state["data_ctx"]

    st.markdown("### 📁 Data Hub – Global Dataset Loader")

    uploaded = st.file_uploader("Upload dataset (CSV, Excel, JSON)",
                                type=["csv","xlsx","xls","json"])

    if uploaded is not None:
        df, name = load_uploaded_file(uploaded)
        if df is not None:
            st.session_state["data_ctx"] = rebuild_data_ctx(df, name)
            data_ctx = st.session_state["data_ctx"]

    df = data_ctx["df"]

    if df is None:
        st.info("No dataset loaded. Modules will use synthetic data.")
        st.markdown("---")
        return

    st.success(f"Loaded dataset: **{data_ctx['name']}**")
    st.dataframe(df.head(10))

    st.markdown(f"**Numeric Columns:** {', '.join(data_ctx['numeric_cols']) or '_None_'}")

    # Cleaning
    st.markdown("#### Cleaning")
    mode = st.selectbox("Choose cleaning mode",
                        ["None","Drop rows with missing values","Fill NA with median","Fill NA with 0"])
    if st.button("Apply Cleaning"):
        clean_df = apply_cleaning(df, mode)
        st.session_state["data_ctx"] = rebuild_data_ctx(clean_df, data_ctx["name"])
        st.success("Cleaning applied.")

    # Inspector
    render_dataset_inspector_ai(data_ctx, accent)
    st.markdown("---")

# ------------------------------------------
# CSS – No Drag Curl, only smooth flip-in
# ------------------------------------------

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
        :root {{ --accent: {accent}; }}

        .book-shell {{
            position: relative;
            width: 100%;
            max-width: 1100px;
            margin: 0.5rem auto;
            perspective: 1800px;
        }}

        .page {{
            position: absolute;
            inset: 0;
            border-radius: 18px;
            background: rgba(8,8,14,0.82);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 20px 40px rgba(0,0,0,0.55);
        }}

        .stack1 {{ z-index: 90; opacity: 0.85; transform: translateY(10px); }}
        .stack2 {{ z-index: 80; opacity: 0.70; transform: translateY(20px); }}
        .stack3 {{ z-index: 70; opacity: 0.55; transform: translateY(30px); }}
        .stack4 {{ z-index: 60; opacity: 0.40; transform: translateY(40px); }}

        .active-page {{
            z-index: 100;
            opacity: 1;
            animation: flipIn 0.6s ease both;
        }}

        @keyframes flipIn {{
            0% {{ opacity: 0; transform: rotateY(-80deg) translateX(-50px); }}
            100% {{ opacity: 1; transform: rotateY(0deg) translateX(0px); }}
        }}

        .page-inner {{
            height: 75vh;
            padding: 0.8rem 1.2rem;
            overflow-y: auto;
            color: #f0f3ff;
        }}

        .page-header {{
            color: var(--accent);
            font-size: 1.2rem;
            border-right: 2px solid var(--accent);
            white-space: nowrap;
            overflow: hidden;
            width: 0;
            animation: typing 2s steps(60,end) forwards, caret 0.7s infinite;
        }}

        @keyframes typing {{ from {{ width: 0; }} to {{ width: 100%; }} }}
        @keyframes caret {{ 50% {{ border-color: transparent; }} }}

        .page-divider {{
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            margin: 0.7rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ------------------------------------------
# MAIN
# ------------------------------------------

def main():
    st.set_page_config(page_title="CDEPM – Policy Codex", layout="wide")

    init_log_ctx()

    st.sidebar.title("CDEPM Orchestrator")
    tab_name = st.sidebar.radio("Module", list(TAB_MAP.keys()))
    accent = TAB_COLORS[tab_name]
    show_logs = st.sidebar.checkbox("Show Log Panel")

    agent_on = st.sidebar.checkbox("Enable AI Margin Analyst")

    inject_css(accent)
    init_data_ctx()

    # Book layers
    st.markdown('<div class="book-shell">', unsafe_allow_html=True)
    st.markdown('<div class="page stack4"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack3"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack2"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack1"></div>', unsafe_allow_html=True)

    st.markdown('<div class="page active-page"><div class="page-inner">', unsafe_allow_html=True)
    st.markdown(f'<div class="page-header">{tab_name}</div><div class="page-divider"></div>', unsafe_allow_html=True)

    # Data Hub
    render_data_hub(accent)
    data_ctx = st.session_state["data_ctx"]

    # Module Renderer
    try:
        module = TAB_MAP[tab_name]
        module.render(accent, get_figure, data_ctx)
    except Exception as e:
        st.error(str(e))
        log_error(str(e))

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Margin Analyst
    if agent_on:
        client = get_openai_client()
        q = st.text_area("Ask Spectre.AI about this module:")
        if st.button("Explain Module"):
            try:
                completion = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "You are a precise econometric analyst."},
                        {"role": "user", "content": f"Module: {tab_name}\n{q}"},
                    ],
                )
                st.write(completion.choices[0].message.content)
            except Exception as e:
                st.error(str(e))
                log_error(str(e))

    # Logs
    if show_logs:
        st.markdown("---")
        st.markdown("### System Log")
        render_log_panel()

if __name__ == "__main__":
    main()
