
import yaml


class Config:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    @staticmethod
    def load(path: str) -> 'Config':
        with open(path) as rf:
            Config.__shared_state = yaml.load(rf)
        return Config()
