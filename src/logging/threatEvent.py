

class ThreatEvent:

    def __init__(self, from_module, level=1, mapid=None, msg=None, patch=None):
        self.from_module = from_module
        self.level = level
        self.set_threat_lvl(level)
        self.mapid = mapid
        self.msg = msg
        self.patch = patch

    def set_threat_lvl(self, lvl):
        self.level = max(1, min(5, lvl))

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
