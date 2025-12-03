# app.py

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

# Map tabs → module
TAB_MAP = {
    "Control System (v0.1)": tab1_control,
    "Cycle Analysis (v0.2)": tab2_cycle,
    "Network View (v0.3)": tab3_network,
    "Queueing / Congestion (v0.4)": tab4_queue,
    "Policy Tuner (v0.5)": tab5_rl,
}

# Neon accent colors per tab
TAB_COLORS = {
    "Control System (v0.1)": "#00eaff",
    "Cycle Analysis (v0.2)": "#ff47e8",
    "Network View (v0.3)": "#5bff62",
    "Queueing / Congestion (v0.4)": "#ffd447",
    "Policy Tuner (v0.5)": "#ff6c47",
}


# ---------- OpenAI Client ----------

def get_openai_client():
    """
    Create OpenAI client.

    - If OPENAI_API_KEY is in st.secrets, use it.
    - Otherwise rely on environment variable.
    """
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        api_key = None

    if api_key:
        return OpenAI(api_key=api_key)
    return OpenAI()  # will use env var if set


# ---------- Plotly theme helpers ----------

def make_plotly_template(accent: str = "#00eaff") -> None:
    """
    Define a Plotly template with glassmorphic background and crosshair spikes.
    """
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


def get_figure(accent: str = "#00eaff") -> go.Figure:
    """
    Create a new Plotly figure using the neon 'spectre' template.
    """
    make_plotly_template(accent)
    return go.Figure()


# ---------- Global Data Hub ----------

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


def load_uploaded_file(uploaded_file) -> pd.DataFrame | None:
    """
    Load supported file types: CSV, Excel, JSON.
    """
    if uploaded_file is None:
        return None

    fname = uploaded_file.name.lower()
    try:
        if fname.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif fname.endswith(".xlsx") or fname.endswith(".xls"):
            return pd.read_excel(uploaded_file)
        elif fname.endswith(".json"):
            return pd.read_json(uploaded_file)
        else:
            st.error("Unsupported file type. Use CSV, Excel, or JSON.")
            return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def build_data_ctx(df: pd.DataFrame | None, name: str | None):
    """
    Build metadata: numeric columns, datetime columns, shape.
    """
    if df is None:
        return {
            "df": None,
            "name": None,
            "numeric_cols": [],
            "datetime_cols": [],
            "n_rows": 0,
            "n_cols": 0,
        }

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns.tolist()

    return {
        "df": df,
        "name": name,
        "numeric_cols": numeric_cols,
        "datetime_cols": datetime_cols,
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
    }


def render_data_hub(accent: str):
    """
    Render a compact Data Hub at the top of the page; this controls dataset
    for the entire system via st.session_state["data_ctx"].
    """
    init_data_ctx()
    data_ctx = st.session_state["data_ctx"]

    st.markdown("### Data Hub – Global Dataset for All Modules")
    st.write(
        "Upload any real dataset (CSV, Excel, JSON). All modules can optionally "
        "use this dataset for analysis instead of purely simulated data."
    )

    uploaded_file = st.file_uploader(
        "Upload dataset",
        type=["csv", "xlsx", "xls", "json"],
        help="This dataset will be available to Control, Cycle, Network, Queue, and Tuner modules.",
    )

    if uploaded_file is not None:
        df = load_uploaded_file(uploaded_file)
        if df is not None:
            data_ctx = build_data_ctx(df, uploaded_file.name)
            st.session_state["data_ctx"] = data_ctx

    df = data_ctx["df"]

    if df is not None:
        st.success(
            f"Loaded dataset: **{data_ctx['name']}** "
            f"({data_ctx['n_rows']} rows × {data_ctx['n_cols']} columns)"
        )

        # Show a small preview
        st.dataframe(df.head(10), use_container_width=True)

        # Show detected columns
        st.markdown("**Detected numeric columns:**")
        if data_ctx["numeric_cols"]:
            st.write(", ".join(data_ctx["numeric_cols"]))
        else:
            st.write("_None detected_")

        if data_ctx["datetime_cols"]:
            st.markdown("**Detected datetime columns:**")
            st.write(", ".join(data_ctx["datetime_cols"]))
    else:
        st.info(
            "No dataset loaded yet. Upload a file to make it available "
            "to all modules. If no data is provided, modules will fall back "
            "to synthetic simulations."
        )


# ---------- CSS & Layout ----------

def inject_css(accent: str):
    """Load CSS theme with dynamic neon accent + typewriter header + page stack."""
    st.markdown(
        f"""
        <style>

        body {{
            background: radial-gradient(circle at top, #14141f 0%, #08080d 40%, #020205 100%) !important;
        }}

        .book-shell {{
            position: relative;
            width: 100%;
            height: 80vh;
            max-width: 1100px;
            margin: 1.5rem auto;
            perspective: 1600px;
        }}

        :root {{
            --accent: {accent};
        }}

        .page {{
            position: absolute;
            inset: 0;
            border-radius: 18px;
            background: rgba(8, 8, 14, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow:
                0 18px 40px rgba(0, 0, 0, 0.55),
                0 0 40px var(--accent);
            overflow: hidden;
            transform-origin: right center;
            transition: transform 0.7s cubic-bezier(0.22,1,0.36,1),
                        opacity 0.7s cubic-bezier(0.22,1,0.36,1),
                        box-shadow 0.4s ease;
        }}

        .active-page {{
            z-index: 100;
            opacity: 1;
            transform: translateY(0px) scale(1) rotateY(0deg);
        }}

        .stack1 {{
            z-index: 90;
            opacity: 0.80;
            transform: translateY(16px) translateX(-7px) scale(0.985) rotateY(-3deg);
        }}
        .stack2 {{
            z-index: 80;
            opacity: 0.65;
            transform: translateY(34px) translateX(-10px) scale(0.97) rotateY(-5deg);
        }}
        .stack3 {{
            z-index: 70;
            opacity: 0.50;
            transform: translateY(52px) translateX(-14px) scale(0.955) rotateY(-7deg);
        }}
        .stack4 {{
            z-index: 60;
            opacity: 0.35;
            transform: translateY(70px) translateX(-18px) scale(0.94) rotateY(-9deg);
        }}

        .flip-in {{
            animation: flipInFromRight 0.7s forwards cubic-bezier(0.22,1,0.36,1);
        }}

        @keyframes flipInFromRight {{
            0% {{
                transform: translateY(0px) rotateY(90deg);
                opacity: 0;
            }}
            50% {{
                transform: translateY(-4px) rotateY(-6deg);
                opacity: 0.9;
            }}
            100% {{
                transform: translateY(0px) rotateY(0deg);
                opacity: 1;
            }}
        }}

        .page-header {{
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--accent);
            opacity: 0.9;
            margin-bottom: 0.4rem;
            width: 0;
            white-space: nowrap;
            overflow: hidden;
            border-right: 2px solid var(--accent);
            animation:
                typing 2.5s steps(40,end) forwards,
                caret 0.75s step-end infinite;
        }}

        @keyframes typing {{
            from {{ width: 0 }}
            to {{ width: 100% }}
        }}

        @keyframes caret {{
            50% {{ border-color: transparent }}
        }}

        .page-divider {{
            height: 2px;
            width: 100%;
            background: linear-gradient(
                90deg,
                rgba(255,255,255,0.0),
                var(--accent),
                rgba(255,255,255,0.0)
            );
            margin-bottom: 1rem;
        }}

        .page-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            padding: 1.4rem 1.6rem;
            overflow-y: auto;
            color: #f0f3ff;
        }}

        .page-inner::-webkit-scrollbar {{
            width: 6px;
        }}
        .page-inner::-webkit-scrollbar-track {{
            background: transparent;
        }}
        .page-inner::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.25);
            border-radius: 4px;
        }}

        .agent-box {{
            position: fixed;
            right: 12px;
            top: 110px;
            width: 280px;
            background: rgba(18,18,26,0.85);
            border: 1px solid var(--accent);
            box-shadow: 0 0 25px var(--accent);
            backdrop-filter: blur(10px);
            padding: 1rem;
            border-radius: 14px;
            z-index: 9999;
        }}

        .agent-title {{
            font-size: 0.9rem;
            letter-spacing: 0.12em;
            color: var(--accent);
            margin-bottom: 0.4rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------- Main ----------

def main():
    st.set_page_config(
        page_title="CDEPM – Quantum Policy Codex",
        layout="wide",
    )

    st.sidebar.title("CDEPM Orchestrator")
    tab_name = st.sidebar.radio("Module", list(TAB_MAP.keys()))
    accent = TAB_COLORS[tab_name]

    inject_css(accent)
    init_data_ctx()

    agent_on = st.sidebar.checkbox("Enable AI Margin Commentator")

    # Book container
    st.markdown('<div class="book-shell">', unsafe_allow_html=True)

    # Depth layers
    st.markdown('<div class="page stack4"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack3"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack2"></div>', unsafe_allow_html=True)
    st.markdown('<div class="page stack1"></div>', unsafe_allow_html=True)

    # Active page
    st.markdown(
        '<div class="page active-page flip-in"><div class="page-inner">',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="page-header">{tab_name}</div>
        <div class="page-divider"></div>
        """,
        unsafe_allow_html=True,
    )

    # ----- Global Data Hub (always at top of content) -----
    render_data_hub(accent)
    st.markdown("---")

    # ----- Render selected tab with data context -----
    data_ctx = st.session_state["data_ctx"]
    module = TAB_MAP[tab_name]
    module.render(accent, get_figure, data_ctx)

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Margin AI analyst
    if agent_on:
        client = None
        try:
            client = get_openai_client()
        except Exception:
            client = None

        st.markdown('<div class="agent-box">', unsafe_allow_html=True)
        st.markdown(
            '<div class="agent-title">Spectre.AI – Margin Analyst</div>',
            unsafe_allow_html=True,
        )

        user_query = st.text_area("Ask about this module:", key="agent_input")

        if st.button("Explain"):
            if not client:
                st.error(
                    "OpenAI client not configured. Set OPENAI_API_KEY in Streamlit secrets or env."
                )
            elif user_query.strip():
                try:
                    completion = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    f"You are a margin commentator explaining the tab "
                                    f"'{tab_name}' in a communication-engineering + "
                                    f"econometrics framing. The dataset context is: "
                                    f"{data_ctx['name'] if data_ctx['name'] else 'no dataset loaded'}."
                                ),
                            },
                            {"role": "user", "content": user_query},
                        ],
                    )
                    answer = completion.choices[0].message.content
                    st.write(answer)
                except Exception as e:
                    st.error(f"Error from OpenAI API: {e}")

        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
