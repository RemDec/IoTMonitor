from src.utils.timer import *
from src.utils.misc_fcts import str_frame, str_multiframe


class Queue(TimerInterface):

    def __init__(self, timer=None, netmap=None, logger=None):
        self.timer = timer
        self.netmap = netmap
        self.logger = logger

        self.set = []
        self.is_running = False

    def add_module(self, active_mod, given_timer=0, given_id=None):
        if not(active_mod.is_active()) or self.get_presence(active_mod) >= 0:
            return False
        new_entry = self.get_mod_entry(active_mod, given_timer, given_id)
        for i in range(len(self.set)):
            if new_entry <= self.set[i]:
                self.set.insert(i, new_entry)
                return True
        self.set.append(new_entry)
        return True

    def remove_module(self, mod):
        ind = self.get_presence(mod)
        if ind >= 0:
            self.set.pop(ind)
            return True
        return False

    def reorganize(self):
        self.set = sorted(self.set, key=lambda mod: mod.get_timer())

    def get_mod_entry(self, active_mod, given_timer, given_id):
        exp_timer = active_mod.get_default_timer() if not given_timer else given_timer
        m_id = active_mod.get_module_id()
        qid = self.get_unique_qid(given_id) if given_id is not None else self.get_unique_qid(m_id)
        return QueueEntry(active_mod, exp_timer, qid)

    def get_unique_qid(self, try_id):
        curr_id = try_id
        counter = 1
        for mod_entry in self.set:
            if mod_entry.qid == curr_id:
                curr_id = try_id + str(counter)
                counter += 1
        return curr_id

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

    def pause(self, kill_thmods=False):
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

    def is_empty(self):
        return len(self.set) == 0

    def get_mod_by_id(self, qid):
        for entry in self.set:
            if entry.qid == qid:
                return entry.module

    def get_corresp_entry(self, field):
        # field either module instance or id
        for entry in self.set:
            if field is entry.module or field == entry.qid:
                return entry

    def get_idlist(self):
        return [entry.qid for entry in self.set]

    def __str__(self):
        return self.adaptive_display(lambda entry: f"{entry.qid} ~ {str(entry.exp_timer)}s")

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
            return self.adaptive_display(lambda entry: f"{entry.qid} {entry.exp_timer}sec [{entry.init_timer}]" +
                                                       f"{entry.module.str_summary()}")
        else:
            s = f"Queue of {len(self.set)} active modules (running : {self.is_running})\n"
            sep = "+"*len(s) + "\n"
            s += f"triggered by {self.timer}\n"
            s += sep
            for entry in self.set:
                s += "*"*(len(sep)//2) + " " + entry.qid + "\n"
                s += entry.module.str_threads()
                s += "*"*(len(sep)//2 + len(entry.qid) + 1) + "\n"
            s += sep
            return s


class QueueEntry:

    def __init__(self, module, exp_timer, qid):
        self.module = module
        self.exp_timer = exp_timer
        self.init_timer = exp_timer
        self.qid = qid

    def decr(self):
        if self.exp_timer >= 1:
            self.exp_timer -= 1
        else:
            self.module.launch()
            self.exp_timer = self.init_timer

    def get_timer(self):
        return self.exp_timer

    def __le__(self, other):
        return self.get_timer() <= other.get_timer()

    def __str__(self):
        title = f"{self.qid} {self.exp_timer}s [{self.init_timer}]"
        f_title = "| " + title + " |"
        sep = "+" + (len(f_title)-2)*"-" + "+"
        return f"{sep}\n{f_title}\n{sep}"


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

