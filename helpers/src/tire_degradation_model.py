import numpy as np
import math

def tire_degradation_model(tire_age_start:int or float,
stint_time:int,
tire_compound: str,
tire_pars:dict)->np.ndarray or float:

    if tire_pars['tire_deg_model'] not in ['lin','quad','cub','ln']:
        raise RuntimeError('Tire degradation model unknown')

    if stint_time == 1:
        if tire_pars["tire_deg_model"] == 'lin':
            t_tire_deg = (tire_pars[tire_compound]['k_0']+tire_pars[tire_compound]['k_1_lin']*tire_age_start)

        elif tire_pars["tire_deg_model"] == 'quad':
            t_tire_deg = (tire_pars[tire_compound]['k_0']
            +tire_pars[tire_compound]['k_1_quad']* tire_age_start
            +tire_pars[tire_compound]['k_2_quad']*math.pow(tire_age_start,2))

        elif tire_pars["tire_deg_model"] == 'cub':
            t_tire_deg = (tire_pars[tire_compound]['k_0']
            +tire_pars[tire_compound]['k_1_cub']* tire_age_start
            +tire_pars[tire_compound]['k_2_cub']*math.pow(tire_age_start,2)
            +tire_pars[tire_compound]['k_3_cub']*math.pow(tire_age_start,3))

        else:
            t_tire_deg = (tire_pars[tire_compound]['k_0']
            +tire_pars[tire_compound]['k_1_ln']
            *math.log(tire_pars[tire_compound]['k_2_ln']
            *tire_age_start +1.0))
    
    else:
        temp_laps = np.arange(tire_age_start,tire_age_start + stint_time)

        if tire_pars["tire_deg_model"] == 'lin':
            t_tire_deg = (tire_pars[tire_compound]['k_0'] + tire_pars[tire_compound]['k_1_lin'] * temp_laps)

        elif tire_pars["tire_deg_model"] == 'quad':
            t_tire_deg = (tire_pars[tire_compound]['k_0']
            +tire_pars[tire_compound]['k_1_quad']* temp_laps
            +tire_pars[tire_compound]['k_2_quad']*math.pow(temp_laps,2))

        elif tire_pars["tire_deg_model"] == 'cub':
            t_tire_deg = (tire_pars[tire_compound]['k_0']
            +tire_pars[tire_compound]['k_1_cub']* temp_laps
            +tire_pars[tire_compound]['k_2_cub']*math.pow(temp_laps,2)
            +tire_pars[tire_compound]['k_3_cub']*math.pow(temp_laps,3))

        else:
            t_tire_deg = (tire_pars[tire_compound]['k_0']
            +tire_pars[tire_compound]['k_1_ln']
            *math.log(tire_pars[tire_compound]['k_2_ln']
            *temp_laps +1.0))
    return t_tire_deg