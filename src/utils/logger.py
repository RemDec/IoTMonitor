import logging
import logging.config
from utils.misc_fcts import replace_in_dicts


class Logger:

    def __init__(self, cfg_file=None):
        self.cfg_file = cfg_file if cfg_file else "default_logger.yaml"
        self.setup_from_yaml(self.cfg_file)
        self.curr_cfg = {}

    def setup_from_yaml(self, file):
        import yaml
        with open(file, 'r') as f:
            cfg_dic = yaml.safe_load(f.read())
        print(cfg_dic)
        self.curr_cfg = cfg_dic
        logging.config.dictConfig(cfg_dic)

    def change_cfg_values(self, key, new_val):
        replace_in_dicts(self.curr_cfg, key, new_val)

    def __str__(self):
        return f"Logger using cfg {self.cfg_file}"


if __name__ == "__main__":
    l = Logger()
    print(l)
    logging.getLogger("control").debug("Debugging logger")