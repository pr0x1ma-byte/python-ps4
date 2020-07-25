import configparser, os
from pathlib import Path


class ConfigMixin:
    def __init__(self):
        self.name = '.python-ps4.ini'
        self.config = configparser.ConfigParser()

    def load(self):
        home = str(Path.home())
        file_path = os.path.join(home, self.name)
        if not os.path.exists(file_path):
            self.config['DEFAULT'] = {'ip': ' ', 'port': 997, 'credential': ' ', 'log_level': 'ERROR'}
            with open(os.path.join(home, self.name), 'w') as file:
                self.config.write(file)
                return

        self.config.read(file_path)
