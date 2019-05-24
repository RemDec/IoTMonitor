from src.utils.misc_fcts import str_frame, str_param_comp


class Panel:

    def __init__(self, netmap=None):
        self.netmap = netmap

        self.set = []
        self.is_running = False

    def add_module(self, passive_mod, given_id=None):
        # create+add a PanelEntry object if the passive_mod instance not yet in an entry within the panel
        if passive_mod.is_active() or self.get_presence(passive_mod) > -1:
            return False
        new_entry = self.get_mod_entry(passive_mod, given_id)
        self.set.append(new_entry)
        return True

    def remove_module(self, mod):
        # remove a module given his instance or pid in the Panel
        ind = self.get_presence(mod)
        if ind >= 0:
            self.set.pop(ind)
            return True
        return False

    def clear(self):
        self.pause(kill_thmods=True)
        self.set = []

    def get_mod_entry(self, mod, given_id=None):
        # return a PanelEntry with adapted pid (no duplicate)
        m_id = mod.get_module_id()
        pid = self.get_unique_pid(m_id) if given_id is None else self.get_unique_pid(given_id)
        return PanelEntry(mod, pid)

    def get_unique_pid(self, try_id):
        # create unique pid in panel from module basic id
        curr_id = try_id
        counter = 1
        for mod_entry in self.set:
            if mod_entry.pid == curr_id:
                curr_id = try_id + str(counter)
                counter += 1
        return curr_id

    def get_presence(self, mod):
        # mod is in panel where mod is a module instance or pid : -1 if absent, PanelEntry indice in set else
        for i, entry in enumerate(self.set):
            if isinstance(mod, str) and mod == entry.pid:
                return i
            if mod is entry.module:
                return i
        return -1

    def pause(self, kill_thmods=True):
        # for panel pause means interrupt current continuously working threads so kill_thmods should be true
        if self.is_running:
            if kill_thmods:
                for entry in self.set:
                    entry.stop_module()
            self.is_running = False

    def resume(self):
        if not self.is_running:
            for entry in self.set:
                entry.launch_module()
            self.is_running = True

    def is_empty(self):
        return len(self.set) == 0

    def get_nbr_mods(self):
        return len(self.set)

    def get_mod_by_id(self, pid):
        for entry in self.set:
            if entry.pid == pid:
                return entry.module

    def get_corresp_entry(self, field):
        # field either module instance or id
        for entry in self.set:
            if field is entry.module or field == entry.pid:
                return entry

    def get_idlist(self):
        return [entry.pid for entry in self.set]

    def adaptive_display(self, fct_to_entry, header=True):
        s = ""
        if header:
            s = f"Panel composed of {len(self.set)} passive modules (running : {self.is_running})\n"
        if self.is_empty():
            s += " "*5 + "[ empty panel ]\n"
        else:
            inter = ""
            for entry in self.set:
                inter += f" {fct_to_entry(entry)} |"
            s += str_frame(inter[:-1])
        return s

    def detail_str(self, level=0):
        if level == 0:
            return self.__str__()
        elif level == 1:
            return self.adaptive_display(lambda entry: f"{entry.pid} {entry.module.str_summary()}")
        else:
            s = f"Panel composed of {len(self.set)} passive modules (running : {self.is_running})\n"
            sep = "+"*len(s) + "\n"
            for entry in self.set:
                s += sep
                s += entry.detail_str(level=2)
            s += sep
            return s

    def __str__(self):
        return self.adaptive_display(lambda entry: entry.pid)


class PanelEntry:

    def __init__(self, module, pid, rel_to_vi=[]):
        self.module = module
        self.pid = pid
        self.rel_to_vi = rel_to_vi

    def set_vi_relative(self, rel_to_vi):
        if isinstance(rel_to_vi, str):
            self.rel_to_vi = [rel_to_vi]
        else:
            self.rel_to_vi = rel_to_vi

    def launch_module(self):
        self.module.launch(rel_to_vi=self.rel_to_vi, read_interv=self.module.get_read_interval())

    def stop_module(self):
        self.module.stop()

    def detail_str(self, level=0):
        s = str_frame(f"{self.pid} {self.module.str_summary()}")
        if level == 0:
            return s
        elif level == 1:
            curr_params, dflt_params, desc_PARAMS = self.module.get_params()
            rel_vi_str = '< no specific VI >' if len(self.rel_to_vi) == 0 else ', '.join(self.rel_to_vi)
            s += f"| PASSIVE module whose description is given as :\n"
            s += f"|  {self.module.get_description()}\n"
            s += f"| Execution relative to VIs : {rel_vi_str}\n"
            s += f"| Associated underlying program : {self.module.get_cmd()}\n"
            s += f"| Module parameters :\n"
            s += str_param_comp(curr_params, dflt_params, descriptions=desc_PARAMS, prefix='|  ')
        else:
            curr_params, dflt_params, desc_PARAMS = self.module.get_params()
            rel_vi_str = '< no specific VI >'
            if len(self.rel_to_vi) > 0 and self.module.netmap is not None:
                rel_vi_str = self.module.netmap.vi_frames(self.module.netmap.get_VI_mapids(subset_mapids=self.rel_to_vi))
            s += f"| PASSIVE module whose description is given as :\n"
            s += f"|  {self.module.get_description()}\n"
            s += f"| Associated underlying program : {self.module.get_cmd()}\n"
            s += f"| Module parameters :\n"
            s += str_param_comp(curr_params, dflt_params, descriptions=desc_PARAMS, prefix='|  ')
            s += f"| Threads registered :\n"
            s += self.module.str_pair_threads() + "|\n"
            s += f"| Execution relative to VIs : {rel_vi_str}\n"
        return s

    def __str__(self):
        return self.detail_str()


if __name__ == '__main__':
    from modules.passives.pingTarget import *
    from src.utils.timer import *
    panel = Panel()
    timer = TimerThread()
    ping = PModPing(timer=timer)
    panel.add_module(ping)
    panel.add_module(ping, given_id="sameinst_ping")
    ping2 = PModPing(timer=timer)
    panel.add_module(ping2)

    print("Simple call __str__()\n", panel)
    print("\nCall detailed display\n", panel.detail_str(level=1))

    print("\nLaunching pingit")
    ping.timer.launch()
    ping.set_read_interval(3)
    ping2.set_read_interval(4)
    panel.resume()
    for i in range(10):
        sleep(1)
        print(panel.detail_str(level=1))
    panel.pause()
    timer.stop()
    sleep(2)
    print("\nAfter interrupt :\n", panel.detail_str(level=2))
