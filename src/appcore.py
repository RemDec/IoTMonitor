from src.routine.routine import *
from src.utils.moduleManager import *
from src.utils.logger import *
from src.utils.timer import *
from src.utils.misc_fcts import has_method
import signal


class Core:

    def __init__(self, logger=None):
        signal.signal(signal.SIGINT, self.interrupt_handler)
        self.modmanager = ModManager()
        self.timer = TimerThread()
        self.netmap = ["Virtual Instances"]
        self.routine = Routine(timer=self.timer, netmap=self.netmap)
        self.logger = Logger() if logger is None else logger

        self.modmanager.load_modlib()
        self.timer.launch()
        self.indep_mods = []

    # ----- Modules library interactions -----

    def instantiate_module(self, mod_id, curr_params=None):
        return self.modmanager.get_mod_from_id(mod_id, curr_params=curr_params, timer=self.timer, netmap=self.netmap)

    def get_available_mods(self, only_names=False, stringed=False):
        # All modules referenced by current used modules library
        if only_names:
            actives, passives = self.modmanager.list_all_modid()
            if stringed:
                return f"Actives : {actives} | Passives : {passives}"
            else:
                return actives, passives
        return self.modmanager.get_all_desc()

    # ----- Independant running modules -----

    def add_indep_module(self, id_or_mod, launch_it=True):
        if isinstance(id_or_mod, str):
            id_or_mod = self.instantiate_module(id_or_mod)
        self.indep_mods.append(id_or_mod)
        if launch_it:
            id_or_mod.launch()

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
            id_or_mod = self.instantiate_module(id_or_mod)
        self.routine.add_module(id_or_mod, given_setid, given_timer)

    def change_mod_params(self, setid, new_params):
        self.routine.change_mod_params(setid, new_params)

    def get_from_routine(self, setid):
        return self.routine.get_mod_by_setid(setid)

    def remove_from_routine(self, setid_or_mod):
        return self.routine.remove_module(setid_or_mod)

    def pause(self):
        self.routine.pause()

    def pause_it(self, target):
        self.routine.pause_it(target)

    def resume(self):
        self.routine.resume()

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

    def quit(self):
        if self.timer is not None:
            self.timer.stop()
        if self.indep_mods is not None:
            self.stop_all_indep()
        if self.routine is not None:
            self.routine.stop()

    def interrupt_handler(self, sig, frame):
        self.quit()

    def corresp_target(self, target_str):
        if target_str == "routine":
            return self.routine
        elif target_str == "netmap":
            return self.netmap
        elif target_str == "timer":
            return self.timer
        elif target_str == "indep":
            return self.indep_mods
        elif target_str == "library":
            return self.modmanager

    def get_display(self, target, level=0):
        obj = self.corresp_target(target)
        if has_method(obj, 'detail_str'):
            return obj.detail_str(level)
        else:
            return obj.__str__()

    def __str__(self):
        actives, passives = self.modmanager.list_all_modid()
        indeps = [mod.m_id for mod in self.indep_mods]
        s = f"=++====== Core application =========\n"
        s += f" || Using logger {self.logger}\n"
        s += f" || Main timer : {self.timer}\n"
        s += f" || Available AModules : {', '.join(actives)}\n"
        s += f" || Available PModules : {', '.join(passives)}\n"
        s += f" || Routine independent modules added :\n || {','.join(indeps)}\n"
        s += f" ++------- ROUTINE -------"
        s += f"{self.routine.detail_str()}"
        s += f" ||\n ++------- NETMAP -------\n"
        s += f"{str(self.netmap)}"
        return s