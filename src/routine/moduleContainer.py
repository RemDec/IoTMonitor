import abc

MAX_LENGTH_SETID = 15


class ModContainer(abc.ABC):

    def __init__(self, netmap):
        self.netmap = netmap
        self.set = []
        self.is_running = False

    # --- Module entries manipulations ---

    @abc.abstractmethod
    def add_module(self, mod_inst, setid=None, rel_to_vi=[]):
        pass

    def remove_module(self, module):
        ind = self.get_presence(module)
        if ind >= 0:
            self.set.pop(ind)
            return True
        return False

    def clear(self):
        self.pause(kill_thmods=True)
        self.set = []

    @abc.abstractmethod
    def get_mod_entry(self, mod_inst, setid=None):
        pass

    def rename(self, old_setid, new_setid):
        setids = self.get_idlist()
        if old_setid in setids:
            if new_setid in setids:
                # Have to rename already so named entry
                wrong_named = self.get_corresp_entry(new_setid)
                wrong_named.setid = self.get_unique_setid(new_setid)
            curr_entry = self.get_corresp_entry(old_setid)
            curr_entry.setid = new_setid
            return curr_entry

    # --- Execution state ---

    @abc.abstractmethod
    def resume(self):
        pass

    def pause(self, kill_thmods=True):
        self.is_running = False
        if kill_thmods:
            for entry in self.set:
                entry.get_mod_inst().stop()

    # --- Misc ---

    def is_empty(self):
        return len(self.set) == 0

    def get_nbr_mods(self):
        return len(self.set)

    def get_presence(self, module):
        for i, entry in enumerate(self.set):
            if isinstance(module, str) and module == entry.get_setid():
                return i
            if module is entry.get_mod_inst():
                return i
        return -1

    def __contains__(self, mod_inst_or_setid):
        return self.get_presence(mod_inst_or_setid) > -1

    def get_mod_by_id(self, setid):
        for entry in self.set:
            if entry.get_setid() == setid:
                return entry.get_mod_inst()

    def get_corresp_entry(self, mod_inst_or_setid):
        # field either module instance or id
        for entry in self.set:
            if mod_inst_or_setid is entry.get_mod_inst() or mod_inst_or_setid == entry.get_setid():
                return entry

    def get_modentries(self):
        return self.set

    def get_idlist(self):
        return [entry.get_setid() for entry in self.set]

    def get_unique_setid(self, try_id):
        try_id = try_id[:MAX_LENGTH_SETID+1]
        idlist = self.get_idlist()
        if not(try_id in idlist):
            return try_id
        counter = 1
        while try_id + str(counter) in idlist:
            counter += 1
        return try_id + str(counter)

    @abc.abstractmethod
    def adaptive_display(self, fct_to_entry, frameit, nbr_per_line=4, header=True):
        pass

    def detail_str(self, level=0):
        if level < 5:
            return self.adaptive_display(lambda entry: entry.detail_str(level=level), frameit=True,
                                         nbr_per_line=max(level+2, 4), header=True)
        else:
            return self.adaptive_display(lambda entry: entry.detail_str(level=level), False)

    def __str__(self):
        return self.detail_str()


class Entry(abc.ABC):

    def __init__(self, mod_inst, setid, rel_to_vi=[]):
        self.module = mod_inst
        self.setid = setid
        self.rel_to_vi = rel_to_vi

    def set_vi_relative(self, rel_to_vi):
        if isinstance(rel_to_vi, str):
            self.rel_to_vi = [rel_to_vi]
        else:
            self.rel_to_vi = rel_to_vi

    def get_setid(self):
        return self.setid

    def get_mod_inst(self):
        return self.module

    @abc.abstractmethod
    def get_container_name(self):
        pass

    @abc.abstractmethod
    def detail_str(self, level=0):
        pass

