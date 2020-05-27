import os
import yaml


def read_config(config_path):
    with open(config_path) as c:
        config = yaml.safe_load(c)
    abspath = os.path.split(config_path)[0]

    dirs = {k: os.path.join(abspath, v) for k, v in config.items()}

    return dirs
