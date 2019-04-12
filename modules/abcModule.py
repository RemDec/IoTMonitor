import abc
import logging

logging.basicConfig(level=logging.DEBUG)


class Module(abc.ABC):

    @abc.abstractmethod
    def get_description(self):
        # A short description of module activity and purpose
        pass

    @abc.abstractmethod
    def get_module_id(self):
        # A short string (should be unique among all available modules)
        pass

    @abc.abstractmethod
    def get_cmd(self):
        # executable command referring real program underlying module abstraction (nmap, ping, ...)
        pass

    @abc.abstractmethod
    def get_params(self):
        # Tuple of dicts describing program parameters (used_params, defaults, desc) where
        # -used_params is the dict mapping param_name -> value really passed to cmd at exec time
        # -defaults dict mapping param_name -> (defaultValue, isMandatory, prefix_or_cmd_flag)
        # -desc provides textual information for each param param_name -> description_string
        pass

    @abc.abstractmethod
    def set_params(self, params):
        # Dict of params used by the module cmd in CLI at launching (used_param above)
        pass

    @abc.abstractmethod
    def launch(self):
        # A call to this should start cmd execution with current used_params as CLI arguments
        # that should occurs in a thread using distrib_output as an user-defined callback function to
        # parse output of the cmd program process. Pre-defined thread managers available in sub-classes
        pass

    @abc.abstractmethod
    def stop(self):
        # Should terminate all cmd current threads
        pass

    @abc.abstractmethod
    def distrib_output(self, output):
        # Callback function that should process output of cmd : parsing, translation to application
        # element like netmap new entry/modif, threat logging and alerting
        pass

    @abc.abstractmethod
    def is_active(self):
        # How a module is classified depending cmd workflow : actives correspond to script execution
        # with unique output at end, passives are processes constantly running in background feeding
        # an output stream with collected information to read and work on
        pass

