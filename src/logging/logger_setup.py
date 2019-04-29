from src.logging.eventsCenter import *
from src.utils.misc_fcts import replace_in_dicts
from src.utils.filesManager import get_dflt_entry
import logging
import logging.config


class CustomLoggerSetup:

    def __init__(self, event_center=None, loggers_capture_events="all", cfg_file=None):
        self.cfg_file = cfg_file if cfg_file else get_dflt_entry("dflt_logger")
        self.curr_cfg = {}
        self.setup_from_yaml(self.cfg_file)
        self.event_center = self.setup_event_center(loggers_capture_events) if event_center is None else event_center

    def setup_from_yaml(self, file):
        import yaml
        with open(file, 'r') as f:
            cfg_dic = yaml.safe_load(f.read())
        self.curr_cfg = cfg_dic
        logging.config.dictConfig(cfg_dic)

    def setup_event_center(self, which_loggers):
        if which_loggers == "all":
            loggers = self.get_all_loggers()
        elif isinstance(which_loggers, str):
            loggers = [which_loggers]
        else:
            loggers = which_loggers
        loggers_obj = [logging.getLogger(log_name) for log_name in loggers]
        return EventsCenter(loggers_obj)

    def change_cfg_values(self, key, new_val):
        replace_in_dicts(self.curr_cfg, key, new_val)

    def get_all_loggers(self):
        return self.curr_cfg.get('loggers', {}).keys()

    def get_event_center(self):
        return self.event_center

    def __str__(self):
        # return f"Logger using cfg {self.cfg_file}\nmaintaining {self.event_center}"
        return f"Logger using cfg {self.cfg_file}"


if __name__ == "__main__":
    l = CustomLoggerSetup()
    print(l)
    logging.getLogger("control").debug("Debugging logger")
