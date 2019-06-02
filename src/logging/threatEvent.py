

class ThreatEvent:

    def __init__(self, from_module, level=1, mapid=None, msg=None, patch=None):
        self.from_module = from_module
        self.level = level
        self.set_threat_lvl(level)
        self.mapid = mapid
        self.msg = msg
        self.patch = patch

    def set_threat_lvl(self, lvl):
        self.level = max(1, min(10, int(lvl)))

    def rel_to_vi(self):
        if self.mapid is None or self.mapid == "":
            return False
        return self.mapid

    def get_level(self):
        return self.level

    def is_serious(self, threshold=3):
        return self.level > threshold

    def get_patch(self):
        if self.patch is None:
            return "No patch available to eliminate the threat"
        return self.patch

    def __eq__(self, other):
        if not isinstance(other, ThreatEvent):
            return False
        return (self.from_module, self.mapid, self.msg) == (other.from_module, other.mapid, other.msg)

    def detail_str(self, level=1):
        for_vi = self.rel_to_vi()
        s = f"/!\\ [{self.level}] threat declared by {self.from_module}{' for '+str(for_vi) if for_vi else ''}\n"
        if level == 1:
            if self.msg is None:
                s += f"    no description provided\n"
            else:
                s += f"    description : {self.msg}\n"
        elif level >= 2:
            if self.msg is None:
                s += f"----| no threat description provided\n"
            else:
                s += f"----| threat description :\n{self.msg}\n"
            if self.patch is None:
                s += f"----| no patch/help for threat provided\n"
            else:
                s += f"----| patch/help provided for threat :\n{self.patch}\n"
        return s

    def __str__(self):
        return self.detail_str()


if __name__ == '__main__':
    th1 = ThreatEvent('scanmodule1', mapid='VirtInst1', msg='exploit detected for this device :CVE-15559.56.23')
    th2 = ThreatEvent('scanmodule1', level=4, mapid='VirtInst2',
                       msg='Several exploitx detected for this device :CVE-40000.10.10, CVE-40000.21.3',
                       patch='Look at update from manufacturer : https://www.samsung.com/be_fr/')
    print(th1.__eq__(th2))