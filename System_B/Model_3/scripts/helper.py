import os
import yaml


def get_experiment_dirs():
    abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(abspath, 'config.yml')

    with open(config_path) as c:
        config = yaml.safe_load(c)
    abspath = os.path.split(config_path)[0]

    dirs = {k: os.path.join(abspath, v) for k, v in config.items()}

    return dirs
