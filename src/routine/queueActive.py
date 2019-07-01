from src.utils.timer import *
from src.utils.misc_fcts import str_lines_frame, str_multiframe, str_param_comp
from src.routine.moduleContainer import *


class Queue(ModContainer, TimerInterface):

    def __init__(self, timer=None, netmap=None):
        super().__init__(netmap)
        self.timer = timer

    def add_module(self, mod_inst, setid=None, rel_to_vi=[], given_timer=0):
        if not(mod_inst.is_active()) or self.get_presence(mod_inst) >= 0:
            return False
        new_entry = self.get_mod_entry(mod_inst, setid, given_timer)
        for i in range(len(self.set)):
            if new_entry <= self.set[i]:
                self.set.insert(i, new_entry)
                return new_entry
        self.set.append(new_entry)
        if len(rel_to_vi) > 0:
            new_entry.set_vi_relative(rel_to_vi)
        return new_entry

    def clear(self):
        self.pause(kill_thmods=True)
        self.set = []

    def reorganize(self):
        self.set = sorted(self.set, key=lambda mod: mod.get_timer())

    def get_mod_entry(self, mod_inst, setid=None, given_timer=0):
        exp_timer = mod_inst.get_default_timer() if not given_timer else given_timer
        m_id = mod_inst.get_module_id()
        setid = self.get_unique_setid(setid) if setid is not None else self.get_unique_setid(m_id)
        return QueueEntry(mod_inst, setid, exp_timer)

    def resume(self):
        if self.timer is None:
            self.timer = TimerThread()
            self.timer.launch()
        self.timer.subscribe(self)
        self.is_running = True

    def is_decrementable(self):
        return self.is_running

    def decr(self):
        for entry in self.set:
            entry.decr()
        self.reorganize()

    def adaptive_display(self, fct_to_entry, frameit, nbr_per_line=4, header=True):
        s = ""
        if header:
            s = f"Queue of {len(self.set)} active modules (running : {self.is_running})\n"
        if self.is_empty():
            s += " "*5 + "[ empty queue ]\n"
        else:
            if frameit:
                strlist = []
                for i, entry in enumerate(self.set):
                    framed = str_lines_frame(fct_to_entry(entry))
                    strlist.append(framed)
                    if i < self.get_nbr_mods()-1:
                        height = len(strlist[-1].split('\n')) - 3
                        sep = '=>\n'
                        nbr_padding = height//2 if height % 2 == 1 else (height-1)//2
                        padding = '  \n'*nbr_padding
                        strlist.append(f"--\n{padding}{sep*(height-nbr_padding*2)}{padding}--\n")
                s += str_multiframe(strlist, by_pack_of=2*nbr_per_line-1, add_interspace=False)
            else:
                sep = "+"*max(len(s), 20) + "\n"
                for entry in self.set:
                    s += sep
                    s += fct_to_entry(entry)
                s += sep
                return s
        return s


class QueueEntry(Entry):

    def __init__(self, module, setid, exp_timer, rel_to_vi=[]):
        super().__init__(module, setid, rel_to_vi)
        self.exp_timer = exp_timer
        self.init_timer = exp_timer

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

    def get_container_name(self):
        return "QUEUE"

    def detail_str(self, level=0):
        s = f"{self.setid} ~ {self.exp_timer}s/{self.init_timer}"
        if level == 0:
            return str_lines_frame(s)
        elif level == 1:
            return s + f" [{self.get_mod_inst().get_module_id()}]"
        elif level == 2:
            return s + f"\n{self.get_mod_inst().str_summary()}"
        elif level == 3:
            if len(self.rel_to_vi) == 0:
                vistr = "Not specific VI relative"
            else:
                vistr = "VIs: " + ','.join(self.rel_to_vi)
            return s + f"\n{self.get_mod_inst().str_summary()}\n{vistr[:40]}"
        elif level == 4:
            if len(self.rel_to_vi) == 0:
                vistr = "Not specific VI relative"
            else:
                vistr = "VIs: " + ','.join(self.rel_to_vi)
            return s + f"\n{self.get_mod_inst().str_summary()}\n{vistr[:40]}\nThreats /!\\ Modifs -o-"
        elif level == 5:
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


if __name__ == '__main__':
    from modules.actives import *
    from src.net.netmap import Netmap
    q = Queue(netmap=Netmap())
    q.add_module(mod_inst=nmapExplorer.AModNmapExplorer(), given_timer=20)
    q.add_module(mod_inst=nmapPortDiscovery.AModNmapPortDisc(), given_timer=20)
    q.add_module(mod_inst=nmapPortDiscovery.AModNmapPortDisc(), given_timer=10, setid='nmap2')
    q.add_module(mod_inst=arbitraryCmd.AModArbitraryCmd(), rel_to_vi=['device1', 'device2', 'modem'], given_timer=2000)
    entry = q.add_module(mod_inst=nmapVulners.AModNmapVulners(), given_timer=200)
    q.add_module(mod_inst=nmapVulners.AModNmapVulners(), given_timer=100, setid='toolongsetid01234567')
    entry.set_vi_relative(['othervi'])
    print("### BEFORE RESUMING ###")
    print(q.detail_str(4))
    q.resume()
    i = 0
    while i < 5:
        sleep(5)
        i += 1
        print("## Running ...\n", q.detail_str(3))
    q.pause()
    print("### AFTER PAUSING ###\n", q.detail_str(4))
    sleep(5)
    q.timer.stop()
    print(q.netmap.detail_str(level=2))
