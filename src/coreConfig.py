from src.utils.filesManager import FilesManager
from src.logging.logger_setup import CustomLoggerSetup
from src.utils.moduleManager import ModManager
from src.utils.timer import TimerThread
from src.routine.routine import Routine
from src.net.netmap import Netmap


class CoreConfig:

    def __init__(self, timer=None, netmap=None, routine=None,
                 logger_setup=None, modmanager=None,
                 filemanager=FilesManager(), check_files=True):
        self.paths = {}
        self.timer, self.netmap, self.routine = (None, )*3
        self.logger_setup, self.modmanager= (None, )*2
        # files and default paths are looked in a filemanager library instance
        self.filemanager = filemanager if filemanager is not None else FilesManager()
        if check_files:
            self.check_file_tree(self.filemanager)

        self.init_logger(logger_setup)
        self.init_modmanager(modmanager)
        self.init_timer(timer)
        self.init_netmap(netmap)
        # routine needs timer and netmap to be instantiate correctly
        self.init_routine(routine)

    def init_logger(self, logger_setup):
        if logger_setup is None:
            self.logger_setup = CustomLoggerSetup(cfg_file=self.filemanager.get_res_path('dflt_logger'))
        elif isinstance(logger_setup, str):
            self.logger_setup = CustomLoggerSetup(cfg_file=self.filemanager.get_res_path(logger_setup))
            self.paths['logger_setup'] = logger_setup
        elif isinstance(CustomLoggerSetup, logger_setup):
            self.logger_setup = logger_setup
        else:
            pass

    def init_modmanager(self, modmanager):
        if modmanager is None:
            self.modmanager = ModManager(modlib_file=self.filemanager.get_res_path('dflt_lib'))
        elif isinstance(modmanager, str):
            self.modmanager = ModManager(modlib_file=self.filemanager.get_res_path(modmanager))
            self.paths['modmanager'] = modmanager
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
            self.paths['netmap'] = netmap
        elif isinstance(netmap, Netmap):
            self.netmap = netmap
        else:
            pass

    def init_routine(self, routine):
        if routine is None:
            self.routine = Routine(timer=self.timer, netmap=self.netmap)
        elif isinstance(routine, str):
            from src.parsers.routineParser import parse_routine_XML
            self.routine = parse_routine_XML(filepath=routine, timer=self.timer, netmap=self.netmap,
                                             modmanager=self.modmanager)
            self.paths['routine'] = routine
        elif isinstance(routine, Routine):
            self.routine = routine
        else:
            pass

    def check_file_tree(self, filemanager=None):
        if filemanager is None:
            filemanager = FilesManager()
        return filemanager