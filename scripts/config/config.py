import os
import json
from copy import deepcopy

CONFIG_FILE_NAME = './config.json'

class Config(object):
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME), 'r') as infile:
            self.config_dict = json.load(infile)

    def get(self, *args, **kwargs):
        default = kwargs.setdefault('default', None)
        data = deepcopy(self.config_dict)
        if not args:
            return data
        else:
            for key in args:
                try:
                    data = data[key]
                except:
                    return default
            return data
