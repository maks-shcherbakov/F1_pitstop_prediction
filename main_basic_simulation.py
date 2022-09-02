from matplotlib.style import available
import numpy as np
import itertools
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import racesim_basic
import os
import pkg_resources
import helpers.src.tire_degradation_model

repo_path_ = os.path.dirname(os.path.abspath(__file__))

requirements_path = os.path.join(repo_path_,'requirements.txt')
dependencies =[]

with open(requirements_path, 'r') as fh_:
    line = fh_.readline()

    while line:
        dependencies.append(line.rstrip())
        line = fh_.readline()

pkg_resources.require(dependencies)

def main(sim_opts: dict, pars_in: dict) -> tuple:
    strategy_combinations = helpers.src.compound_combinations.\
        compound_combinations(available_compounds=pars_in['available_compounds'],
                            min_no_pitstops = sim_opts["min_no_pitstops"],
                            max_no_pitstops=sim_opts["max_no_pitstops"],
                            enforce_diff_compounds=sim_opts["enforce_diff_compounds"],
                            start_compound=sim_opts["start_compound"],
                            all_orders=False)


    exit_qp = False
    t_race_fastest = {}
    t_race_full_factorial = {}

    if sim_opts["use_qp"]:
        for cur_no_pitstops in range(sim_opts["min_no_pitstops"],sim_opts["max_no_pitstops"]+ 1):
            t_race_fastest[cur_no_pitstops] = []

            for cur_comp_strat in strategy_combinations[cur_no_pitstops]:
                tires = [[comp,0] for comp in cur_comp_strat]
                tires[0][1] = sim_opts["start_age"]

                opt_stint_lengths = racesim_basic .src.opt_strategy_basic. \
                    opt_strategy_basic(tot_no_laps = pars_in['race_pars']['tot_no_laps'],
                    tire_pars=pars_in['driver_pars']['tire_pars'],
                    tires=tires)

                if opt_stint_lengths is None:
                    print("Could not colve the quadratic problem,moving to full factorial")
                    exit_qp = True
                    t_race_fastest = {}
                    break

                laps_tmp=0
                strategy=[]
                strategy_stints = []

                for i in range(cur_no_pitstops+1):
                    strategy.append([laps_tmp],
                                    tires[i][0],
                                    tires[i][1],
                                    0.0)
                    strategy_stints.extend([opt_stint_lengths[i],tires[i][0]])
                    laps_tmp += opt_stint_lengths[i]

                t_race_tmp = racesim_basic.src.calc_racetimes_basic.  \
                    calc_racetimes_basic(t_base=pars_in['driver_pars']["t_base"],
                                         tot_no_laps=pars_in['race_pars']["tot_no_laps"],
                                         t_lap_sens_mass=pars_in['track_pars']["t_lap_sens_mass"],
                                         t_pitdrive_inlap=pars_in['track_pars']["t_pitdrive_inlap"],
                                         t_pitdrive_outlap=pars_in['track_pars']["t_pitdrive_outlap"],
                                         t_pitdrive_inlap_fcy=pars_in['track_pars']["t_pitdrive_inlap_fcy"],
                                         t_pitdrive_outlap_fcy=pars_in['track_pars']["t_pitdrive_outlap_fcy"],
                                         t_pitdrive_inlap_sc=pars_in['track_pars']["t_pitdrive_inlap_sc"],
                                         t_pitdrive_outlap_sc=pars_in['track_pars']["t_pitdrive_outlap_sc"],
                                         t_pit_tirechange=pars_in['driver_pars']["t_pit_tirechange"],
                                         pits_aft_finishline=pars_in['track_pars']["pits_aft_finishline"],
                                         tire_pars=pars_in['driver_pars']["tire_pars"],
                                         p_grid=pars_in['driver_pars']["p_grid"],
                                         t_loss_pergridpos=pars_in['track_pars']["t_loss_pergridpos"],
                                         t_loss_firstlap=pars_in['track_pars']["t_loss_firstlap"],
                                         strategy=strategy,
                                         drivetype=pars_in['driver_pars']["drivetype"],
                                         m_fuel_init=pars_in['driver_pars']["m_fuel_init"],
                                         b_fuel_perlap=pars_in['driver_pars']["b_fuel_perlap"],
                                         t_pit_refuel_perkg=pars_in['driver_pars']["t_pit_refuel_perkg"],
                                         t_pit_charge_perkwh=pars_in['driver_pars']["t_pit_charge_perkwh"],
                                         fcy_phases=None,
                                         t_lap_sc=pars_in['track_pars']["t_lap_sc"],
                                         t_lap_fcy=pars_in['track_pars']["t_lap_fcy"])[0][-1]

                t_race_fastest[cur_no_pitstops].append([tuple(strategy_stints), t_race_tmp])

            if exit_qp:
                break

        if not exit_qp:
            for cur_no_pitstops in t_race_fastest:
                t_race_fastest[cur_no_pitstops] = sorted(t_race_fastest[cur_no_pitstops],key=lambda x: x[1])


    if not sim_opts["use_qp"] or exit_qp:
        for cur_no_pitstops in range(sim_opts['min_no_pitstops'], sim_opts['max_no_pitstops']+1):
            t_race_template = np.zeros((pars_in['race_pars']['tot_no_laps'] - 1,) * cur_no_pitstops)
            t_race_full_factorial[cur_no_pitstops] = {cur_comp_strat: np.copy(t_race_template)
                                                    for cur_comp_strat in strategy_combinations[cur_no_pitstops]}

            for cur_comp_strat in t_race_full_factorial[cur_no_pitstops]:
                for idxs_cur_inlaps in itertools.product(range(pars_in['race_pars']['tot_no_laps'] - 1),
                                                        repeat=cur_no_pitstops):
                    if not all([x < y for x,y in zip(idxs_cur_inlaps, idxs_cur_inlaps[1:])]):
                        t_race_full_factorial[cur_no_pitstops][cur_comp_strat][idxs_cur_inlaps] = np.nan
                        continue

                    strategy = [[0, cur_comp_strat[0], sim_opts['start_age'], 0.0]]

                    for i in range(cur_no_pitstops):
                        strategy.append([idxs_cur_inlaps[i] + 1, 
                                        cur_comp_strat[i + 1], 
                                        0,
                                        0.0])


                    t_race_full_factorial[cur_no_pitstops][cur_comp_strat][idxs_cur_inlaps] = racesim_basic.src.\
                        calc_racetimes_basic.calc_racetimes_basic(t_base=pars_in['driver_pars']["t_base"],
                                                                  tot_no_laps=pars_in['race_pars']["tot_no_laps"],
                                                                  t_lap_sens_mass=pars_in['track_pars'][
                                                                      "t_lap_sens_mass"],
                                                                  t_pitdrive_inlap=pars_in['track_pars'][
                                                                      "t_pitdrive_inlap"],
                                                                  t_pitdrive_outlap=pars_in['track_pars'][
                                                                      "t_pitdrive_outlap"],
                                                                  t_pitdrive_inlap_fcy=pars_in['track_pars'][
                                                                      "t_pitdrive_inlap_fcy"],
                                                                  t_pitdrive_outlap_fcy=pars_in['track_pars'][
                                                                      "t_pitdrive_outlap_fcy"],
                                                                  t_pitdrive_inlap_sc=pars_in['track_pars'][
                                                                      "t_pitdrive_inlap_sc"],
                                                                  t_pitdrive_outlap_sc=pars_in['track_pars'][
                                                                      "t_pitdrive_outlap_sc"],
                                                                  pits_aft_finishline=pars_in['track_pars'][
                                                                      "pits_aft_finishline"],
                                                                  t_pit_tirechange=pars_in['driver_pars'][
                                                                      "t_pit_tirechange"],
                                                                  tire_pars=pars_in['driver_pars']["tire_pars"],
                                                                  p_grid=pars_in['driver_pars']["p_grid"],
                                                                  t_loss_pergridpos=pars_in['track_pars'][
                                                                      "t_loss_pergridpos"],
                                                                  t_loss_firstlap=pars_in['track_pars'][
                                                                      "t_loss_firstlap"],
                                                                  strategy=strategy,
                                                                  drivetype=pars_in['driver_pars']["drivetype"],
                                                                  m_fuel_init=pars_in['driver_pars']["m_fuel_init"],
                                                                  b_fuel_perlap=pars_in['driver_pars']["b_fuel_perlap"],
                                                                  t_pit_refuel_perkg=pars_in['driver_pars'][
                                                                      "t_pit_refuel_perkg"],
                                                                  t_pit_charge_perkwh=pars_in['driver_pars'][
                                                                      "t_pit_charge_perkwh"],
                                                                  fcy_phases=sim_opts["fcy_phases"],
                                                                  t_lap_sc=pars_in['track_pars']["t_lap_sc"],
                                                                  t_lap_fcy=pars_in['track_pars']["t_lap_fcy"])[0][-1]
                    
        for cur_no_pitstops in t_race_full_factorial:
            t_race_fastest[cur_no_pitstops] = []

            for cur_comp_strat in t_race_full_factorial[cur_no_pitstops]:

                idx_tmp = np.nanargmin(t_race_full_factorial[cur_no_pitstops][cur_comp_strat])

                opt_inlap_idxs = np.unravel_index(idx_tmp, t_race_full_factorial[cur_no_pitstops][cur_comp_strat].shape)

                laps_tmp = 0
                opt_stint_lengths = []

                for i in range(cur_no_pitstops):
                    opt_stint_lengths.append(opt_inlap_idxs[i] + 1 - laps_tmp)
                    laps_tmp += opt_stint_lengths[-1]

                opt_stint_lengths.append(pars_in['race_pars']['tot_no_laps'] - laps_tmp)

                strategy_stints = []

                for tmp in zip(opt_stint_lengths, cur_comp_strat):
                    strategy_stints.extend(list(tmp))

                t_race_tmp = t_race_full_factorial[cur_no_pitstops][cur_comp_strat][opt_inlap_idxs]

                t_race_fastest[cur_no_pitstops].append([tuple(strategy_stints), t_race_tmp])

        for cur_no_pitstops in t_race_fastest:
            t_race_fastest[cur_no_pitstops] = sorted(t_race_fastest[cur_no_pitstops], key=lambda x:x[1])

    return t_race_fastest, t_race_full_factorial


if __name__ == '__main__':

    race_pars_file_ = "pars_YasMarina_2017.ini"
    simple_format_ = True
    driver_initials_ = ""

    sim_opts_ = {"min_no_pitstops": 1,
                 "max_no_pitstops": 2,
                 "start_compound": None,
                 "start_age": 0,
                 "enforce_diff_compounds": True,
                 "use_qp": False,
                 "fcy_phases": None}


    use_plot = True
    use_print = True
    use_print_result = True

    if simple_format_:
        pars_in_ = racesim_basic.src.import_pars.import_pars(use_print=use_print, race_pars_file=race_pars_file_)
    else:
        pars_in_ = racesim_basic.src.import_pars.import_ext_params(use_print=use_print, 
                                                                    race_pars_file=race_pars_file_,
                                                                    driver_initials=driver_initials_)

    racesim_basic.src.check_pars.check_pars(sim_opts=sim_opts_, pars_in = pars_in_,use_plot=use_plot)

    t_start = time.perf_counter()

    t_race_fastest_, t_race_full_factorial_ = main(sim_opts=sim_opts_,pars_in=pars_in_)

    if use_print:
        print('Calculation time: %.3fs' % (time.perf_counter() - t_start))

    if use_print_result:
        print('Printing stint length of inlaps(order is not relevant)')

        for cur_no_pitstops_, strategies_cur_no_pitstops in t_race_fastest_.items():
            print('Race times for %i stop strategies:' % cur_no_pitstops_)

            for strategy_ in strategies_cur_no_pitstops:
                print_string = ''

                for entry in strategy_[0]:
                    print_string += str(entry) + ' '

                print(print_string + ': %.3fs' % strategy_[1])

    if use_plot:

        stint_length = 25

        t_c1_degr = helpers.src.tire_degradation_model. \
            tire_degradation_model(tire_age_start=0,
                                    stint_time=stint_length,
                                    tire_compound=pars_in_['available_compounds'][0], 
                                    tire_pars=pars_in_['driver_pars']['tire_pars'])

        t_c2_degr = helpers.src.tire_degradation_model. \
            tire_degradation_model(tire_age_start=0,
                                    stint_time=stint_length,
                                    tire_compound=pars_in_['available_compounds'][1], 
                                    tire_pars=pars_in_['driver_pars']['tire_pars'])

        t_c3_degr = helpers.src.tire_degradation_model. \
            tire_degradation_model(tire_age_start=0,
                                    stint_time=stint_length,
                                    tire_compound=pars_in_['available_compounds'][2], 
                                    tire_pars=pars_in_['driver_pars']['tire_pars'])

        fig = plt.figure()
        ax = fig.gca()

        laps_tmp_ = np.arange(1, stint_length + 1)
        ax.plot(laps_tmp_, t_c1_degr)
        ax.plot(laps_tmp_, t_c2_degr, 'x-')
        ax.plot(laps_tmp_, t_c3_degr, 'o-')

        x_min = 0
        x_max = laps_tmp_[-1] - 1
        ax.set_xlim(left=x_min, right=x_max)
        plt.hlines((t_c1_degr[0], t_c2_degr[0], t_c3_degr[0]), x_min, x_max, color='grey', linestyle='--')

        plt.legend(pars_in_['available_compounds'])
        plt.title('Tire degradation plot')
        plt.ylabel('(Relative) Time loss in s/lap')
        plt.xlabel('Tire age in laps')

        plt.grid()
        plt.show()

        if not sim_opts_["use_qp"]:
            for cur_comp_strat_ in t_race_full_factorial_[1]:
                fig = plt.figure()
                ax = fig.gca()

                laps_tmp_ = np.arange(1, pars_in_['race_pars']["tot_no_laps"] + 1)
                ax.plot(laps_tmp_[:-1], t_race_full_factorial_[1][cur_comp_strat_])

                t_race_min = np.amin(t_race_full_factorial_[1][cur_comp_strat_])
                plt.title('Current strategy: ' + str(cur_comp_strat_) + '\nMinimum race time: %.3fs' % t_race_min)
                plt.xlabel('Lap of pitstop')
                plt.ylabel('Race time in s')

                plt.grid()
                plt.show()

            for cur_comp_strat_ in t_race_full_factorial_[2]:
                fig = plt.figure()
                ax = fig.gca(projection='3d')

                laps_tmp_ = np.arange(1, pars_in_['race_pars']["tot_no_laps"] + 1)
                x_, y_ = np.meshgrid(laps_tmp_[:-1], laps_tmp_[:-1])  
                ax.plot_wireframe(x_, y_, t_race_full_factorial_[2][cur_comp_strat_])

                t_race_min = np.nanmin(t_race_full_factorial_[2][cur_comp_strat_])
                plt.title('Current strategy: ' + str(cur_comp_strat_) + '\nMinimum race time: %.3fs' % t_race_min)
                plt.ylabel('Lap of first pitstop')
                plt.xlabel('Lap of second pitstop')
                ax.set_zlabel('Race time in s')

                plt.show()

            if sim_opts_["max_no_pitstops"] > 2:
                print('INFO: Plotting of strategies with more than 2 stops is not possible!')               
    
