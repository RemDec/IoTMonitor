from src.routine.panelPassive import Panel, MAX_LENGTH_SETID
from src.routine.queueActive import Queue
from modules.abcModule import Module


class Routine:

    def __init__(self, modules=[], timer=None, netmap=None, panel=None, queue=None):
        self.panel = Panel(netmap=netmap) if panel is None else panel
        self.queue = Queue(timer=timer, netmap=netmap) if queue is None else queue
        # routine is running if at least panel or queue is running
        self.is_running = False
        self.add_modules(modules)
        self.correct_state()

    # --- Routine interactions ---

    def add_module(self, mod_inst, setid=None, rel_to_vi=[], given_timer=0):
        if mod_inst.is_active():
            entry_added = self.queue.add_module(mod_inst, setid=setid, rel_to_vi=rel_to_vi, given_timer=given_timer)
        else:
            if given_timer > 0:
                mod_inst.set_read_interval(given_timer)
            entry_added = self.panel.add_module(mod_inst, setid=setid, rel_to_vi=rel_to_vi)
        if not entry_added:
            # Raise exception
            print("Adding to routine failed for mod_instule", mod_inst)
        i = 1
        got_setid = entry_added.get_setid()
        while not self.check_unique_setid():
            entry_added.setid = got_setid + str(i)
        return entry_added

    def add_modules(self, modlist):
        for any_mod in modlist:
            if isinstance(any_mod, Module):
                self.add_module(any_mod)
            elif isinstance(any_mod, tuple):
                mod, id = any_mod[:2]
                timer = 0 if len(any_mod) < 3 else any_mod[2]
                self.add_module(mod, setid=id, given_timer=timer)

    def remove_module(self, setid_or_mod):
        return self.get_corresp_set(setid_or_mod).remove_module(setid_or_mod)

    def change_mod_params(self, setid, new_params):
        set = self.get_corresp_set(setid)
        if set is not None:
            mod = set.get_mod_by_id(setid)
            mod.stop()
            mod.set_params(new_params)
            mod.launch()

    def rename_module(self, old_setid, new_setid):
        container = self.get_corresp_set(old_setid)
        if new_setid.strip() != '' and container is not None:
            entry = container.rename(old_setid, new_setid)
            i = 1
            while not self.check_unique_setid():
                container.rename(entry.get_setid(), new_setid + str(i))
            return entry

    def clear(self):
        self.panel.clear()
        self.queue.clear()
        self.correct_state()

    # --- Execution state related methods ---

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

    def stop(self):
        # stop all threads activity
        self.pause(kill_thpanel=True, kill_thqueue=True)

    def pause_it(self, target):
        t = self.str_to_target(target)
        t.pause()
        self.correct_state()

    def resume_it(self, target):
        t = self.str_to_target(target)
        if t is self:
            self.resume()
        else:
            if not t.is_running:
                t.resume()
        self.correct_state()

    def correct_state(self):
        self.is_running = self.panel.is_running or self.queue.is_running

    # --- Internal methods and misc ---

    def get_mod_by_setid(self, setid, whole_entry=False):
        container = self.get_corresp_set(setid)
        if container is not None:
            if whole_entry:
                return container.get_corresp_entry(setid)
            return container.get_mod_by_id(setid)

    def get_all_setids(self):
        return self.panel.get_idlist(), self.queue.get_idlist()

    def get_corresp_set(self, mod_inst_or_setid):
        # Get which structure is/should be module in, where module either setid or module instance.
        if mod_inst_or_setid in self.panel:
            return self.panel
        if mod_inst_or_setid in self.queue:
            return self.queue

    def str_to_target(self, s):
        if s == "routine":
            return self
        elif s == "panel":
            return self.panel
        elif s == "queue":
            return self.queue

    def check_unique_setid(self):
        # unique ids are guaranteed across both sets
        for setid in self.panel.get_idlist():
            if setid in self.queue.get_idlist():
                return False
        return True

    def rdmize_id(self):
        from random import sample
        from string import ascii_lowercase
        new_id = ''.join(sample(ascii_lowercase, MAX_LENGTH_SETID))
        all_ids = self.panel.get_idlist() + self.queue.get_idlist()
        while new_id in all_ids:
            new_id = ''.join(sample(ascii_lowercase, MAX_LENGTH_SETID))
        return new_id

    def detail_str(self, level=0):
        s = f"\nRoutine in current state : {'RUNNING' if self.is_running else 'PAUSED'}\n" \
            f"\n      <[[ CURRENT PANEL ]]>\n{self.panel.detail_str(level)}" \
            f"\n      <[[ CURRENT QUEUE ]]>\n{self.queue.detail_str(level)}"
        return s

    def __str__(self):
        return self.detail_str()


if __name__ == '__main__':
    from src.utils.timer import TimerThread
    from time import sleep
    from modules.actives import *
    from modules.passives import *

    timer = TimerThread(autostart=True)
    r = Routine(timer=timer)
    r.add_module(mod_inst=nmapExplorer.AModNmapExplorer(), given_timer=20)
    r.add_module(mod_inst=nmapPortDiscovery.AModNmapPortDisc(), given_timer=20)
    r.add_module(mod_inst=nmapPortDiscovery.AModNmapPortDisc(), given_timer=10, setid='nmap2')
    r.add_module(mod_inst=arbitraryCmd.AModArbitraryCmd(), rel_to_vi=['device1', 'device2', 'modem'], given_timer=2000)
    entry = r.add_module(mod_inst=nmapVulners.AModNmapVulners(), given_timer=200)
    r.add_module(mod_inst=nmapVulners.AModNmapVulners(), given_timer=100, setid='toolongsetid01234567')
    entry.set_vi_relative(['othervi'])

    r.add_module(pingTarget.PModPing(timer=timer))
    r.add_module(arbitraryCmdBg.PModArbitraryCmdBg(timer=timer))

    print("### BEFORE RESUMING ###", r.detail_str(4))
    r.resume()
    i = 0
    while i < 5:
        i += 1
        sleep(5)
        print('## Running ..', r.detail_str(3))

    r.pause()
    timer.stop()
    sleep(1)
    print("### AFTER PAUSING ###", r.detail_str(4))