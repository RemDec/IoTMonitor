from src.logging.eventsCenter import *
from src.utils.misc_fcts import replace_in_dicts
from src.utils.filesManager import get_dflt_entry
from src.utils.constants import MAIL_TIMEOUT
import logging
import logging.config
import logging.handlers


class CustomLoggerSetup:
    """Setup of the app logging system from a configuration file (.yaml) formatted as specified by logging std lib

    Instantiate the Event Center with desired loggers obtained from the configuration file. Event Center is the way
    to maintain in the application events to log in the application environment (as object of dedicated classes, not
    only messages). The setup also manages user email configuration : getting corresponding SMTP server, authentication
    to it, reachability test. As loggers are instantiated from a static file, some dynamic modifications may be
    necessary, handled in the form of a function to apply on dictionary obtained from .yaml file parsing.
    """

    def __init__(self, event_center=None, loggers_capture_events="all",
                 email=None, email_pwd=None, mail_server=None,
                 cfg_file=None, fct_modify_loggers=None):
        """

        Args:
            event_center(EventCenter): an instance of EventCenter, None for auto instantiation and loggers customization
            loggers_capture_events(str): target loggers to customize, list of str for multiple or 'all'
            email(str): user email or None for no mail service
            email_pwd(str): user email account password on authenticated SMTP server
            mail_server(str): SMTP server name to use, smtp.gmail.com for exemple. If None, deduced from email
            cfg_file(str): path of the .yaml file to parse in dict from which loggers/handlers are instantiated
            fct_modify_loggers(function): a function to apply on obtained dict, returning the final dict to use
        """

        self.user_email = email
        self.user_pwd = email_pwd
        self.mail_server = mail_server

        self.cfg_file = cfg_file if cfg_file else get_dflt_entry("dflt_logger")
        self.curr_cfg = {}
        fct_modify_loggers = self.cfg_to_defaults if fct_modify_loggers is None else fct_modify_loggers
        self.setup_from_yaml(self.cfg_file, fct_modify_loggers=fct_modify_loggers)
        self.setup_mail_service(user_email=email, user_pwd=email_pwd, mail_server=mail_server)
        self.event_center = self.setup_event_center(loggers_capture_events) if event_center is None else event_center

    def setup_from_yaml(self, file, fct_modify_loggers=lambda cfg_dic: cfg_dic):
        import yaml
        with open(file, 'r') as f:
            cfg_dic = yaml.safe_load(f.read())
        self.curr_cfg = fct_modify_loggers(cfg_dic)
        logging.config.dictConfig(cfg_dic)

    def cfg_to_defaults(self, loaded_cfg):
        general_logs = get_dflt_entry("logs", suffix='general_logs.log')
        replace_in_dicts(loaded_cfg, 'genfile', lambda handler: handler.__setitem__('filename', general_logs))
        event_logs = get_dflt_entry("logs", suffix='events.log')
        replace_in_dicts(loaded_cfg, 'eventfile', lambda handler: handler.__setitem__('filename', event_logs))
        return loaded_cfg

    def setup_event_center(self, which_loggers):
        if which_loggers == "all":
            loggers = self.get_all_loggers()
        elif isinstance(which_loggers, str):
            loggers = [which_loggers]
        else:
            loggers = which_loggers
        loggers_obj = [logging.getLogger(log_name) for log_name in loggers]
        return EventsCenter(loggers_obj)

    # --- Email services ---

    def email_to_server(self, user_email, mail_server):
        if user_email is None:
            return
        import re
        if mail_server is None:
            m = re.search(r'(.+)@(.+)\.(.+)', user_email)
            if m:
                _, host, tld = m.groups()
                self.mail_server = f"smtp.{host}.{tld}"
            else:
                raise AttributeError
        else:
            self.mail_server = mail_server

    def setup_mail_service(self, user_email, user_pwd, mail_server):
        self.user_email = user_email
        self.user_pwd = user_pwd
        self.email_to_server(user_email, mail_server)
        if self.user_email is not None:
            mailhandler = TlsSMTPHandler((self.mail_server, 587), fromaddr=self.user_email,
                                         toaddrs=[self.user_email], subject='IoTMonitor - mail alert service',
                                         credentials=(self.user_email, self.user_pwd))
            logging.getLogger('mail').addHandler(mailhandler)

    def test_mail_service(self):
        if self.user_email is not None:
            test_mailhandler = TlsSMTPHandlerErrorFree((self.mail_server, 587), fromaddr=self.user_email,
                                                       toaddrs=[self.user_email], subject='IoTMonitor - testing mail',
                                                       credentials=(self.user_email, self.user_pwd))
            mail_logger = logging.getLogger('mail')
            old_hdlers = mail_logger.handlers
            mail_logger.handlers = [test_mailhandler]
            mail_logger.critical("This mail has been sent as a test from an IoTMonitor application, more details here:"
                                 "https://github.com/RemDec/IoTMonitor")
            mail_logger.handlers = old_hdlers

    # --- Misc ---

    def get_all_loggers(self):
        return self.curr_cfg.get('loggers', {}).keys()

    def get_event_center(self):
        return self.event_center

    def email_str(self):
        if self.user_email is None:
            return "No user email configured"
        return f"Contact email {self.user_email} (SMTP server {self.mail_server})"

    def detail_str(self, level=0):
        if level == 0:
            return f"LoggerSetup using cfg {self.cfg_file}"
        elif level >= 1:
            return f"LoggerSetup using config file {self.cfg_file}\n{self.email_str()}"

    def __str__(self):
        return self.detail_str()


class TlsSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        try:
            import smtplib
            try:
                from email.utils import formatdate
            except ImportError:
                import time
                formatdate = lambda: str(time.time())
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port, timeout=MAIL_TIMEOUT)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                self.fromaddr,
                ','.join(self.toaddrs),
                self.getSubject(record),
                formatdate(), msg)
            if self.username:
                smtp.ehlo()  # for tls add this line
                smtp.starttls()  # for tls add this line
                smtp.ehlo()  # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except Exception as e:
            msg = f"Exception at mail sending for : {self.fromaddr} (SMTP server {self.mailhost})"
            logging.getLogger('error').exception(msg)


class TlsSMTPHandlerErrorFree(logging.handlers.SMTPHandler):
    def emit(self, record):
        import smtplib
        try:
            from email.utils import formatdate
        except ImportError:
            import time
            formatdate = lambda: str(time.time())
        port = self.mailport
        if not port:
            port = smtplib.SMTP_PORT
        smtp = smtplib.SMTP(self.mailhost, port, timeout=MAIL_TIMEOUT)
        msg = self.format(record)
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
            self.fromaddr,
            ','.join(self.toaddrs),
            self.getSubject(record),
            formatdate(), msg)
        if self.username:
            smtp.ehlo()  # for tls add this line
            smtp.starttls()  # for tls add this line
            smtp.ehlo()  # for tls add this line
            smtp.login(self.username, self.password)
        smtp.sendmail(self.fromaddr, self.toaddrs, msg)
        smtp.quit()


if __name__ == "__main__":
    l = CustomLoggerSetup()
    print(l)
    logging.getLogger("cli").debug("Logger that alert user in cli directly")
    logging.getLogger("mail").critical("Critical thread sent by email")
