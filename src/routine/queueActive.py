from utils.timer import *


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

    def is_empty(self):
        return len(self.set) == 0

    def run(self):
        if self.timer is None:
            self.timer = TimerThread()
            self.timer.launch()
        self.timer.subscribe(self)
        self.is_running = True

    def pause(self):
        self.is_running = False

    def is_decrementable(self):
        return self.is_running

    def decr(self):
        for entry in self.set:
            entry.decr()
        self.reorganize()

    def __str__(self):
        s = f"Queue composed of {len(self.set)} active modules (running :{self.is_running})\n"
        if self.is_empty():
            s += " "*5 + "[ empty module queue ]"
        for i, mod in enumerate(self.set):
            s += str(mod) + "\n"
            if i < len(self.set)-1:
                s += " "*5 + "|\n"
                s += " "*5 + "V\n"
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
    from actives.nmapExplorer import *
    from actives.arbitraryCmd import *

    nmap = AModNmapExplorer()
    sleep = AModArbitraryCmd({"prog": "sleep", "args": "5"})
    ping = AModArbitraryCmd({"prog": "ping", "args": "-c 1 8.8.8.8"})

    q.add_module(nmap, given_timer=10, given_id="nmapmodule")
    q.add_module(sleep, given_timer=20)
    q.add_module(ping)
    print(q.get_presence(nmap))
    q.add_module(nmap) # duplicate should not be added
    print(q)

    q.run()
    cnt = 65
    import time
    while cnt > 0:
        time.sleep(10)
        cnt -= 10
        print(q)
    q.pause()
    print("After pausing queue :\n", q)

