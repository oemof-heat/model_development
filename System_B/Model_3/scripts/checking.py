import os

from helper import get_experiment_dirs, check_if_csv_dirs_equal


dirs = get_experiment_dirs()

model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

dir_old = os.path.join(model_path, dirs['postprocessed'], '_default', 'all_scenarios')

dir_new = os.path.join(model_path, dirs['postprocessed'], 'all_scenarios')

print(f"Comparing {dir_new} with {dir_old}.")

check_if_csv_dirs_equal(dir_new, dir_old)
