import logging
import logging.config
from src.utils.misc_fcts import replace_in_dicts
from src.utils.filesManager import get_dflt_entry


class Logger:

    def __init__(self, cfg_file=None):
        self.cfg_file = cfg_file if cfg_file else get_dflt_entry("dflt_logger")
        self.setup_from_yaml(self.cfg_file)
        self.curr_cfg = {}
        logging.getLogger("threat").register_threat_event = self.register_threat_event

    def setup_from_yaml(self, file):
        import yaml
        with open(file, 'r') as f:
            cfg_dic = yaml.safe_load(f.read())
        self.curr_cfg = cfg_dic
        logging.config.dictConfig(cfg_dic)

    def change_cfg_values(self, key, new_val):
        replace_in_dicts(self.curr_cfg, key, new_val)

    def register_threat_event(self, threat):
        print("Threat registred :", threat)

    def __str__(self):
        return f"Logger using cfg {self.cfg_file}"


if __name__ == "__main__":
    l = Logger()
    print(l)
    logging.getLogger("control").debug("Debugging logger")
    logging.getLogger("threat").register_threat_event("ALLO")
