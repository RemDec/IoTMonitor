from src.coreConfig import CoreConfig
from modules.abcModule import Module
from src.utils.misc_fcts import obj_str, log_feedback_available
import signal


class Core:
    """This objects represents the app itself, maintaining references to all its components.

    It is the upper level of the logic part through all elements can be managed.
    """

    def __init__(self, coreconfig=None, handle_sigint=True):
        if coreconfig is None:
            coreconfig = CoreConfig()
        log_feedback_available('Instantiation of AppCore considering '+coreconfig.detail_str(level=0))
        if handle_sigint:
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
                                'timer': self.timer, 'library': self.modmanager, 'config': self.coreconfig,
                                'events': self.get_event_center(), 'feedback': self.get_feedback()}
        log_feedback_available('Finished instantiation of AppCore and its components')

    # ----- Modules library interactions -----

    def instantiate_module(self, mod_id, curr_params=None):
        return self.modmanager.get_mod_from_id(mod_id, curr_params=curr_params, timer=self.timer, netmap=self.netmap)

    def get_mod_descriptor(self, mod_id):
        return self.modmanager.get_mod_desc(mod_id)

    def get_available_mods(self, only_names=False, stringed=False):
        # All modules referenced by current used modules library
        if only_names:
            actives, passives = self.modmanager.list_all_modid()
            if stringed:
                return f"Actives : {actives} | Passives : {passives}"
            else:
                return actives, passives
        return self.modmanager.get_all_desc()

    # ----- Independent running modules -----

    def add_indep_module(self, id_or_mod, curr_params=None, launch_it=False):
        self.clear_not_running_mods()
        if isinstance(id_or_mod, str):
            id_or_mod = self.instantiate_module(id_or_mod, curr_params=curr_params)
        elif isinstance(id_or_mod, Module) and curr_params is not None:
            id_or_mod.set_params(curr_params)
        self.indep_mods.append(id_or_mod)
        if launch_it:
            id_or_mod.launch()
        log_feedback_available(f"Added [{id_or_mod.get_module_id()}] in independent modules list "
                               f"(launching it: {launch_it})")
        return id_or_mod

    def get_indep_mod(self, module_or_index):
        try:
            if isinstance(module_or_index, Module):
                return module_or_index if module_or_index in self.indep_mods else None
            elif isinstance(module_or_index, int):
                return self.indep_mods[module_or_index]
        except (ValueError, IndexError):
            return None

    def get_independent_modules(self):
        return self.indep_mods

    def stop_indep_module(self, module_or_index):
        modinst = self.get_indep_mod(module_or_index)
        if modinst is not None:
            modinst.stop()
        self.clear_not_running_mods()

    def stop_all_indep(self):
        for mod in self.indep_mods:
            mod.stop()
        self.clear_not_running_mods()

    def clear_not_running_mods(self):
        terminated = [modinst for modinst in self.indep_mods if not modinst.is_running()]
        for modinst in terminated:
            self.indep_mods.remove(modinst)

    def clear_indep_mods(self):
        self.stop_all_indep()
        self.indep_mods = []

    def str_indep_mods(self):
        if len(self.indep_mods) == 0:
            return '< no independent module >'
        s = []
        for modinst in self.indep_mods:
            state = 'R' if modinst.is_running() else 'NR'
            s.append(f"{modinst.get_module_id()}({state})")
        return ', '.join(s)

    # ----- Routine interactions -----

    def add_to_routine(self, id_or_mod, given_setid=None, given_timer=None):
        if isinstance(id_or_mod, str):
            id_or_mod = self.instantiate_module(id_or_mod)
        entry = self.routine.add_module(id_or_mod, setid=given_setid, given_timer=given_timer)
        log_feedback_available(f"Routine : adding a new Module entry [{id_or_mod.get_module_id()}] "
                               f"with setid {entry.get_setid()}")
        return entry

    def change_mod_params(self, setid, new_params):
        self.routine.change_mod_params(setid, new_params)

    def get_from_routine(self, setid, whole_entry=False):
        return self.routine.get_mod_by_setid(setid, whole_entry)

    def remove_from_routine(self, setid_or_mod):
        log_feedback_available(f"Routine : removing entry {setid_or_mod if isinstance(setid_or_mod, str) else ''}")
        return self.routine.remove_module(setid_or_mod)

    def rename_routine_modentry(self, oldsetid, newsetid):
        log_feedback_available(f"Routine : renaming entry {oldsetid} in {newsetid}")
        return self.routine.rename_module(oldsetid, newsetid)

    def clear_routine(self):
        log_feedback_available(f"Routine : clearing both sets, killing running programs")
        self.routine.clear()

    def pause(self):
        self.routine.pause()

    def pause_it(self, target):
        log_feedback_available(f"Routine : pausing {target}")
        self.routine.pause_it(target)

    def resume(self):
        self.routine.resume()

    def resume_it(self, target):
        log_feedback_available(f"Routine : resuming {target}")
        self.routine.resume_it(target)

    def get_all_setids(self):
        return self.routine.get_all_setids()

    # ----- Netmap interactions -----

    def add_to_netmap(self, vi, mapid=None):
        attrib_mapid = self.netmap.add_vi(vi, mapid)
        log_feedback_available(f"Netmap : adding a new VI with mapid {attrib_mapid}")
        return attrib_mapid

    def get_from_netmap(self, mapid):
        return self.netmap.get_vi(mapid)

    def remove_from_netmap(self, mapid):
        log_feedback_available(f"Netmap : removing a VI using mapid {mapid}")
        self.netmap.remove_vi(mapid)

    def rename_netmap_vi(self, oldmapid, newmapid):
        log_feedback_available(f"Netmap : renaming VI {oldmapid} to {newmapid}")
        self.netmap.rename_vi(oldmapid, newmapid)

    def clear_netmap(self):
        log_feedback_available(f"Netmap : clearing all existing VIs and associated events")
        self.netmap.clear()

    def get_netmap(self):
        return self.netmap

    def get_all_mapids(self):
        return self.netmap.get_vi_mapids()

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
        if target == 'indep':
            self.clear_indep_mods()
        else:
            self.corresp_target(target).clear()

    def clear(self):
        self.clear_netmap()
        self.clear_routine()
        self.clear_indep_mods()

    def quit(self):
        log_feedback_available(f"AppCore : quitting application, shut down all processes running")
        if self.timer is not None:
            self.timer.stop()
        if self.indep_mods is not None:
            self.clear_indep_mods()
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
                if not all_display.endswith('\n\n'):
                    all_display += '\n'
            return all_display
        return obj_str(obj, level)

    def detail_str(self, level=2):
        actives, passives = self.modmanager.list_all_modid()
        indeps = self.str_indep_mods()
        s = ""
        header = f"=++============ Core application (disp. lvl {level}) ===============\n"
        if level == 0:
            s += header
            s += f" || Available modules : {','.join(actives)} | {','.join(passives)}\n"
            s += f" ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=0)}"
            s += f" ||\n ++------- NETMAP -------\n"
            s += f"{self.netmap.detail_str(level=0)}"
        elif level == 1:
            last_feedback = self.get_event_center().pull_feedback()
            if last_feedback.strip() != '':
                s += last_feedback + '_' * 100 + '\n\n'
            s += header
            s += f" || Available modules : {','.join(actives)} | {','.join(passives)}\n"
            s += f" || Routine independent Modules : {indeps}\n"
            s += f" ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=level)}"
            s += f" ||\n ++------- NETMAP  -------\n"
            s += f"{self.netmap.vi_frames()}"
        elif level < 5:
            last_feedback = self.get_event_center().pull_feedback(nbr_lines=3)
            if last_feedback.strip() != '':
                s += last_feedback + '_' * 130 + '\n\n'
            s += header
            s += f" || Core config file : {self.coreconfig.get_cfg_file()}\n"
            s += f" || {self.logger_setup.email_str()}\n"
            s += f" || Available modules : {','.join(actives)} | {','.join(passives)}\n"
            s += f" || Routine independent Modules : {indeps}\n"
            s += f" ||\n ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=level)}"
            s += f" ||\n ++------- NETMAP  -------\n"
            s += f"{self.netmap.detail_str(level=2, vi_by_pack_of=4)}"
        elif level < 8:
            last_feedback = self.get_event_center().pull_feedback(nbr_lines=min(5, level))
            if last_feedback.strip() != '':
                s += last_feedback + '_'*50 + "^^^ FEEDBACK BAR ^^^" + '_'*50 + '\n\n'
            s += header
            s += f" || Core config file : {self.coreconfig.get_cfg_file()}\n"
            s += f" || {self.logger_setup.email_str()}\n"
            s += f" || Available AModules : {', '.join(actives)}\n"
            s += f" || Available PModules : {', '.join(passives)}\n"
            s += f" || Routine independent Modules :\n || {indeps}\n"
            s += f" ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=4)}"
            s += f" ||\n ++------- NETMAP -------\n"
            vi_per_line = 4 if level < 8 else 5
            s += f"{self.netmap.detail_str(level=2, vi_by_pack_of=vi_per_line, max_char_per_vi=35)}"
        else:
            last_feedback = self.get_event_center().pull_feedback(nbr_lines=min(5, level))
            if last_feedback.strip() != '':
                s += last_feedback + '_'*50 + "^^^ FEEDBACK BAR ^^^" + '_'*50 + '\n\n'
            s += header
            s += f" || Coreconfig instance maintains file configuration paths :\n"
            s += self.coreconfig.str_current_paths(prefix=" ||  -")
            s += f" || {self.logger_setup.email_str()}\n"
            s += f" || Using loggers {', '.join(self.logger_setup.get_all_loggers())}\n"
            s += f" || Available AModules : {', '.join(actives)}\n"
            s += f" || Available PModules : {', '.join(passives)}\n"
            s += f" || Routine independent modules :\n || {indeps}\n"
            s += f" ++------- ROUTINE -------"
            s += f"{self.routine.detail_str(level=4)}"
            s += f" ||\n ++------- NETMAP -------\n"
            vi_per_line = 4 if level < 9 else 5
            s += f"{self.netmap.detail_str(level=2, vi_by_pack_of=vi_per_line, max_char_per_vi=37)}"
        return s

    def __str__(self):
        self.detail_str()
