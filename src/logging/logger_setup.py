from src.logging.eventsCenter import *
from src.utils.misc_fcts import replace_in_dicts
from src.utils.filesManager import get_dflt_entry
import logging
import logging.config


class CustomLoggerSetup:

    def __init__(self, event_center=None, loggers_capture_events="all",
                 cfg_file=None, fct_modify_loggers=None):

        self.cfg_file = cfg_file if cfg_file else get_dflt_entry("dflt_logger")
        self.curr_cfg = {}
        fct_modify_loggers = self.cfg_to_defaults if fct_modify_loggers is None else fct_modify_loggers
        self.setup_from_yaml(self.cfg_file, fct_modify_loggers=fct_modify_loggers)
        self.event_center = self.setup_event_center(loggers_capture_events) if event_center is None else event_center

    def setup_from_yaml(self, file, fct_modify_loggers=lambda cfg_dic: cfg_dic):
        import yaml
        with open(file, 'r') as f:
            cfg_dic = yaml.safe_load(f.read())
        self.curr_cfg = fct_modify_loggers(cfg_dic)
        logging.config.dictConfig(cfg_dic)

    def cfg_to_defaults(self, loaded_cfg):
        general_logs = get_dflt_entry("logs", suffix='general_logs.log')
        replace_in_dicts(loaded_cfg, 'genfile', lambda handler: handler.__setitem__('filename', general_logs))
        event_logs = get_dflt_entry("logs", suffix='events.log')
        replace_in_dicts(loaded_cfg, 'eventfile', lambda handler: handler.__setitem__('filename', event_logs))
        return loaded_cfg

    def get_all_loggers(self):
        return self.curr_cfg.get('loggers', {}).keys()

    def setup_event_center(self, which_loggers):
        if which_loggers == "all":
            loggers = self.get_all_loggers()
        elif isinstance(which_loggers, str):
            loggers = [which_loggers]
        else:
            loggers = which_loggers
        loggers_obj = [logging.getLogger(log_name) for log_name in loggers]
        return EventsCenter(loggers_obj)

    def get_event_center(self):
        return self.event_center

    def __str__(self):
        return f"LoggerSetup using cfg {self.cfg_file}"


if __name__ == "__main__":
    l = CustomLoggerSetup()
    print(l)
    logging.getLogger("control").debug("Debugging logger")
