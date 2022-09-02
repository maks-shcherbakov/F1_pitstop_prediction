from cmath import isclose
from tkinter import N
import numpy as np
import helpers.src.tire_degradation_model
import math
def calc_racetimes_basic(t_base: float,
                         tot_no_laps: int,
                         t_lap_sens_mass: float,
                         t_pitdrive_inlap: float,
                         t_pitdrive_outlap: float,
                         t_pit_tirechange: float,
                         pits_aft_finishline: bool,
                         tire_pars: dict,
                         p_grid: int,
                         t_loss_pergridpos: float,
                         t_loss_firstlap: float,
                         strategy: list,
                         drivetype: str,
                         m_fuel_init: float,
                         b_fuel_perlap: float,
                         t_pit_refuel_perkg: float,
                         t_pit_charge_perkwh: float,
                         t_pitdrive_inlap_fcy: float = None,
                         t_pitdrive_outlap_fcy: float = None,
                         t_pitdrive_inlap_sc: float = None,
                         t_pitdrive_outlap_sc: float = None,
                         fcy_phases: list = None,
                         t_lap_sc: float = None,
                         t_lap_fcy: float = None)-> tuple:


    if len(strategy) == 0: 
        raise RuntimeError('Start Compound info not provided')
    elif len(strategy) == 1:
        print('No pitstop is given in the strategy data')

    if not all([len(x) == 4 for x in strategy]): 
        raise RuntimeError('Inserted strategy data does not contain [inlap,compound,age,refuelling] for all pitstops')

    if not all(x[0] < y[0] for x, y in zip(strategy,strategy[1:])): 
        raise RuntimeError('The inlaps are not soted in the rissing order')

    if drivetype=='combustion': 
        if m_fuel_init is None or b_fuel_perlap is None: 
            raise RuntimeError('Parameters m_fuel_init and b_fuel_perlap are required for a combustion car!')
    elif drivetype == 'electric':
        pass
    else: 
        raise RuntimeError('Unknown drivetype')

    if any(x[3] != 0.0 for x in strategy):
        if drivetype == 'combustion' and t_pit_refuel_perkg is None:
            raise RuntimeError('Refueling is set but t_pit_refuel_perkg is not set!')
        elif drivetype == 'electric' and t_pit_charge_perkwh is not None:
            raise RuntimeError('Recharging is set but t_pit_charge_perkwh is not set!')


    if fcy_phases is not None and (t_lap_fcy is None or t_lap_sc is None):
        print("WARNING: t_lap_fcy and t_lap_sc are required if fcy_phases is not None! Using 140% and 160% of the"
              " base lap time instead!")
        t_lap_fcy = t_base * 1.4
        t_lap_sc = t_base * 1.6

    if fcy_phases is not None and any(False if x[2] in ['SC', 'VSC'] else True for x in fcy_phases):
        raise RuntimeError("Unknown FCY phase type!")

    if fcy_phases is not None and not all([x[0] < y[0] for x, y in zip(fcy_phases, fcy_phases[1:])]):
        raise RuntimeError('The given FCY phases are not sorted in a rising order!')


    if fcy_phases is not None \
            and (t_pitdrive_inlap_fcy is None or t_pitdrive_outlap_fcy is None
                 or t_pitdrive_inlap_sc is None or t_pitdrive_outlap_sc is None):
        raise RuntimeError("t_pitdrive_inlap_fcy/sc and t_pitdrive_outlap_fcy/sc must all be supplied if there are FCY"
                           " phases to consider!")


    if fcy_phases is not None:
        for idx_phase in range(len(fcy_phases)):
            if fcy_phases[idx_phase][1] > float(tot_no_laps):
                print("WARNING: Inserted FCY phase ends after the last lap of the race, reducing it to end with the"
                      " final lap!")
                fcy_phases[idx_phase][1] = float(tot_no_laps)

    
    t_laps = np.ones(tot_no_laps) * t_base 

    if drivetype == 'combustion':
        t_laps+= (m_fuel_init - b_fuel_perlap * np.arange(0,tot_no_laps)) * t_lap_sens_mass

    t_laps[0] += t_loss_firstlap + (p_grid - 1) * t_loss_pergridpos

    for idx in range(len(strategy)):
        cur_inlap = strategy[idx][0]

        if idx + 1 < len(strategy):
            len_cur_stint = strategy[idx + 1][0] - cur_inlap
        else:
            len_cur_stint = tot_no_laps - cur_inlap

        comp_cur_stint = strategy[idx][1]
        age_cur_stint = strategy[idx][2]

        t_laps[cur_inlap:cur_inlap + len_cur_stint] += helpers.src.tire_degradation_model.\
            tire_degradation_model(tire_age_start=age_cur_stint,
                                    stint_time=len_cur_stint,
                                    tire_compound=comp_cur_stint,
                                    tire_pars=tire_pars)

        if cur_inlap < tot_no_laps:
            t_laps[cur_inlap] += tire_pars['t_add_coldtires']

    t_laps_pit = np.zeros(tot_no_laps)


    if fcy_phases is not None:
        t_pit_before_fcy_start_end = [[0.0,0.0]] * len(fcy_phases)

    else:
        t_pit_before_fcy_start_end =None

    if pits_aft_finishline:
        lap_fraction_pit_inlap = 0.01
        lap_fraction_pit_outlap = 0.05
    else:
        lap_fraction_pit_inlap = 0.05
        lap_fraction_pit_outlap = 0.01

    for idx in range(len(strategy)):
        cur_inlap = strategy[idx][0]

        if cur_inlap == 0:
            continue

        t_pit_inlap=0.0

        if not pits_aft_finishline:
            t_pit_inlap += __perform_pitstop_standstill(t_pit_tirechange=t_pit_tirechange,
                                                        drivetype=drivetype,
                                                        cur_stop=strategy[idx],
                                                        t_pit_refuel_perkg=t_pit_refuel_perkg,
                                                        t_pit_charge_perkwh=t_pit_charge_perkwh)
                            
        if fcy_phases is not None:
            cur_phase  = next((x for x in fcy_phases 
                                if x[0] <= cur_inlap - lap_fraction_pit_inlap and cur_inlap <= x[1]), None)
        else: cur_phase = None

        if cur_phase is None:
            t_pit_inlap+= t_pitdrive_inlap
        elif cur_phase[2] == 'SC':
            if cur_phase[0] < cur_inlap -1.0:
                t_pit_inlap+= t_pitdrive_inlap_sc
            else: 
                t_pit_inlap+= t_pitdrive_inlap_fcy
        elif cur_phase[2] == 'VSC':
            t_pit_inlap+=t_pitdrive_inlap_fcy
        else:
            raise RuntimeError('Unknown FCY phase !')

        t_laps_pit[cur_inlap - 1] += t_pit_inlap

        if cur_inlap >= tot_no_laps:
            continue

        t_pit_outlap = 0.0

        if pits_aft_finishline:
            t_pit_outlap += __perform_pitstop_standstill(t_pit_tirechange=t_pit_tirechange, 
                                                        drivetype=drivetype,
                                                        cur_stop=strategy[idx],
                                                        t_pit_refuel_perkg=t_pit_refuel_perkg,
                                                        t_pit_charge_perkwh=t_pit_charge_perkwh)

        if fcy_phases is not None:
            cur_phase = next((x for x in fcy_phases 
                            if x[0] <= cur_inlap and cur_inlap + lap_fraction_pit_outlap <=x[1]), None)
        else: 
            cur_phase=None

        if cur_phase is None:
            t_pit_outlap += t_pitdrive_outlap
        elif cur_phase[2] == 'SC':
            if cur_phase[0]< cur_inlap - 1.0:
                t_pit_outlap += t_pitdrive_outlap_sc
            else:
                t_pit_outlap += t_pitdrive_outlap_fcy
        elif cur_phase[2] == 'VSC':
            t_pit_outlap += t_pitdrive_outlap_fcy
        else:
            raise RuntimeError('Unknown FCY phase')

        t_laps_pit[cur_inlap] += t_pit_outlap

        if fcy_phases is not None:
            for idx_fcy_phase , cur_phase in enumerate(fcy_phases):
                if cur_inlap + lap_fraction_pit_outlap < cur_phase[0] < cur_inlap + 1.0:
                    t_pit_before_fcy_start_end[idx_fcy_phase][0] += t_pit_outlap

                if math.isclose(cur_phase[1],cur_inlap):
                    t_pit_before_fcy_start_end[idx_fcy_phase][1] += t_pit_inlap

                elif cur_inlap + lap_fraction_pit_outlap < cur_phase[1] < cur_inlap + 1.0:
                    t_pit_before_fcy_start_end[idx_fcy_phase][1] += t_pit_outlap

    if fcy_phases is not None:
        fcy_phases_conv = [[None, None, x[2], None, None] for x in fcy_phases]

        for idx_phase, cur_phase in enumerate(fcy_phases):
            start_idx = math.floor(cur_phase[0])
            stop_idx = math.ceil(cur_phase[1])

            for idx_lap in range(start_idx, stop_idx):

                cur_progress = float(idx_lap)

                if cur_progress <= cur_phase[0]:
                    lap_frac_normal_bef = cur_phase[0] - cur_progress

                if cur_progress + 1.0 >= cur_phase[1]:
                    lap_frac_normal_aft = cur_progress + 1.0 - cur_progress[1]
                else:
                    lap_frac_normal_aft = 0.0

                lap_frac_normal = lap_frac_normal_bef + lap_frac_normal_aft
                lap_frac_slow = 1.0 - lap_frac_normal

                t_lap_slow = t_lap_fcy

                fcy_phases_conv[idx_phase][0] = (np.sum(t_laps[:idx_lap] + t_laps_pit[:idx_lap])
                                                + lap_frac_normal_bef * t_laps[idx_lap]
                                                + t_pit_before_fcy_start_end[idx_phase][0])

                if cur_progress + 1.0 >= cur_phase[1]:
                    if math.isclose(cur_phase[1], tot_no_laps):
                        fcy_phases_conv[idx_phase][1] = math.inf
                    else:
                        fcy_phases_conv[idx_phase][1] = fcy_phases_conv[idx_phase][0] + lap_frac_slow * t_lap_slow

                elif cur_progress +1.0 >= cur_phase[1]:

                    if cur_phase[2] == 'SC' :
                        lap_frac_normal = 0.0
                        lap_frac_slow = 1.0
                        t_lap_slow = t_lap_sc
                    else:
                        lap_frac_normal =cur_progress +1.0 - cur_phase[1]
                        lap_frac_slow = 1.0 - lap_frac_normal
                        t_lap_slow = t_lap_fcy

                    if math.isclose(cur_phase[1],tot_no_laps):
                        fcy_phases_conv[idx_phase][1] = math.inf 
                    else:
                        fcy_phases_conv[idx_phase][1] = (np.sum(t_laps[:idx_lap] + t_laps_pit[:idx_lap])
                                                        + lap_frac_slow * t_lap_slow
                                                        + t_pit_before_fcy_start_end[idx_phase][1])
                else: 
                    lap_frac_normal = 0.0
                    lap_frac_slow = 1.0 


                    if cur_phase[2] == 'SC':
                        t_lap_slow = t_lap_sc
                    else:
                        t_lap_slow = t_lap_fcy

            if cur_phase[2] == 'SC':
                t_race_sc_start = np.sum(t_laps[:start_idx + 1] + t_laps_pit[:start_idx +1])
                fcy_phases_conv[idx_phase][3] = t_race_sc_start - fcy_phases_conv[idx_phase][0]

                if fcy_phases_conv[idx_phase][3] < 0.33 * t_lap_sc:

                    t_sc_delay_diff = 0.33 * t_lap_sc - fcy_phases_conv[idx_phase][3]

                    fcy_phases_conv[idx_phase][3] += t_sc_delay_diff
                    fcy_phases_conv[idx_phase][1] += t_sc_delay_diff
                    if start_idx + 1 < tot_no_laps:
                        t_laps[start_idx+1] += t_sc_delay_diff

                if math.isclose(cur_phase[1],tot_no_laps):
                    fcy_phases_conv[idx_phase][4] = math.inf
                else:
                    fcy_phases_conv[idx_phase][4] = stop_idx - start_idx - 1

    else:
        fcy_phases_conv = None

    t_race_lapwise = np.cumsum(t_laps + t_laps_pit)

    return t_race_lapwise, fcy_phases_conv

def __perform_pitstop_standstill(t_pit_tirechange: float, drivetype: str, cur_stop: list, t_pit_refuel_perkg: float,
                                t_pit_charge_perkwh: float) -> float:

    timeloss_standstill = t_pit_tirechange

    if drivetype == ' combustion' \
            and cur_stop[3] != 0.0 \
            and cur_stop[3] * t_pit_refuel_perkg > timeloss_standstill:
        timeloss_standstill = cur_stop[3] * t_pit_refuel_perkg

    elif drivetype == 'electric' \
            and cur_stop[3] != 0.0 \
            and cur_stop[3] * t_pit_charge_perkwh > timeloss_standstill:
        timeloss_standstill = cur_stop[3] * t_pit_charge_perkwh

    return timeloss_standstill
    

                
            







