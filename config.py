import os
import yaml

class ConfigMember(dict):
    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            value = ConfigMember(value)
        return value

class Config(dict):
    def __init__(self, file_path):
        assert os.path.exists(file_path), "ERROR: Config File doesn't exist."
        with open(file_path, 'r') as f:
            self.member = yaml.load(f)
            f.close()

    def __getattr__(self, name):
        if name not in self.member:
            return False
        value = self.member[name]
        if isinstance(value, dict):
            value = ConfigMember(value)
        return value
