from src.appCLI import *
from src.utils.filesManager import FilesManager
from argparse import RawDescriptionHelpFormatter
import argparse
import sys
import os

app_desc = "    Entry point for IoTMonitor launching, a Python > 3.6 application/framework for home\n" \
           "network security supervision. For more details about its features, refer to Github guide :\n" \
           "https://github.com/RemDec/IoTMonitor (you should need an intro to concepts manipulated in).\n" \
           "You can also check the in-app help to be guided, depending chosen interface type.\n" \
           "    One feature of the app is the alert mailing. The only mail account involved is yours!\n" \
           "It is used to send email to an authentication SMTP server with as default destination the\n" \
           "same email address so that you are notified of found threats on your own mailbox. It is why\n" \
           "you have to provide your email credentials (if you want to use this feature with --mail).\n" \
           "    Notes :\n\n" \
           "[*] For now, only CLI interface is available. However, this is coupled with a watching system\n" \
           "    to have a continuous look at app state, considering 3 modes (-m):\n" \
           "        ~ noout is simply no watching excepted by implicit call in CLI interactive interface\n" \
           "        ~ outpiped sends the display stream in a pipe you use as desired (useful for remotely\n" \
           "          use/control app with ssh or in non-graphical environment)\n" \
           "        ~ outscreen spawns a new terminal window whose only job is giving continuously a \n" \
           "          current state overview of selected app elements\n\n" \
           "[*] If you are using console output (and you should) that is default, a terminal is spawned\n" \
           "    displaying continuously app state. To avoid display to be truncated due to inheritance,\n" \
           "    invoke the app in a max-sized terminal (fullscreen preferentially)\n\n" \
           "[*] Some mail services providers as Gmail may ask for a manual config. in order to receive\n" \
           "    such mails. Check this help page : https://support.google.com/accounts/answer/6010255\n\n" \
           "[*] If not given, SMTP server is guessed but it is not 100% reliable. Try to pass it with\n" \
           "    --mserver. If you don't know it, try to look the corresponding entry in\n" \
           "    https://serversmtp.com/smtp-server-address/\n"


def is_valid_file(filesmanager, parser, arg):
    if arg is None:
        return None
    full_path = filesmanager.complete_path('configs', arg)
    if not os.path.isfile(full_path) or not filesmanager.check_file(full_path):
        parser.error(f"The file {full_path} does not exist!")
    else:
        return full_path


if os.getuid() != 0:
    import sys
    print("Please run IoTMonitor as root user")
    sys.exit(1)

filesmanager = FilesManager()

sys.path.extend([os.path.splitext(os.path.abspath(__file__))[0]])

parser = argparse.ArgumentParser(description=app_desc, formatter_class=RawDescriptionHelpFormatter)

parser.add_argument("-i", "--interface",
                    help="user interaction mode with the app (graphical or with inline context menu parser)",
                    choices=("cli", "gui"), default="cli")
parser.add_argument("-m", "--mode", help="which interface mode to use, available modes depend on interface type",
                    choices=cli_modes, default='outscreen')
parser.add_argument("-cfg", "--fileconfig", default=None,
                    type=lambda x: is_valid_file(filesmanager, parser, x),
                    help="path to config file to use (indicating itself others paths considered by the app)")
parser.add_argument("-nas", "--noautosave", help="disable current app state being saved on regular exiting",
                    action="store_true")
parser.add_argument("-nal", "--noautoload", action="store_true",
                    help="disable auto loading of last config and app elements autosaved when exiting")
parser.add_argument("-cln", "--cleanlast", action="store_true",
                    help="clean files resulted from autosave of last app elements state at exiting (/svd/*/last_*)")

parser.add_argument("-lvl", "--lvldisplay", type=int, choices=range(0, 10), default=3,
                    help="initial informations display level in app (mutable later by interface)"),
parser.add_argument("--mail", help="Email to use for threat alerts, prior to which defined in config file if exists")

parser.add_argument("--mserver", help="SMTP server to use for sending mails, not given implies guessing from address")

parser.add_argument("--testmail", help="Set it to send a test email to specified address before app launching",
                    action="store_true")

parser.add_argument("--term", default='xterm',
                    help="Terminal to use for view in cli mode, should be in path or constant 'auto' (default 'xterm')")

parser.add_argument("--installprogs", help="Try to install all underlying programs present in the Modules Library and"
                                           " not yet installed in the system", action="store_true")
args = parser.parse_args()

auto_save = not args.noautosave
use_last_cfg = not args.noautoload
clean_last = args.cleanlast
user_email = args.mail
pwd = None
mail_server = args.mserver
must_test_email = args.testmail
term_cmd = args.term
install = args.installprogs

if install:
    from src.utils.misc_fcts import install_programs
    print("Starting research and installation of lacking underlying programs in this system..\n\n")
    print(install_programs('svd/configs/modlib.xml'))
    exit(0)

if clean_last:
    filesmanager.clean_last_files()

if user_email is not None:
    import getpass
    import re
    email_ok = re.fullmatch(r'(.+)@(.+)\.(.+)', user_email)
    if email_ok is None:
        print("Error, email address must match regular expression", r'(.+)@(.+)\.(.+)')
        sys.exit(1)
    pwd = getpass.unix_getpass(prompt=f"email password [{user_email}] :")
    if must_test_email:
        pass

mail_infos = (user_email, pwd, mail_server)

try:
    if args.interface == 'cli':
        if must_test_email:
            from smtplib import SMTPException
            # Doesn't immediately start parsing that is blocking
            appcli = AppCLI(mode=args.mode, terminal=term_cmd, level=args.lvldisplay, start_parsing=False,
                            start_pull_output=False,
                            save_on_exit=auto_save, use_last_coreconfig=use_last_cfg, target_coreconfig=args.fileconfig,
                            mail_infos=mail_infos)
            try:
                print(f"Testing email with parameters : address {user_email}, SMTP server"
                      f"{appcli.coreconfig.logger_setup.mail_server}\n(check your mailbox) ...")
                appcli.coreconfig.logger_setup.test_mail_service()
            except (SMTPException, OSError) as e:
                print("Email test resulted in an error :", e)
                appcli.stop_app(oppose_to_saving=True)
                exit(1)
            appcli.start_app()
        else:
            AppCLI(mode=args.mode, terminal=term_cmd, level=args.lvldisplay, save_on_exit=auto_save,
                   use_last_coreconfig=use_last_cfg, target_coreconfig=args.fileconfig,
                   mail_infos=mail_infos)
    else:
        print("Only CLI interface is implemented ATM, please use argument -i cli or none")
except Exception as e:
    print("An unexpected exception occurred, try to run the app with --clean and check the parameters you gave are\n"
          "correct following --help description. Also ensure paths present in superconfig file (default\n"
          "svd/configs/last_coreconfig.yaml) are correct.\nPlease report traceback :\n")
    raise e

