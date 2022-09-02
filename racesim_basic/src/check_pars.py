def check_pars(sim_opts: dict, pars_in:dict, use_plot: bool) -> None:

    if pars_in['driver_pars']['tire_pars']['tire_deg_model'] != 'lin' and sim_opts['use_qp']: 
        raise RuntimeError('QP is only available for a linear model')

    if use_plot and sim_opts['use_qp']:
        print('Plotting will ne reduced')

    if not 0 <= sim_opts['min_no_pitstops'] < sim_opts['max_no_pitstops']:
        raise RuntimeError('Wrong nomber of pitstops selected')

    if sim_opts['min_no_pitstops'] == 0 and sim_opts['enforce_diff_compounds']:
        print('Different compounds cannot be enforced if the nimber of pitstops is 0')

    if sim_opts['use_qp'] and sim_opts['fcy_phases']:
        print('FCY phases cannot be simulated with the quadratic optimisation method')