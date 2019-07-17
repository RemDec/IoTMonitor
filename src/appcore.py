from src.coreConfig import CoreConfig
from src.utils.misc_fcts import obj_str, log_feedback_available
import signal


class Core:
    """This objects represents the app itself, maintaining references to all its components.

    It is the upper level of the logic part through all elements can be managed.
    """

    def __init__(self, coreconfig=None):
        if coreconfig is None:
            coreconfig = CoreConfig()
        log_feedback_available('Instantiation of AppCore considering '+coreconfig.detail_str(level=0))
        signal.signal(signal.SIGINT, self.interrupt_handler)
        self.coreconfig = coreconfig
        self.logger_setup = coreconfig.logger_setup
        self.modmanager = coreconfig.modmanager
        self.timer = coreconfig.timer
        self.netmap = coreconfig.netmap
        self.routine = coreconfig.routine
        self.indep_mods = []

        self.modmanager.load_modlib()
        self.timer.launch()

        self.code_components = {'app': self, 'routine': self.routine, 'netmap': self.netmap, 'indep': self.indep_mods,
                                'timer': self.timer, 'library': self.modmanager,
                                'events': self.get_event_center(), 'feedback': self.get_feedback()}
        log_feedback_available('Finished instantiation of AppCore and its components')

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
        return self.routine.add_module(id_or_mod, setid=given_setid, given_timer=given_timer)

    def change_mod_params(self, setid, new_params):
        self.routine.change_mod_params(setid, new_params)

    def get_from_routine(self, setid, whole_entry=False):
        return self.routine.get_mod_by_setid(setid, whole_entry)

    def remove_from_routine(self, setid_or_mod):
        return self.routine.remove_module(setid_or_mod)

    def rename_routine_modentry(self, oldsetid, newsetid):
        self.routine.rename_module(oldsetid, newsetid)

    def clear_routine(self):
        self.routine.clear()

    def pause(self):
        self.routine.pause()

    def pause_it(self, target):
        self.routine.pause_it(target)

    def resume(self):
        self.routine.resume()

    def resume_it(self, target):
        self.routine.resume_it(target)

    def get_all_setids(self):
        return self.routine.get_all_setids()

    # ----- Netmap interactions -----

    def add_to_netmap(self, vi, mapid=None):
        self.netmap.add_VI(vi, mapid)

    def get_from_netmap(self, mapid):
        return self.netmap.get_VI(mapid)

    def remove_from_netmap(self, mapid):
        self.netmap.remove_VI(mapid)

    def rename_netmap_vi(self, oldmapid, newmapid):
        self.netmap.rename_VI(oldmapid, newmapid)

    def clear_netmap(self):
        self.netmap.clear()

    def get_netmap(self):
        return self.netmap

    def get_all_mapids(self):
        return self.netmap.get_VI_mapids()

    def get_saved_events(self, mapid, target='all', to_str_lvl=-1, reverse=False):
        event_list = self.netmap.get_saved_events_for_vi(mapid, target)
        if reverse:
            event_list = reversed(event_list)
        if to_str_lvl < 0:
            return event_list
        return '\n'.join(map(lambda e: e.detail_str(level=to_str_lvl), event_list))

    # ----- Logging and events -----

    def get_logger_setup(self):
        return self.logger_setup

    def get_event_center(self):
        return self.logger_setup.get_event_center()

    def get_feedback(self):
        return self.get_event_center().get_feedback()

    # ----- Utilities -----

    def clear_target(self, target):
        self.corresp_target(target).clear()

    def clear(self):
        self.clear_netmap()
        self.clear_routine()

    def quit(self):
        if self.timer is not None:
            self.timer.stop()
        if self.indep_mods is not None:
            self.stop_all_indep()
        if self.routine is not None:
            self.routine.stop()

    def interrupt_handler(self, sig, frame):
        log_feedback_available('AppCore execution flow interrupted due to signal '+str(sig))
        self.quit()

    def corresp_target(self, target_str):
        target = self.code_components.get(target_str)
        if target is not None:
            return target
        elif target_str == "threats":
            return self.get_event_center().get_threat_events()
        elif target_str == "modifs":
            return self.get_event_center().get_modif_events()

    def get_display(self, target, level=0):
        obj = self.corresp_target(target)
        if isinstance(obj, list):
            all_display = ""
            for indiv_obj in obj:
                all_display += obj_str(indiv_obj, level)
            return all_display
        return obj_str(obj, level)

    def detail_str(self, level=2):
        actives, passives = self.modmanager.list_all_modid()
        indeps = [mod.get_module_id() for mod in self.indep_mods] if len(self.indep_mods) > 0 else ['< no independent module >']
        s = ""
        if level == 0:
            s += f"=++====== Core application =========\n"
            s += f" || Available modules : {','.join(actives)} | {','.join(passives)}\n"
            s += f" ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=0)}"
            s += f" ||\n ++------- NETMAP -------\n"
            s += f"{self.netmap.detail_str(level=0)}"
        elif level == 1:
            last_feedback = self.get_event_center().pull_feedback()
            if last_feedback.strip() != '':
                s += last_feedback + '_' * 100 + '\n\n'
            s += f"=++====== Core application =========\n"
            s += f" || Available modules : {','.join(actives)} | {','.join(passives)}\n"
            s += f" || Routine independent modules :\n || {','.join(indeps)}\n"
            s += f" ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=1)}"
            s += f" ||\n ++------- NETMAP  -------\n"
            s += f"{self.netmap.vi_frames()}"
        elif level < 5:
            last_feedback = self.get_event_center().pull_feedback(nbr_lines=3)
            if last_feedback.strip() != '':
                s += last_feedback + '_' * 130 + '\n\n'
            s += f"=++====== Core application =========\n"
            s += f" || Core config file : {self.coreconfig.get_cfg_file()}\n"
            s += f" || {self.logger_setup.email_str()}\n"
            s += f" || Available modules : {','.join(actives)} | {','.join(passives)}\n"
            s += f" || Routine independent modules :\n ||  {','.join(indeps)}\n"
            s += f" ||\n ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=level)}"
            s += f" ||\n ++------- NETMAP  -------\n"
            s += f"{self.netmap.detail_str(level=2, vi_by_pack_of=4)}"
        else:
            last_feedback = self.get_event_center().pull_feedback(nbr_lines=min(5, level))
            if last_feedback.strip() != '':
                s += last_feedback + '_'*50 + "^^^ FEEDBACK BAR ^^^" + '_'*50 + '\n\n'
            s += f"=++====== Core application =========\n"
            s += f" || Coreconfig instance maintains file configuration paths :\n"
            s += self.coreconfig.str_current_paths(prefix=" ||  -")
            s += f" || {self.logger_setup.email_str()}\n"
            s += f" || Using loggers {', '.join(self.logger_setup.get_all_loggers())}\n"
            s += f" || Available AModules : {', '.join(actives)}\n"
            s += f" || Available PModules : {', '.join(passives)}\n"
            s += f" || Routine independent modules added :\n || {','.join(indeps)}\n"
            s += f" ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=3)}"
            s += f" ||\n ++------- NETMAP -------\n"
            s += f"{self.netmap.detail_str(level=2, vi_by_pack_of=4, max_char_per_vi=35)}"
        return s

    def __str__(self):
        self.detail_str()
