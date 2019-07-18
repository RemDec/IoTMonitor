from src.logging.threatEvent import *
from src.logging.modifEvent import *
from src.logging.feedback import Feedback
from src.utils.constants import MAX_MODIFS, MAX_THREATS
import logging


class EventsCenter:
    """Gathering object for all Events objects, keeping an 'object' trace of it in the app (more than just pure logging)

    Some existing Logger objects from logging lib can be passed to at instantiation. Such loggers instances will be
    customized with new features aiming to provide the possibility to interact directly with the application event
    center to register events in it, such that this is not only pure logging in files etc. but also keeping a trace
    of events in application environment. So events can still be manipulated, sorted, filtered depending the needs.

    This object has 2 jobs :
       - Being a congruence center for Events declaration and registering, where Events are objects of 2 types : Threats
       and Modifications. Such objects can be instantiated outside this class, but methods provided in permit to avoid
       instantiation (see register_*). Register events are chronologically maintained but are limited in number.
       - Customizing standard library module logging by declaring new methods for the module and instantiated loggers.
       So these methods are facilities that can be accessed from anywhere in the code just by importing standard logging
       module and calling new methods set on it by EventCenter at instantiation.
    """

    def __init__(self, loggers=[]):
        self.loggers = loggers if isinstance(loggers, list) else [loggers]
        self.threats = []
        self.modifs = []
        self.last_feedback = []
        self.temp_ind = 0
        self.setup_loggers()
        self.feedback_queue = Feedback()

    def setup_loggers(self):
        logging.log_feedback = self.log_feedback
        for i, logger in enumerate(self.loggers):
            logger.register_threat = self.register_threat
            logger.register_modif = self.register_modif
            logger.log_feedback = self.log_feedback

    # --- Registering events in this center and pass it to real loggers ---

    def log_event(self, event, logit_with_lvl, target_logger):
        """Log an event in a existing target logger with a given level, or root logger if non existing in logging

        Args:
            event: string to log in the target logger
            logit_with_lvl: int ranging from 0 to 50 or a constant as defined by python standard library logging
            target_logger: a string, name of the target logger (already existing and referenced through logging lib)
        """
        logging.getLogger(target_logger).log(level=logit_with_lvl, msg=str(event))

    def register_threat(self, from_module, level=1, mapid=None, msg=None, patch=None,
                        logit_with_lvl=-1, target_logger="threats", avoid_duplicate=True):
        """Register a new threat object instantiated from given parameters and may log this threat declaration

        Args:
            from_module(str): id of the module declaring the threat
            level(int): the dangerosity level of the threat
            mapid(str): mapid of the VI concerned by the threat
            msg(str): string detailing the threat
            patch(str): string describing a possible patch for the threat
            logit_with_lvl(int): level of logging, -1 if no logging desired
            target_logger(str): name of the target logger
            avoid_duplicate(bool): whether should avoid registering the threat if same threat has already been
                                   registered previously

        Returns:
            The threat event object instantiated
        """
        threat = ThreatEvent(from_module, level, mapid, msg, patch)
        if not(self.event_already_exists(threat)) or not avoid_duplicate:
            self.register_threat_event(threat)
            if logit_with_lvl > 0:
                self.log_event(threat, logit_with_lvl, target_logger)
        return threat

    def register_modif(self, modified_res, obj_type='app_res', obj_id=None, modificator='app',
                       old_state=None, new_state=None,
                       logit_with_lvl=-1, target_logger="modifs"):
        """Register a new modification object instantiated from given parameters and may log this modifi declaration

        Args:
            modified_res(str): describes object concerned by the modification event
            obj_type:
            obj_id(str): id of the modified resource/object in the application (likely mapid/module id)
            modificator(str): name or id of the entity that modified the resource
            old_state(str): old value of the modified resource
            new_state(str): new value
            logit_with_lvl(int): level of logging, -1 if no logging desired
            target_logger(str): name of the target logger

        Returns:
            The modification event object instantiated
        """
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
        """Register a message in the feedback memory with possibility to also log it in normal logging system

        Args:
            msg(str): the message to push in the feedback
            logitin(str): target logger name or None if no normal logging desired for the message
            lvl(int): int or string corresponding to logging level
        """
        if logitin is not None and logitin in [l.name for l in self.loggers]:
            if isinstance(lvl, str):
                lvl = lvl.upper()
                map_lvl = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING,
                           'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
                lvl = map_lvl.get(lvl, logging.DEBUG)
            if lvl > 0:
                logging.getLogger(logitin).log(lvl, msg)
        self.feedback(msg)

    # --- Feedback communication ---

    def get_feedback(self):
        return self.feedback_queue

    def feedback(self, str_fb):
        """Feed the feedback content with new strings, split based on newline character"""
        self.feedback_queue.feed(str_fb)

    def pull_feedback(self, nbr_lines=2, nbr_pass=1):
        return self.feedback_queue.pull_feedback(nbr_lines, nbr_pass)

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

    def event_already_exists(self, tomatch):
        return len(self.filter_events(filter_fct=lambda event: event == tomatch)) > 0

    def check_lengths(self):
        while len(self.threats) > MAX_THREATS:
            self.threats.pop()
        while len(self.modifs) > MAX_MODIFS:
            self.modifs.pop()

    def detail_str(self, level=0):
        s = f"EventCenter with registered loggers : {', '.join([l.name for l in self.loggers])}\n"
        if level == 0:
            s += f"    | Threats events logged in history : {len(self.threats)}/{MAX_THREATS}\n"
            s += f"    | Modifications events logged in history : {len(self.modifs)}/{MAX_MODIFS}\n"
        elif level == 1:
            s += f"    | Threats events logged in history ({len(self.threats)}/{MAX_THREATS})\n"
            for _, threat in reversed(self.threats):
                s += f"    + {threat.detail_str(level=0)}"
            s += f"    |\n    | Modifications events logged in history ({len(self.modifs)}/{MAX_MODIFS})\n"
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
