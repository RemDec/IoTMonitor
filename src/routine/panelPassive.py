from src.utils.misc_fcts import str_frame


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

    def get_mod_entry(self, mod, given_id):
        # return a PanelEntry with adapted pid (no duplicate)
        m_id = mod.get_module_id()
        pid = self.get_unique_pid(m_id)
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
                    entry.module.stop()
            self.is_running = False

    def resume(self):
        if not self.is_running:
            for entry in self.set:
                entry.module.launch(read_interv=entry.module.get_read_interval())
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

    def __str__(self):
        return self.adaptive_display(lambda entry: entry.pid)

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
            return self.adaptive_display(lambda entry: entry.pid + " " + entry.module.str_summary())
        else:
            s = f"Panel composed of {len(self.set)} passive modules (running : {self.is_running})\n"
            sep = "+"*len(s) + "\n"
            s += sep
            for entry in self.set:
                s += "*"*(len(sep)//2) + " " + entry.pid + "\n"
                s += entry.module.str_pair_threads()
                s += "*"*(len(sep)//2 + len(entry.pid) + 1) + "\n"
            s += sep
            return s


class PanelEntry:

    def __init__(self, module, pid):
        self.module = module
        self.pid = pid

    def __str__(self):
        return str_frame(f"{self.pid} -> {self.module.str_summary()}")


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
