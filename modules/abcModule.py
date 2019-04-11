import abc
import logging

logging.basicConfig(level=logging.DEBUG)


class Module(abc.ABC):

    @abc.abstractmethod
    def get_description(self):
        pass

    @abc.abstractmethod
    def get_module_id(self):
        pass

    @abc.abstractmethod
    def set_params(self, params):
        pass

    @abc.abstractmethod
    def launch(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def distrib_output(self, output):
        pass

    @abc.abstractmethod
    def is_active(self):
        pass