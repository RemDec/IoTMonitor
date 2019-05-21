import sys
from src.appCLI import *
from src.utils.filesManager import FilesManager
import argparse
import os


def is_valid_file(filesmanager, parser, arg):
    if arg is None:
        return None
    arg = filesmanager.complete_path('configs', arg)
    if not os.path.isfile(arg):
        parser.error(f"The file {arg} does not exist!")
    else:
        return arg


if os.getuid() != 0:
    import sys
    print("Please run IoTMonitor as root user")
    sys.exit(0)

filesmanager = FilesManager()

sys.path.extend([os.path.splitext(os.path.abspath(__file__))[0]])

parser = argparse.ArgumentParser(description="Entry point for IoTMonitor application launching.")

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
parser.add_argument("-lvl", "--lvldisplay", type=int, choices=range(0, 4), default=1,
                    help="initial informations display level in app (mutable later by interface)"),
parser.add_argument("--email", help="Email to use for threat alerts, prior to which defined in config file if exists")

args = parser.parse_args()

auto_save = not args.noautosave
use_last_cfg = not args.noautoload


if args.interface == 'cli':
    AppCLI(mode=args.mode, level=args.lvldisplay, save_on_exit=auto_save,
           use_last_coreconfig=use_last_cfg, target_coreconfig=args.fileconfig)
else:
    print("Only CLI interface is implemented ATM, please use argument -i cli or none")
