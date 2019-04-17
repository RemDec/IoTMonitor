from src.routine.routine import *
from src.utils.moduleManager import *
from src.utils.logger import *
from src.utils.timer import *
import signal


class Core:

    def __init__(self, logger=None):
        signal.signal(signal.SIGINT, self.interrupt_handler)
        self.modmanager = ModManager()
        self.timer = TimerThread()
        self.netmap = []
        self.routine = Routine(timer=self.timer, netmap=self.netmap)
        self.logger = Logger() if logger is None else logger

        self.modmanager.load_modlib()
        self.timer.launch()
        self.indep_mods = []

    # ----- Modules library interactions -----

    def create_module(self, mod_id):
        return self.modmanager.get_mod_from_id(mod_id)

    def get_available_mods(self):
        return self.modmanager.get_all_desc()

    # ----- Independant running modules -----

    def launch_indep_module(self, new_module, launch_it=True):
        self.indep_mods.append(new_module)
        if launch_it:
            new_module.launch()

    def stop_indep_module(self, module_or_index):
        if isinstance(module_or_index, int):
            self.indep_mods[module_or_index].stop()
        elif module_or_index in self.indep_mods:
            self.indep_mods[self.indep_mods.index(module_or_index)].stop()

    def stop_all_indep(self):
        for mod in self.indep_mods:
            mod.stop()

    # ----- Routine interactions -----

    def add_to_routine(self, id_or_mod, given_setid=None, given_timer=None):
        if isinstance(id_or_mod, str):
            id_or_mod = self.create_module(id_or_mod)
        self.routine.add_module(id_or_mod, given_setid, given_timer)

    def change_mod_params(self, setid, new_params):
        self.routine.change_mod_params(setid, new_params)

    def get_from_routine(self, setid):
        return self.routine.get_mod_by_setid(setid)

    def remove_from_routine(self, setid_or_mod):
        return self.routine.remove_module(setid_or_mod)

    def pause_it(self, target):
        self.routine.pause_it(target)

    def resume_it(self, target):
        self.routine.resume_it(target)

    def clear_routine(self):
        pass

    # ----- Netmap interactions -----

    def add_to_netmap(self, iv):
        pass

    def get_from_netmap(self, index):
        pass

    def remove_from_netmap(self, index):
        pass

    def get_netmap(self):
        return self.netmap

    # ----- Output -----

    def get_diagram_view(self):
        pass

    def get_threats_logs(self):
        pass

    def set_handler(self, for_logger, handler_cfg):
        pass

    # ----- Utilities -----

    def interrupt_handler(self, sig, frame):
        if self.timer is not None:
            self.timer.stop()
        if self.indep_mods is not None:
            self.stop_all_indep()
        if self.routine is not None:
            self.routine.stop()

    def __str__(self):
        actives, passives = self.modmanager.list_all_modid()
        indeps = [mod.m_id for mod in self.indep_mods]
        s = f"=++====== Core application =========\n"
        s += f" || Using logger {self.logger}\n"
        s += f" || Main timer : {self.timer}\n"
        s += f" || Available AModules : {','.join(actives)}\n"
        s += f" || Available PModules : {','.join(passives)}\n"
        s += f" || Routine independent modules added :\n || {','.join(indeps)}\n"
        s += f" ++------- ROUTINE -------\n"
        s += f"{self.routine.detail_str()}"
        s += f" ||\n ++------- NETMAP -------\n"
        s += f"{str(self.netmap)}"
        return s