from src.routine.panelPassive import *
from src.routine.queueActive import *
from modules.abcModule import *

class Routine:

    def __init__(self, modules=[], timer=None, netmap=None, logger=None):
        self.MAX_ID_LGTH = 15
        self.panel = Panel(netmap, logger)
        self.queue = Queue(timer=timer, netmap=netmap, logger=logger)
        # routine is running if at least panel or queue is running
        self.is_running = False
        self.add_modules(modules)

    # --- Routine interactions ---

    def add_module(self, mod, given_id=None, given_timer=0):
        if mod.is_active():
            well_added = self.queue.add_module(mod, given_timer=given_timer, given_id=given_id)
        else:
            well_added = self.panel.add_module(mod, given_id=given_id)
        if not well_added:
            # Raise exception
            print("Adding to routine failed for module", mod)
        self.check_unique_ids()

    def add_modules(self, modlist):
        for any_mod in modlist:
            if isinstance(any_mod, Module):
                self.add_module(any_mod)
            elif isinstance(any_mod, tuple):
                mod, id, interv = any_mod
                self.add_module(mod, id, 0 if interv is None else interv)

    def remove_module(self, mod):
        return self.get_corresp_set(mod).remove_module(mod)

    def pause(self, kill_thpanel=True, kill_thqueue=False):
        # can pause whatever is running or not, worst case it does nothing because no module thread alive
        self.panel.pause(kill_thpanel)
        self.queue.pause(kill_thqueue)
        self.is_running = False

    def resume(self):
        # can run only if paused, run twice would lead to overthreading for nothing
        if not self.panel.is_running:
            self.panel.resume()
        if not self.queue.is_running:
            self.queue.resume()
        self.is_running = True

    def str_to_target(self, s):
        if s == "routine":
            return self
        elif s == "panel":
            return self.panel
        elif s == "queue":
            return self.queue

    def correct_state(self):
        self.is_running = self.panel.is_running or self.queue.is_running

    def pause_it(self, target):
        t = self.str_to_target(target)
        t.pause()
        self.correct_state()

    # --- Internal methods and misc ---

    def get_corresp_set(self, mod):
        return self.queue if mod.is_active() else self.panel

    def check_unique_ids(self):
        # unique ids are guaranteed in each set, but not crossing both
        qids = self.queue.get_idlist()
        for id in self.panel.get_idlist():
            if id in qids:
                i = 1
                new_id = f"{id}#{i}"
                while len(new_id) <= self.MAX_ID_LGTH and new_id in qids:
                    i += 1
                    new_id = f"{id}#{i}"
                if new_id not in qids:
                    self.panel.get_corresp_entry(id).pid = new_id
                else:
                    self.panel.get_corresp_entry(id).pid = self.rdmize_id()

    def rdmize_id(self):
        from random import sample
        from string import ascii_lowercase
        new_id = ''.join(sample(ascii_lowercase, self.MAX_ID_LGTH))
        all_ids = self.panel.get_idlist() + self.queue.get_idlist()
        while new_id in all_ids:
            new_id = ''.join(sample(ascii_lowercase, self.MAX_ID_LGTH))
        return new_id

    def detail_str(self, level=0):
        s = f"\nRoutine in current state : {'RUNNING' if self.is_running else 'PAUSED'}\n" \
            f"\n      <[[ CURRENT PANEL ]]>\n{self.panel.detail_str(level)}\n" \
            f"\n      <[[ CURRENT QUEUE ]]>\n{self.queue.detail_str(level)}"
        return s

    def __str__(self):
        return self.detail_str()


if __name__=='__main__':
    from modules.actives.nmapExplorer import *
    from modules.passives.pingTarget import *
    from src.utils.timer import *

    t = TimerThread()
    nmap = AModNmapExplorer()
    ping = PModPing(timer=t)
    rout = Routine(modules=[(nmap, 'nmapSURNAME', 10), ping], timer=t)
    print(rout.detail_str(level=1))
    t.launch()
    rout.resume()
    for i in range(5):
        sleep(5)
        print("\n##########################\n", rout.detail_str(level=1))
    print("\n\n########## Before Pausing ##########", rout.detail_str(2))
    rout.pause()
    t.stop()
    print("\n\n########## Paused ##########", rout.detail_str(2))
