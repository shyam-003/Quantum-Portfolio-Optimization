import numpy as np
from qiskit.primitives import Sampler
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit.quantum_info import SparsePauliOp


def run_qaoa_solver(qubo, reps):
    
    # --- convert to Ising Hamiltonian ---
    # -------------------------------------------------
    op, offset = qubo.to_ising()
    op = SparsePauliOp(op.paulis, op.coeffs.real)

    # --- Define callback function ---
    history = []
    def callback(eval_count, params, value, std):
        history.append((eval_count, np.real(value)))

    # --- Setup QAOA solver ---
    sampler = Sampler()
    optimizer = COBYLA(maxiter=500)
    qaoa = QAOA(
        sampler=sampler,
        optimizer=optimizer,
        reps=reps,
        callback=callback
    )
    
    # --- Compute result ---
    solver = MinimumEigenOptimizer(qaoa)
    result = solver.solve(qubo)
    return result, history