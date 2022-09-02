import numpy as np
import cvxpy as cp

def opt_strategy_basic(tot_no_laps: int, 
                        tire_pars:dict,
                        tires: list) -> np.ndarray:

    k_1_lin_array = np.array([tire_pars[x[0]]['k_1_lin'] for x in tires])
    k_0_array = np.array([tire_pars[x[0]]['k_0'] for x in tires])
    age_array = np.array([x[1] for x in tires])

    no_stints = len(tires)

    P = np.eye(no_stints) * 0.5 * k_1_lin_array * 2    
    q = (0.5 + age_array) * k_1_lin_array + k_0_array

    G = np.eye(no_stints) * -1.0
    h = np.ones(no_stints) * -1.0

    A = np.ones((1, no_stints))
    b = np.array([tot_no_laps])

    x = cp.Variable(no_stints, integer=True)

    P = cp.Constant(P)

    objective = cp.Minimize(0.5* cp.quad_form(x,P)+ q @ x)
    constraints = [G @ x <= h, A @ x ==b]
    prob = cp.Problem(objective, constraints)

    tmp = prob.solve(solver='ECOS_BB')

    if not np.isinf(tmp):
        stint_length = np.round(x.values).astype(np.int32)
    else:
        stint_length = None

    return stint_length

if __name__ == '__main__':
    pass