import numpy as np

from qiskit.primitives import Sampler
from qiskit_algorithms import SamplingVQE
from qiskit_algorithms.optimizers import COBYLA
from qiskit.circuit.library import TwoLocal
from qiskit_optimization.algorithms import MinimumEigenOptimizer


def run_vqe_solver(qubo, num_assets, reps):

    # --- Define the callback function ---
    history = []
    def callback(eval_count, params, value, std):
        history.append((eval_count, np.real(value)))

    # --- Define the Ansatz ---
    ansatz = TwoLocal(
        num_assets,
        rotation_blocks='ry',
        entanglement_blocks='cz',
        reps=reps,
        entanglement='full'
    )

    # VQE setup
    sampler = Sampler()
    optimizer = COBYLA(maxiter=500)

    vqe = SamplingVQE(
        sampler=sampler,
        ansatz=ansatz,
        optimizer=optimizer,
        callback=callback
    )

    # --- Compute result ---
    solver = MinimumEigenOptimizer(vqe)
    result = solver.solve(qubo)
    return result, history