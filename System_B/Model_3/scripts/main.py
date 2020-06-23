import helper
import preprocessing
import optimization
import postprocessing
import plotting


if __name__ == '__main__':
    scenario_assumptions = helper.get_scenario_assumptions()

    selected_id = scenario_assumptions.index

    for i in selected_id:
        print(f"Running scenario {i} with the name '{scenario_assumptions.loc[i]['name']}'")

        preprocessing.main(**scenario_assumptions.loc[i])

        optimization.main(**scenario_assumptions.loc[i])

        postprocessing.main(**scenario_assumptions.loc[i])

        plotting.main(**scenario_assumptions.loc[i])
