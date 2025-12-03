# app.py

import streamlit as st
import openai

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


def inject_css(accent: str):
    """Load CSS theme with dynamic neon accent + typewriter header."""
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

        /* ----- Neon Accent Color ----- */
        :root {{
            --accent: {accent};
        }}

        /* ----- Page Styles (same as before, but neon tuned) ----- */
        .page {{
            position: absolute;
            inset: 0;
            border-radius: 18px;
            background: rgba(8, 8, 14, 0.75);
            backdrop-filter: blur(12px);
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

        /* Page flip */
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

        /* ----- Typewriter Header Animation ----- */
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

        /* Divider */
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

        /* Page content container */
        .page-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            padding: 1.4rem 1.6rem;
            overflow-y: auto;
            color: #f0f3ff;
        }}

        /* ----- Margin Commentator (AI Agent) ----- */
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


def main():
    st.set_page_config(
        page_title="CDEPM – Quantum Policy Codex",
        layout="wide"
    )

    # Sidebar tab selector
    st.sidebar.title("CDEPM Orchestrator")
    tab_name = st.sidebar.radio("Module", list(TAB_MAP.keys()))
    accent = TAB_COLORS[tab_name]

    # Inject CSS with dynamic accent color
    inject_css(accent)

    # Toggle for margin agent
    agent_on = st.sidebar.checkbox("Enable AI Margin Commentator")

    # Book-shell container
    st.markdown('<div class="book-shell">', unsafe_allow_html=True)

    # Four depth layers
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

    # Render actual module
    module = TAB_MAP[tab_name]
    module.render()

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- AI Margin Commentator ----
    if agent_on:
        with st.container():
            st.markdown('<div class="agent-box">', unsafe_allow_html=True)
            st.markdown(f'<div class="agent-title">Spectre.AI – Margin Analyst</div>', unsafe_allow_html=True)

            user_query = st.text_area("Ask about this module:", key="agent_input")

            if st.button("Explain"):
                if user_query.strip():
                    try:
                        completion = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": f"You are a margin commentator explaining the tab '{tab_name}'."},
                                {"role": "user", "content": user_query}
                            ]
                        )
                        st.write(completion.choices[0].message["content"])
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
