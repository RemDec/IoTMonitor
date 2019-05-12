from src.utils.filesManager import *
from src.coreConfig import CoreConfig
import yaml


def config_to_YAML(coreconfig, filepath=get_dflt_entry('configs', 'last_coreconfig.yaml'),
                   XML_path_routine=None, XML_path_netmap=None):
    vals = {}
    cfgpaths = coreconfig.paths

    for key, val in cfgpaths.items():
        vals[key] = val

    if XML_path_routine is not None:
        vals['routine'] = XML_path_routine
    if XML_path_netmap is not None:
        vals['netmap'] = XML_path_netmap

    with open(filepath, 'w') as f:
        yaml.dump(vals, f)


def YAML_to_config(filepath=get_dflt_entry('configs', 'last_coreconfig.yaml'),
                   timer=None, netmap=None, routine=None,
                   logger_setup=None, modmanager=None,
                   filemanager=None, check_files=True):
    with open(filepath, 'r') as f:
        cfg_dic = yaml.safe_load(f.read())

    coreconfig = CoreConfig(timer=timer,
                            netmap=netmap if netmap is not None else cfg_dic.get('netmap'),
                            routine=routine if routine is not None else cfg_dic.get('routine'),
                            logger_setup=logger_setup if logger_setup is not None else cfg_dic.get('logger_setup'),
                            modmanager=modmanager if modmanager is not None else cfg_dic.get('modmanager'),
                            filemanager=filemanager, check_files=check_files)
    return coreconfig