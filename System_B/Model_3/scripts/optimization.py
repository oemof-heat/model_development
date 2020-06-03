import logging
import os
import yaml

from oemof.solph import EnergySystem, Model

# DONT REMOVE THIS LINE!
from oemof.tabular import datapackage  # noqa
from oemof.tabular.facades import TYPEMAP

from helper import get_experiment_dirs


def optimize(input_data_dir, results_data_dir, solver='cbc', save_lp=False):
    r"""
    Takes the specified datapackage, creates an energysystem and solves the
    optimization problem.
    """
    # create energy system object
    logging.info("Creating EnergySystem from datapackage")
    es = EnergySystem.from_datapackage(
        os.path.join(input_data_dir, "datapackage.json"),
        attributemap={}, typemap=TYPEMAP,
    )

    # create model from energy system (this is just oemof.solph)
    logging.info("Creating the optimization model")
    m = Model(es)

    # if you want dual variables / shadow prices uncomment line below
    # m.receive_duals()

    # save lp file together with optimization results
    if save_lp:
        lp_file_dir = os.path.join(results_data_dir, 'model.lp')
        logging.info(f"Saving the lp-file to {lp_file_dir}")
        m.write(lp_file_dir, io_options={'symbolic_solver_labels': True})

    # select solver 'gurobi', 'cplex', 'glpk' etc
    logging.info(f'Solving the problem using {solver}')
    m.solve(solver=solver)

    # get the results from the the solved model(still oemof.solph)
    es.results = m.results()

    # now we use the write results method to write the results in oemof-tabular
    # format
    logging.info(f'Writing the results to {results_data_dir}')
    es.dump(results_data_dir)


def main():
    logging.info('Optimisation')

    dirs = get_experiment_dirs()

    optimize(dirs['preprocessed'], dirs['optimised'])


if __name__ == '__main__':
    main()
