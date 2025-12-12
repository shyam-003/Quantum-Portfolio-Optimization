import numpy as np
import pandas as pd
import yfinance as yf
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.converters import QuadraticProgramToQubo
from qiskit.quantum_info import SparsePauliOp

try:
    from qaoa_solver import run_qaoa_solver
    from vqe_solver import run_vqe_solver
except ImportError:
    print("Warning: Solver files (qaoa_solver.py, vqe_solver.py) not found. Define dummy functions.")
    def run_qaoa_solver(*args): return type('Result', (object,), {'x': []})(), []
    def run_vqe_solver(*args): return type('Result', (object,), {'x': []})(), []



def get_preview_data(tickers):
    """
    Downloads market data for the Streamlit UI preview
    """
    try:
        data = yf.download(
            tickers,
            start="2023-01-01",
            end="2024-01-01",
            progress=False,
            auto_adjust=True
        )["Close"]
    
    except Exception as e:
        print(f"Error fetching preview data: {e}")
        return pd.DataFrame(), pd.Series()

    returns = data.pct_change().dropna()
    sigma = returns.cov() * 252
    
    last_prices = data.iloc[-1]
    return sigma, last_prices


def run_quantum_solver(algorithm, tickers, budget, risk_factor, depth):
    """
    Central function called by app.py to execute the chosen quantum algorithm
    """

    # --- Data Fetching & Financial Metrics ---
    # -----------------------------------------
    try:
        data = yf.download(
            tickers,
            start="2023-01-01",
            end="2024-01-01",
            progress=False,
            auto_adjust=True
        )["Close"]
    
    except Exception as e:
        raise RuntimeError(f"Failed to fetch financial data: {e}")
        
    returns = data.pct_change().dropna()
    num_assets = len(tickers)
    
    mu = returns.mean().to_numpy() * 252
    sigma = returns.cov().to_numpy() * 252

    # --- Build Quadratic Model & Ising Hamiltonian ---
    # -------------------------------------------------
    qp = QuadraticProgram()
    
    for i in range(num_assets):
        qp.binary_var(name=tickers[i])
        
    qp.minimize(
        linear=-mu,
        quadratic=risk_factor * sigma
    )
    
    qp.linear_constraint(
        linear={tickers[i]: 1 for i in range(num_assets)},
        sense="==",
        rhs=budget,
        name="budget_constraint"
    )
    
    # --- convert to QUBO ---
    # -------------------------------------------------
    converter = QuadraticProgramToQubo(penalty=100)
    qubo = converter.convert(qp)

    result = None
    history = None

    if algorithm == "QAOA":
        
        result, history = run_qaoa_solver(qubo, depth)
    elif algorithm == "VQE":
        result, history = run_vqe_solver(qubo, num_assets, depth)
    else:
        raise ValueError("Invalid algorithm specified in run_quantum_solver.")
    
    if result is None or result.x is None or len(result.x) == 0:
        return None, None, None, None, None
    

    # --- FINAL METRICS CALCULATION ---
    # -------------------------------------------------
    selection = result.x
    selected_tickers = [tickers[i] for i, x in enumerate(selection) if x == 1]

    opt_return = np.dot(mu, selection)
    opt_risk   = np.sqrt(selection.T @ sigma @ selection)
    sharpe     = opt_return / opt_risk if opt_risk > 0 else 0

    steps = [s for s, v in history]
    values = [v for s, v in history]

    # print(f"Selected Tickers : {selected_tickers}")
    # print(f"Optimal return : {opt_return}")
    # print(f"Optimal risk : {opt_risk}")
    # print(f"Sharpe ration : {sharpe}")

    return selected_tickers, (steps, values), opt_return, opt_risk, sharpe