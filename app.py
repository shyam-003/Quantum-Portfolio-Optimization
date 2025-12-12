import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from main import get_preview_data, run_quantum_solver


# =================
# SESSION STATES
# =================
if "algorithm" not in st.session_state:
    st.session_state.algorithm = None
if "run_complete" not in st.session_state:
    st.session_state.run_complete = False
if "selected_tickers_final" not in st.session_state:
    st.session_state.selected_tickers_final = None
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "history" not in st.session_state:
    st.session_state.history = None

# ==========================
# STREAMLIT UI SETTINGS
# ==========================
st.set_page_config(page_title="Quantum Portfolio Optimizer", layout="wide")

st.markdown("""
    <style>
        /* Container background */
        div[data-testid="metric-container"] {
            background-color: #f9f9f9 !important;
            padding: 10px !important;
            border-radius: 5px !important;
        }

        /* Label: 'Return', 'Risk', 'Sharpe Ratio' */
        div[data-testid="metric-container"] label[data-testid="stMetricLabel"] > div > p {
            color: black !important;
            font-weight: 600 !important;
        }

        /* Value: the main number */
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] > div:nth-child(1) {
            color: black !important;
            font-weight: 700 !important;
        }

        div[data-testid="metric-container"] div[data-testid="stMetricDelta"] > div {
            color: black !important;
        }
                
    </style>
""", unsafe_allow_html=True)

st.title("⚛️ Quantum Portfolio Optimization")


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.header("1. Asset Universe")

    all_tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "JPM", "V", "JNJ", "WMT",
        "PG", "UNH", "HD", "BAC", "MA",
        "PFE", "DIS", "KO", "PEP", "CSCO",
        "XOM", "CVX", "COST", "AVGO", "ADBE"
    ]

    selected_tickers = st.multiselect(
        "Select Assets (min 3, max 10):",
        options=all_tickers,
        default=all_tickers[:5],
        max_selections=10
    )

    num_selected = len(selected_tickers)
    st.caption(f"Selected: {num_selected} assets")

    if num_selected < 3:
        st.error("⚠️ Please select at least 3 assets.")

    st.divider()

    # =========================
    # CONSTRAINTS
    # =========================
    st.header("2. Constraints")

    if num_selected >= 3:
        budget = st.number_input(
            "Budget (assets to pick)",
            min_value=1,
            max_value=num_selected,
            value=min(3, num_selected),
            step=1
        )
    else:
        budget = None

    risk_factor = st.slider("Risk Factor (q)", 0.0, 1.0, 0.5, 0.1)

    st.divider()

    # =========================
    # ALGORITHM SELECTION
    # =========================
    st.header("3. Choose Algorithm")

    colA, colB = st.columns(2)

    with colA:
        if st.button("📡 Select QAOA"):
            st.session_state.algorithm = "QAOA"
            st.session_state.run_complete = False

    with colB:
        if st.button("🧪 Select VQE"):
            st.session_state.algorithm = "VQE"
            st.session_state.run_complete = False

    if st.session_state.algorithm:
        st.success(f"Selected Algorithm: {st.session_state.algorithm}")

    depth = st.slider("Circuit Depth / Reps", 1, 4, 2)
    
    st.divider()

    # =========================
    # RUN BUTTON
    # =========================

    run_btn = st.button("🚀 Run Optimization", type="primary", key="run_optimizer")


# ==============================
# MAIN PANEL CONTENT
# ==============================
if num_selected >= 3:

    # --- Data Preview Section ---
    with st.spinner("Loading market data..."):
        try:
            pre_sigma, last_prices = get_preview_data(selected_tickers)
        except Exception:
            st.error("Could not fetch market data. Check tickers.")
            pre_sigma = pd.DataFrame()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Covariance Matrix")
        if not pre_sigma.empty:
            
            fig_cov, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(pre_sigma, cmap="coolwarm", cbar_kws={'label': 'Covariance (Risk)'})
            ax.set_title("Annualized Covariance (Risk Input)")
            st.pyplot(fig_cov)

    with col2:
        st.subheader("💲 Latest Prices")
        if not pre_sigma.empty:
            dfp = pd.DataFrame({
                "Ticker": selected_tickers,
                "Price ($)": [f"{last_prices[t]:.2f}" for t in selected_tickers]
            })
            st.dataframe(dfp, hide_index=True)

    st.divider()


    # ===================================================
    # EXECUTE OPTIMIZATION LOGIC
    # ===================================================
    if run_btn:
        st.session_state.run_complete = False
        st.session_state.selected_tickers_final = None
        st.session_state.metrics = None
        st.session_state.history = None

        if st.session_state.algorithm is None:
            st.error("⚠️ Please select an algorithm first (QAOA or VQE) in the sidebar.")
            st.stop()

        if budget is None:
            st.error("Select at least 3 assets and define the budget.")
            st.stop()
            
        # --- UNIFIED EXECUTION CALL ---
        algo_name = st.session_state.algorithm
        st.subheader(f"Running {algo_name} (Reps/Depth={depth})")
        
        with st.spinner(f"Optimizing via {algo_name}..."):
            (selected_tickers_final, history, opt_return, opt_risk, sharpe) = run_quantum_solver(
                algo_name, selected_tickers, budget, risk_factor, depth
            )

        # Post-execution Check and Save
        if selected_tickers_final is None:
            st.error("Optimization failed. Check server logs for data loading or solver errors.")
        else:
            # Storing final results in session state
            st.session_state.selected_tickers_final = selected_tickers_final
            st.session_state.history = history
            st.session_state.metrics = {
                'Return': opt_return,
                'Risk': opt_risk,
                'Sharpe': sharpe,
                'Budget': budget,
                'Algorithm': algo_name
            }
            st.session_state.run_complete = True
            st.success(f"{algo_name} Optimization Complete!")
            st.rerun()


    # ======================
    # DISPLAY RESULTS
    # ======================
    if st.session_state.run_complete:
        selected_tickers_final = st.session_state.selected_tickers_final
        history = st.session_state.history
        metrics = st.session_state.metrics
        
        r1, r2, r3 = st.columns([1.2, 2, 1])

        # Portfolio
        with r1:
            st.markdown("### 🎯 Selected Portfolio")
            
            # Recalculate selection count from the list of tickers
            current_selection_count = len(selected_tickers_final)
            
            # Constraint Check
            if current_selection_count != metrics['Budget']:
                st.error(f"⚠️ **Constraint Violated:** Selected {current_selection_count} assets, but budget is {metrics['Budget']}. Check QUBO penalty in main.py.")

            if not selected_tickers_final:
                st.warning("No assets selected.")
            else:
                for asset in selected_tickers_final:
                    st.success(asset)

        # Learning Curve
        with r2:
            st.markdown("### 📈 Optimization Convergence (Cost vs. Iterations)")
            steps, energies = history
            fig_lc, ax_lc = plt.subplots()
            ax_lc.plot(steps, energies, linewidth=2, color='purple')
            ax_lc.set_title(f"{metrics['Algorithm']} Cost Trajectory (Depth={depth})")
            ax_lc.set_xlabel("Optimizer Iterations")
            ax_lc.set_ylabel("Cost (Expected Energy)")
            ax_lc.grid(True)
            st.pyplot(fig_lc)

        # Metrics
        with r3:
            st.markdown("### 🏆 Metrics")
            st.metric("Return", f"{metrics['Return']:.2f}%")
            st.metric("Risk", f"{metrics['Risk']:.2f}%")
            st.metric("Sharpe Ratio", f"{metrics['Sharpe']:.4f}")

else:
    st.info("👈 Select at least 3 assets to begin.")