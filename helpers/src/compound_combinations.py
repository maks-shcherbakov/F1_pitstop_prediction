import itertools
from tracemalloc import start

def compound_combinations(available_compounds: list,
                            min_no_pitstops: int = 1,
                            max_no_pitstops: int = 3,
                            enforce_diff_compounds: bool =True,
                            start_compound: str = None,
                            all_orders:bool=False) -> dict:

    strategy_combinations={}

    for cur_no_pitstops in range(min_no_pitstops,max_no_pitstops + 1):
        if not all_orders:
            strategy_combinations[cur_no_pitstops] = \
                list(itertools.combinations_with_replacement(available_compounds,r=cur_no_pitstops + 1))

        else:
            strategy_combinations[cur_no_pitstops] =[strat_tmp for strat_tmp in strategy_combinations[cur_no_pitstops]
                                                    if not len(set(strat_tmp)) == 1]

        if enforce_diff_compounds:
            strategy_combinations[cur_no_pitstops] = [temp_strat for temp_strat in strategy_combinations[cur_no_pitstops]
            if not len(set(temp_strat)) == 1]

        if start_compound:
            strategy_combinations[cur_no_pitstops] = [temp_strat for temp_strat in strategy_combinations[cur_no_pitstops]
            if start_compound in temp_strat]

            for idx_set in range(len(strategy_combinations[cur_no_pitstops])):
                if not strategy_combinations[cur_no_pitstops][idx_set][0] == start_compound:
                    set_list = list(strategy_combinations[cur_no_pitstops][idx_set])
                    idx_start_compound= set_list.index(start_compound)
                    set_list[0],set_list[idx_start_compound] = set_list[idx_start_compound],set_list[0]
                    strategy_combinations[cur_no_pitstops][idx_set] = tuple(set_list)

    return strategy_combinations