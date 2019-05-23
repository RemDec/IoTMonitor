from src.utils.misc_fcts import obj_str
from src.utils.filesManager import FilesManager
from src.logging.logger_setup import CustomLoggerSetup
from src.utils.moduleManager import ModManager
from src.utils.timer import TimerThread
from src.routine.routine import Routine
from src.net.netmap import Netmap


def get_coreconfig_from_file(filepath, timer=None, netmap=None, routine=None,
                             logger_setup=None, event_center=None, modmanager=None,
                             filemanager=FilesManager(), check_files=True):
    import pathlib
    ext = pathlib.Path(filepath).suffix
    if ext == '.yaml':
        from src.parsers.coreConfigParser import YAML_to_config
        coreconfig = YAML_to_config(filepath=filepath, timer=timer, netmap=netmap, routine=routine,
                                    logger_setup=logger_setup, event_center=event_center, modmanager=modmanager,
                                    filemanager=filemanager, check_files=check_files)
    else:
        coreconfig = CoreConfig(file_from=filepath)
    return coreconfig


class CoreConfig:

    def __init__(self, timer=None, netmap=None, routine=None,
                 logger_setup=None, event_center=None, modmanager=None,
                 filemanager=None, check_files=True,
                 file_from=''):
        self.file_from = file_from
        self.timer, self.netmap, self.routine = (None, )*3
        self.logger_setup, self.event_center, self.modmanager = (None, )*3

        # files and default paths are looked in a filemanager instance, refrenced for saving at exiting time
        self.filemanager = filemanager if filemanager is not None else FilesManager()
        if check_files:
            self.check_file_tree(self.filemanager)
        self.paths = {'config': self.filemanager.get_res_path('last_cfg') if file_from == '' else file_from,
                      'logger_setup': self.filemanager.get_res_path('dflt_logger'),
                      'library': self.filemanager.get_res_path('dflt_lib'),
                      'routine': self.filemanager.get_res_path('last_routine'),
                      'netmap': self.filemanager.get_res_path('last_netmap')}

        # instantiating app elements in right order and considering path of cfg files or yet instantiated objects
        self.init_logger(logger_setup)
        self.init_event_center(event_center)
        self.init_modmanager(modmanager)
        self.init_timer(timer)
        self.init_netmap(netmap)
        self.init_routine(routine)  # routine needs timer and netmap to be instantiate correctly before

    def init_logger(self, logger_setup):
        if logger_setup is None:
            self.logger_setup = CustomLoggerSetup(cfg_file=self.paths['logger_setup'])
        elif isinstance(logger_setup, str):
            self.paths['logger_setup'] = self.filemanager.complete_path('configs', logger_setup)
            self.logger_setup = CustomLoggerSetup(cfg_file=self.paths['logger_setup'])
        elif isinstance(CustomLoggerSetup, logger_setup):
            self.logger_setup = logger_setup
        else:
            pass

    def init_event_center(self, event_center):
        self.event_center = event_center if event_center is not None else self.logger_setup.get_event_center()

    def init_modmanager(self, modmanager):
        if modmanager is None:
            self.modmanager = ModManager(modlib_file=self.paths['library'], load_direct=True)
        elif isinstance(modmanager, str):
            self.paths['library'] = self.filemanager.complete_path('configs', modmanager)
            self.modmanager = ModManager(modlib_file=self.paths['library'], load_direct=True)
        elif isinstance(modmanager, ModManager):
            self.modmanager = modmanager
        else:
            pass

    def init_timer(self, timer):
        if timer is None:
            self.timer = TimerThread()
        elif isinstance(timer, TimerThread):
            self.timer = timer
        else:
            pass

    def init_netmap(self, netmap):
        if netmap is None:
            self.netmap = Netmap()
        elif isinstance(netmap, str):
            from src.parsers.netmapParser import parse_netmap_XML
            self.paths['netmap'] = self.filemanager.complete_path('netmaps', netmap)
            self.netmap = parse_netmap_XML(filepath=self.paths['netmap'], event_center=self.event_center)
        elif isinstance(netmap, Netmap):
            self.netmap = netmap
        else:
            pass

    def init_routine(self, routine):
        if routine is None:
            self.routine = Routine(timer=self.timer, netmap=self.netmap)
        elif isinstance(routine, str):
            from src.parsers.routineParser import parse_routine_XML
            self.paths['routine'] = self.filemanager.complete_path('routines', routine)
            self.routine = parse_routine_XML(filepath=self.paths['routine'], timer=self.timer, netmap=self.netmap,
                                             modmanager=self.modmanager)
        elif isinstance(routine, Routine):
            self.routine = routine
        else:
            pass

    def set_file_from(self, filepath):
        self.file_from = filepath
        return self

    def check_file_tree(self, filemanager=None):
        if filemanager is None:
            filemanager = FilesManager()
        return filemanager

    def str_current_paths(self, prefix=""):
        s = ""
        for res, path in self.paths.items():
            s += f"{prefix}{res} : {path}\n"
        return s

    def get_cfg_file(self):
        if self.file_from == '':
            return "< core configuration from scratch (defaults) >"
        return self.file_from

    def detail_str(self, level=1):
        use_paths = "non defaults values for some resource paths" if len(self.paths) > 0 else "all paths as defaults"
        s = f"Core config maintaining {use_paths}\n"
        s += f"Instantiated from file {self.get_cfg_file()}\n"
        if level > 0:
            for obj, given_path in self.paths.items():
                s += f"  | {obj} : {given_path}\n"
            s += "Instantiated objects maintained :\n"
            s += "   <--- Resources managers --->\n"
            for obj in [self.filemanager, self.logger_setup, self.modmanager]:
                s += obj_str(obj, level) + '\n--->\n'
            s += "   <--- Application components --->\n"
            for obj in [self.timer, self.routine, self.netmap]:
                s += obj_str(obj, level) + '\n--->\n'
        return s

    def __str__(self):
        return self.detail_str()
