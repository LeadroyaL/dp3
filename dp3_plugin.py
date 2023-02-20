from abc import ABCMeta, abstractmethod


class Dp3Plugin(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def plugin_entry(*_argv: str):
        pass

    @staticmethod
    def help():
        print("No help information")
