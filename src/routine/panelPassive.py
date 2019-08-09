from src.routine.moduleContainer import *
from src.utils.misc_fcts import str_lines_frame, str_param_comp, str_multiframe


class Panel(ModContainer):

    def __init__(self, netmap=None):
        super().__init__(netmap=netmap)

    def add_module(self, mod_inst, setid=None, rel_to_vi=[]):
        # create+add a PanelEntry object if the passive_mod instance not yet in an entry within the panel
        if mod_inst.is_active() or self.get_presence(mod_inst) > -1:
            return False
        new_entry = self.get_mod_entry(mod_inst, setid)
        self.set.append(new_entry)
        return new_entry

    def clear(self):
        self.pause(kill_thmods=True)
        self.set = []
        self.is_running = False

    def get_mod_entry(self, mod_inst, setid=None):
        # return a PanelEntry with adapted pid (no duplicate)
        m_id = mod_inst.get_module_id()
        setid = self.get_unique_setid(m_id) if setid is None else self.get_unique_setid(setid)
        return PanelEntry(mod_inst, setid)

    def resume(self):
        if not self.is_running:
            for entry in self.set:
                entry.launch_module()
            self.is_running = True

    def adaptive_display(self, fct_to_entry, frameit, nbr_per_line=4, header=True):
        s = ""
        if header:
            s = f"Panel composed of {len(self.set)} passive modules (running : {self.is_running})\n"
        if self.is_empty():
            s += " "*5 + "[ empty panel ]\n"
        else:
            if frameit:
                strlist = [str_lines_frame(fct_to_entry(entry)) for entry in self.set]
                s += str_multiframe(strlist, by_pack_of=nbr_per_line, add_interspace=False)
            else:
                sep = "+" * max(len(s), 20) + "\n"
                for entry in self.set:
                    s += sep
                    s += fct_to_entry(entry)
                s += sep
                return s
        return s


class PanelEntry(Entry):

    def __init__(self, module, setid, rel_to_vi=[]):
        super().__init__(mod_inst=module, setid=setid, rel_to_vi=rel_to_vi)

    def launch_module(self):
        self.module.launch(rel_to_vi=self.rel_to_vi)

    def stop_module(self):
        self.module.stop()

    def get_container_name(self):
        return "PANEL"

    def detail_str(self, level=0):
        s = f"{self.setid} ~ {self.module.get_read_interval()}s"
        if level == 0:
            # setid and read interval
            return s
        elif level == 1:
            # adding original module id (not settable as setid)
            return s + f" [{self.get_mod_inst().get_module_id()}]"
        elif level == 2:
            # showing module id threads state
            return s + f"\n{self.get_mod_inst().str_summary()}"
        elif level == 3:
            # adding events icons
            modifs, threats = self.module.get_nbr_events()
            return s + f"\n{self.get_mod_inst().str_summary()}\n      {threats} /!\\   {modifs} -o-"
        elif level == 4:
            # adding VI and summary of results
            if len(self.rel_to_vi) == 0:
                vistr = "Not specific VI relative"
            else:
                vistr = "VIs: " + ','.join(self.rel_to_vi)
            modifs, threats = self.module.get_nbr_events()
            return s + f"\n{self.get_mod_inst().str_summary()}\n{vistr[:40]}\n      {threats} /!\\   {modifs} -o-"
        elif level == 5:
            curr_params, dflt_params, desc_PARAMS = self.module.get_params()
            rel_vi_str = '\n| < no specific VI >' if len(self.rel_to_vi) == 0 else ', '.join(self.rel_to_vi)
            s += f"\n| PASSIVE module whose description is given as :\n"
            s += f"|  {self.module.get_description()}\n"
            modifs, threats = self.module.get_nbr_events()
            s += f"| Events : {threats} /!\\   {modifs} -o-\n"
            s += f"| Execution relative to VIs : {rel_vi_str}\n"
            s += f"| Associated underlying program : {self.module.get_cmd()}\n"
            s += f"| Module parameters :\n"
            s += str_param_comp(curr_params, dflt_params, descriptions=desc_PARAMS, prefix='|  ')
        else:
            curr_params, dflt_params, desc_PARAMS = self.module.get_params()
            rel_vi_str = '| < no specific VI >'
            if len(self.rel_to_vi) > 0 and self.module.netmap is not None:
                rel_vi_str = self.module.netmap.vi_frames(self.module.netmap.get_vi_mapids(subset_mapids=self.rel_to_vi))
            s += f"\n| PASSIVE module whose description is given as :\n"
            s += f"|  {self.module.get_description()}\n"
            s += f"| Associated underlying program : {self.module.get_cmd()}\n"
            modifs, threats = self.module.get_nbr_events()
            s += f"| Threats {threats} /!\\  Modifications {modifs} -o-\n"
            s += f"| Module parameters :\n"
            s += str_param_comp(curr_params, dflt_params, descriptions=desc_PARAMS, prefix='|  ')
            s += f"| Threads registered :\n"
            s += self.module.str_pair_threads() + "|\n"
            b = '\n'
            s += f"| Execution relative to VIs :\n{rel_vi_str}{b if rel_vi_str[-1] != b else ''}"
        return s

    def __str__(self):
        return self.detail_str()


if __name__ == '__main__':
    from src.utils.timer import TimerThread
    from time import sleep
    from modules.passives import *

    timer = TimerThread(autostart=True)
    p = Panel()
    p.add_module(pingTarget.PModPing(timer=timer))
    p.add_module(arbitraryCmdBg.PModArbitraryCmdBg(timer=timer))
    print("### BEFORE RESUMING ###")
    print(p.detail_str(4))
    p.resume()
    i = 0
    while i < 5:
        sleep(5)
        i += 1
        print("## Running ...\n", p.detail_str(3))
    p.pause()
    print("### AFTER PAUSING ###\n", p.detail_str(4))
    sleep(5)
    timer.stop()
