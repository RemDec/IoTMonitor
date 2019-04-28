from src.logging.threatEvent import *
from src.logging.modifEvent import *
import logging


class EventsCenter:

    def __init__(self, loggers):
        self.loggers = loggers if isinstance(loggers, list) else [loggers]

        self.MAX_THREATS = 20
        self.MAX_MODIFS = 20
        self.threats = []
        self.modifs = []
        self.temp_ind = 0
        self.setup_loggers()

    def setup_loggers(self):
        for logger in self.loggers:
            logger.register_threat = self.register_threat
            logger.register_modif = self.register_modif

    def register_threat(self, from_module, level=1, mapid=None, msg=None, patch=None,
                        logit_with_lvl=-1, target_logger="threat"):

        threat = ThreatEvent(from_module, level, mapid, msg, patch)
        self.register_threat_event(threat)
        if logit_with_lvl > 0:
            self.log_event(threat, logit_with_lvl, target_logger)

    def register_modif(self, modified_res, obj_type='app_res', obj_id=None, modificator='app',
                       old_state=None, new_state=None,
                       logit_with_lvl=-1, target_logger="modif"):

        modif = ModifEvent(modified_res, obj_type, obj_id, modificator, old_state, new_state)
        self.register_modif_event(modif)
        self.register_threat_event(modif)
        if logit_with_lvl > 0:
            self.log_event(modif, logit_with_lvl, target_logger)

    def register_threat_event(self, threat_event):
        self.threats.insert(0, (self.temp_ind, threat_event))
        self.temp_ind += 1
        self.check_lengths()

    def register_modif_event(self, modif_event):
        self.modifs.insert(0, (self.temp_ind, modif_event))
        self.temp_ind += 1
        self.check_lengths()

    def check_lengths(self):
        while len(self.threats) > self.MAX_THREATS:
            self.threats.pop()
        while len(self.modifs) > self.MAX_MODIFS:
            self.modifs.pop()

    def log_event(self, event, logit_with_lvl, target_logger):
        logging.getLogger(target_logger).log(level=logit_with_lvl, msg=str(event))

    def get_ordered_events(self, filter_fct=lambda x: True):
        threats_list = self.get_threat_events(filter_fct=filter_fct, keep_temp=True)
        modifs_list = self.get_modif_events(filter_fct=filter_fct, keep_temp=True)
        events = []
        # latest event are events lists in tail
        j = len(modifs_list) - 1
        for i in range(len(threats_list)-1, -1, -1):
            temp_i, threat = threats_list[i]
            while j >= 0 and modifs_list[j][0] < temp_i:
                # modif event is older than current i threat event
                events.insert(0, modifs_list[j][1])
                j -= 1
            events.insert(0, threat)
        while j >= 0:
            events.insert(0, modifs_list[j][1])
            j -= 1
        return events

    def filter_events(self, target, filter_fct=lambda x: True, keep_temp=False):
        target = self.threats if target == "threats" else self.modifs
        filtered = []
        for temp, event in target:
            if filter_fct(event):
                filtered.append((temp, event) if keep_temp else event)
        return filtered

    def get_threat_events(self, filter_fct=lambda x: True, keep_temp=False):
        return self.filter_events(target="threats", filter_fct=filter_fct, keep_temp=keep_temp)

    def get_modif_events(self, filter_fct=lambda x: True, keep_temp=False):
        return self.filter_events(target="modifs", filter_fct=filter_fct, keep_temp=keep_temp)

    def detail_str(self, level=0):
        s = f"EventCenter with registered loggers : {', '.join([l.name for l in self.loggers])}\n"
        if level == 0:
            s += f"    | Threats events logged in history : {len(self.threats)}/{self.MAX_THREATS}\n"
            s += f"    | Modifications events logged in history : {len(self.modifs)}/{self.MAX_MODIFS}\n"
        elif level == 1:
            s += f"    | Threats events logged in history ({len(self.threats)}/{self.MAX_THREATS})\n"
            for _, threat in reversed(self.threats):
                s += f"    + {threat.detail_str(level=0)}"
            s += f"    |\n    | Modifications events logged in history {len(self.modifs)}/{self.MAX_MODIFS}\n"
            for _, modif in reversed(self.modifs):
                s += f"    + {modif.detail_str(level=0)}"
        else:
            pass
        return s

    def __str__(self):
        return self.detail_str(level=1)


if __name__ == '__main__':
    from src.logging.logger import *
    l = Logger()
    center = EventsCenter(logging.getLogger("debug"))
    center.register_threat("mymodule", 3, "netmapVI_id", "Alert raised by module!")
    center.register_modif("instance MAC field", "virt_inst", "myinst_id", "scanmodule", "unknown", "1C:39:47:12:AA:B3")
    #print(center)
    print("\n\n##### ordered ####\n", str(center.get_ordered_events()))
