from src.logging.threatEvent import *
from src.logging.modifEvent import *
import logging


class EventsCenter:

    def __init__(self, loggers=[]):
        self.loggers = loggers if isinstance(loggers, list) else [loggers]
        self.MAX_THREATS = 20
        self.MAX_MODIFS = 20
        self.threats = []
        self.modifs = []
        self.last_feedback = []
        self.temp_ind = 0
        self.setup_loggers()

    def setup_loggers(self):
        logging.log_feedback = self.log_feedback
        for i, logger in enumerate(self.loggers):
            logger.register_threat = self.register_threat
            logger.register_modif = self.register_modif
            logger.log_feedback = self.log_feedback

    # --- Registering events in this center and pass it to real loggers ---

    def log_event(self, event, logit_with_lvl, target_logger):
        logging.getLogger(target_logger).log(level=logit_with_lvl, msg=str(event))

    def register_threat(self, from_module, level=1, mapid=None, msg=None, patch=None,
                        logit_with_lvl=-1, target_logger="threat"):

        threat = ThreatEvent(from_module, level, mapid, msg, patch)
        self.register_threat_event(threat)
        if logit_with_lvl > 0:
            self.log_event(threat, logit_with_lvl, target_logger)
        return threat

    def register_modif(self, modified_res, obj_type='app_res', obj_id=None, modificator='app',
                       old_state=None, new_state=None,
                       logit_with_lvl=-1, target_logger="modif"):

        modif = ModifEvent(modified_res, obj_type, obj_id, modificator, old_state, new_state)
        self.register_modif_event(modif)
        if logit_with_lvl > 0:
            self.log_event(modif, logit_with_lvl, target_logger)
        return modif

    def register_threat_event(self, threat_event):
        self.threats.insert(0, (self.temp_ind, threat_event))
        self.temp_ind += 1
        self.check_lengths()

    def register_modif_event(self, modif_event):
        self.modifs.insert(0, (self.temp_ind, modif_event))
        self.temp_ind += 1
        self.check_lengths()

    def log_feedback(self, msg, logitin=None, lvl=10):
        if logitin is not None and logitin in [l.name for l in self.loggers]:
            if isinstance(lvl, str):
                lvl = lvl.upper()
                map_lvl = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING,
                           'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
                lvl = map_lvl[lvl]
            if lvl > 0:
                logging.getLogger(logitin).log(lvl, msg)
        self.feedback(msg)

    def feedback(self, str_fb):
        self.last_feedback.extend(str_fb.split('\n'))

    def pull_feedback(self, nbr_lines=2, nbr_pass=1):
        to_return = '\n'.join(self.last_feedback[:nbr_lines])
        if len(self.last_feedback) > nbr_lines:
            # There are still lines in waiting to be displayed
            self.last_feedback = self.last_feedback[nbr_pass:]
        return to_return + '\n' if len(to_return) > 0 and to_return[-1] != '\n' else ''

    # --- Retrieving events object based on filters ---

    def get_ordered_events(self, filter_fct=lambda x: True, keep_temp=False):
        threats_list = self.get_threat_events(filter_fct=filter_fct, keep_temp=True)
        modifs_list = self.get_modif_events(filter_fct=filter_fct, keep_temp=True)
        events = []
        # latest event are events lists in tail
        j = len(modifs_list) - 1
        for i in range(len(threats_list)-1, -1, -1):
            temp_i, threat = threats_list[i]
            while j >= 0 and modifs_list[j][0] < temp_i:
                # modif event is older than current i threat event
                event = modifs_list[j] if keep_temp else modifs_list[j][1]
                events.insert(0, event)
                j -= 1
            event = (temp_i, threat) if keep_temp else threat
            events.insert(0, event)
        while j >= 0:
            event = modifs_list[j] if keep_temp else modifs_list[j][1]
            events.insert(0, event)
            j -= 1
        return events

    def filter_events(self, target='all', filter_fct=lambda x: True, keep_temp=False):
        if target == 'all':
            target = self.get_ordered_events(filter_fct=filter_fct, keep_temp=True)
        else:
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

    # --- Misc ---

    def check_lengths(self):
        while len(self.threats) > self.MAX_THREATS:
            self.threats.pop()
        while len(self.modifs) > self.MAX_MODIFS:
            self.modifs.pop()

    def detail_str(self, level=0):
        s = f"EventCenter with registered loggers : {', '.join([l.name for l in self.loggers])}\n"
        if level == 0:
            s += f"    | Threats events logged in history : {len(self.threats)}/{self.MAX_THREATS}\n"
            s += f"    | Modifications events logged in history : {len(self.modifs)}/{self.MAX_MODIFS}\n"
        elif level == 1:
            s += f"    | Threats events logged in history ({len(self.threats)}/{self.MAX_THREATS})\n"
            for _, threat in reversed(self.threats):
                s += f"    + {threat.detail_str(level=0)}"
            s += f"    |\n    | Modifications events logged in history ({len(self.modifs)}/{self.MAX_MODIFS})\n"
            for _, modif in reversed(self.modifs):
                s += f"    + {modif.detail_str(level=0)}"
        else:
            pass
        return s

    def __str__(self):
        return self.detail_str(level=1)


if __name__ == '__main__':
    from src.logging.logger_setup import CustomLoggerSetup
    l = CustomLoggerSetup()
    center = EventsCenter([logging.getLogger("debug")])
    center.register_threat("mymodule", 3, "netmapVI_id", "Alert raised by module!")
    center.register_modif("instance MAC field", "virt_inst", "myinst_id", "scanmodule", "unknown", "1C:39:47:12:AA:B3")
    center.register_threat("second_module", 5, "another_mapid", "Very SERIOUS alert!")
    center.register_threat("mymodule", 1, "another_mapid", "Same module raised easy alert")
    print(center)
    print("\n\n##### all event ordered ####\n")
    for event in center.get_ordered_events():
        print(event)
