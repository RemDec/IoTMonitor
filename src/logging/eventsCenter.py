from src.logging.threatEvent import *
from src.logging.modifEvent import *
import logging


class EventsCenter:

    def __init__(self, loggers):
        self.loggers = loggers
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

    def get_ordered_events(self):
        pass