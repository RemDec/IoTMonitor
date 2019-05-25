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


def YAML_to_config(filepath=get_dflt_entry('last_cfg'),
                   timer=None, netmap=None, routine=None,
                   logger_setup=None, event_center=None, modmanager=None,
                   filemanager=None):
    with open(filepath, 'r') as f:
        cfg_dic = yaml.safe_load(f.read())
        cfg_dic = {} if cfg_dic is None else cfg_dic

    coreconfig = CoreConfig(timer=timer,
                            netmap=netmap if netmap is not None else cfg_dic.get('netmap'),
                            routine=routine if routine is not None else cfg_dic.get('routine'),
                            logger_setup=logger_setup if logger_setup is not None else cfg_dic.get('logger_setup'),
                            event_center=event_center,
                            modmanager=modmanager if modmanager is not None else cfg_dic.get('modmanager'),
                            filemanager=filemanager,
                            file_from=filepath)
    return coreconfig


if __name__ == '__main__':
    from src.utils.timer import TimerThread
    routine = get_dflt_entry('div_outputs', 'testRoutineXML.xml')
    file = get_dflt_entry('div_outputs', 'testCoreConfig.yaml')
    config_to_YAML(CoreConfig(routine=routine), filepath=file)
    coreconfig = YAML_to_config(filepath=file, timer=TimerThread(name='Replacement timer'))
    print(coreconfig.detail_str(level=1))
