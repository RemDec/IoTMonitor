from src.utils.timer import *
from src.utils.misc_fcts import str_frame, str_param_comp


class Queue(TimerInterface):

    def __init__(self, timer=None, netmap=None):
        self.timer = timer
        self.netmap = netmap

        self.set = []
        self.is_running = False

    def add_module(self, active_mod, given_timer=0, given_id=None):
        if not(active_mod.is_active()) or self.get_presence(active_mod) >= 0:
            return False
        new_entry = self.get_mod_entry(active_mod, given_timer, given_id)
        for i in range(len(self.set)):
            if new_entry <= self.set[i]:
                self.set.insert(i, new_entry)
                return new_entry
        self.set.append(new_entry)
        return new_entry

    def remove_module(self, mod):
        ind = self.get_presence(mod)
        if ind >= 0:
            self.set.pop(ind)
            return True
        return False

    def clear(self):
        self.pause(kill_thmods=True)
        self.set = []

    def reorganize(self):
        self.set = sorted(self.set, key=lambda mod: mod.get_timer())

    def get_mod_entry(self, active_mod, given_timer, given_id):
        exp_timer = active_mod.get_default_timer() if not given_timer else given_timer
        m_id = active_mod.get_module_id()
        qid = self.get_unique_qid(given_id) if given_id is not None else self.get_unique_qid(m_id)
        return QueueEntry(active_mod, exp_timer, qid)

    def get_unique_qid(self, try_id):
        idlist = self.get_idlist()
        if not(try_id in idlist):
            return try_id
        counter = 1
        while try_id + str(counter) in idlist:
            counter += 1
        return try_id + str(counter)

    def get_presence(self, mod):
        for i, entry in enumerate(self.set):
            if isinstance(mod, str) and mod == entry.qid:
                return i
            if mod is entry.module:
                return i
        return -1

    def run(self):
        if self.timer is None:
            self.timer = TimerThread()
            self.timer.launch()
        self.timer.subscribe(self)
        self.is_running = True

    def pause(self, kill_thmods=True):
        # for queue pause means stop decrementing launching countdown, kill_thmods kill also threads launched newly
        self.is_running = False
        if kill_thmods:
            for entry in self.set:
                entry.module.stop()

    def resume(self):
        self.timer.subscribe(self)
        self.is_running = True

    def is_decrementable(self):
        return self.is_running

    def decr(self):
        for entry in self.set:
            entry.decr()
        self.reorganize()

    def rename(self, old_qid, new_qid):
        qids = self.get_idlist()
        if old_qid in qids:
            if new_qid in qids:
                # Have to rename already so named entry
                wrong_named = self.get_corresp_entry(new_qid)
                wrong_named.pid = self.get_unique_qid(new_qid)
            curr_entry = self.get_corresp_entry(old_qid)
            curr_entry.pid = new_qid

    def is_empty(self):
        return len(self.set) == 0

    def get_nbr_mods(self):
        return len(self.set)

    def get_mod_by_id(self, qid):
        for entry in self.set:
            if entry.qid == qid:
                return entry.module

    def get_corresp_entry(self, field):
        # field either module instance or qid
        for entry in self.set:
            if field is entry.module or field == entry.qid:
                return entry

    def get_idlist(self):
        return [entry.qid for entry in self.set]

    def get_modentries(self):
        return self.set

    def adaptive_display(self, fct_to_entry, header=True):
        s = ""
        if header:
            s = f"Queue of {len(self.set)} active modules (running : {self.is_running})\n"
        if self.is_empty():
            s += " "*5 + "[ empty queue ]\n"
        else:
            inter = ""
            for entry in self.set:
                inter += f" {fct_to_entry(entry)} |=>|"
            s += str_frame(inter[:-4])
        return s

    def detail_str(self, level=0):
        if level == 0:
            return self.__str__()
        elif level == 1:
            return self.adaptive_display(lambda entry: f"{entry.qid} {entry.exp_timer}s [{entry.init_timer}]" +
                                                       f"{entry.module.str_summary()}")
        else:
            s = f"Queue of {len(self.set)} active modules (running : {self.is_running})\n"
            sep = "+"*len(s) + "\n"
            s += f"triggered by {self.timer}\n"
            for entry in self.set:
                s += sep
                s += entry.detail_str(level=2)
            s += sep
            return s

    def __str__(self):
        return self.adaptive_display(lambda entry: f"{entry.qid} ~ {str(entry.exp_timer)}s")


class QueueEntry:

    def __init__(self, module, exp_timer, qid, rel_to_vi=[]):
        self.module = module
        self.exp_timer = exp_timer
        self.init_timer = exp_timer
        self.qid = qid
        self.rel_to_vi = rel_to_vi

    def set_vi_relative(self, rel_to_vi):
        if isinstance(rel_to_vi, str):
            self.rel_to_vi = [rel_to_vi]
        else:
            self.rel_to_vi = rel_to_vi

    def decr(self):
        if self.exp_timer >= 1:
            self.exp_timer -= 1
        else:
            self.module.launch(rel_to_vi=self.rel_to_vi)
            self.exp_timer = self.init_timer

    def set_timer(self, new_timer):
        self.exp_timer = new_timer

    def get_timer(self):
        return self.exp_timer

    def __le__(self, other):
        return self.get_timer() <= other.get_timer()

    def detail_str(self, level=0):
        s = str_frame(f"{self.qid} {self.exp_timer}s [{self.init_timer}]")
        if level == 0:
            return s
        elif level == 1:
            curr_params, dflt_params, desc_PARAMS = self.module.get_params()
            rel_vi_str = '| < no specific VI >' if len(self.rel_to_vi) == 0 else ', '.join(self.rel_to_vi)
            s += f"| ACTIVE module whose description is given as :\n"
            s += f"|  {self.module.get_description()}\n"
            s += f"| Execution relative to VIs : {rel_vi_str}\n"
            s += f"| Associated underlying program : {self.module.get_cmd()}\n"
            s += f"| Module parameters :\n"
            s += str_param_comp(curr_params, dflt_params, descriptions=desc_PARAMS, prefix='|  ')
        else:
            curr_params, dflt_params, desc_PARAMS = self.module.get_params()
            rel_vi_str = '| < no specific VI >'
            if len(self.rel_to_vi) > 0 and self.module.netmap is not None:
                rel_vi_str = self.module.netmap.vi_frames(self.module.netmap.get_VI_mapids(subset_mapids=self.rel_to_vi))
            s += f"| PASSIVE module whose description is given as :\n"
            s += f"|  {self.module.get_description()}\n"
            s += f"| Associated underlying program : {self.module.get_cmd()}\n"
            s += f"| Module parameters :\n"
            s += str_param_comp(curr_params, dflt_params, descriptions=desc_PARAMS, prefix='|  ')
            s += f"| Threads registered :\n"
            s += self.module.str_threads() + "|\n"
            b = '\n'
            s += f"| Execution relative to VIs :\n{rel_vi_str}{b if rel_vi_str[-1] != b else ''}"
        return s

    def __str__(self):
        return self.detail_str()


if __name__=="__main__":
    q = Queue()
    print(q)
    from modules.actives.nmapExplorer import *
    from modules.actives.arbitraryCmd import *

    nmap = AModNmapExplorer()
    sleep = AModArbitraryCmd({"prog": "sleep", "args": "5"})
    ping = AModArbitraryCmd({"prog": "ping", "args": "-c 1 8.8.8.8"})

    q.add_module(nmap, given_timer=5, given_id="nmapmodule")
    q.add_module(sleep, given_timer=10)
    q.add_module(ping, given_timer=3)
    q.add_module(nmap) # duplicate should not be added
    print("\n#########################\nBefore running queue :\n", q)
    print("\n #### with details level = 1", q.detail_str(level=1))
    print("\n #### with details level = 2", q.detail_str(level=2))
    print("\n Starting ..")
    q.run()
    cnt = 25
    import time
    while cnt > 0:
        time.sleep(5)
        cnt -= 5
        print(q.detail_str(level=1))
    q.pause(kill_thmods=True)
    q.timer.stop()
    print("\n#########################\nAfter pausing queue :\n", q)
    print(q.detail_str(level=2))

