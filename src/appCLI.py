from src.coreConfig import CoreConfig
from src.parsers.parserCLI import CLIparser
from src.appcore import Core
from src.utils.timer import TimerInterface, TimerThread
from src.coreConfig import get_coreconfig_from_file
from src.utils.filesManager import FilesManager
from src.utils.misc_fcts import log_feedback_available
import subprocess
import signal
import os


cli_modes = ('noout', 'outpiped', 'outscreen')
terms = {'xterm': ['xterm', '-geometry', '150x70+0+0', '+aw', '-e'],
         'konsole': ['konsole', '-e'],
         'gnome': ['gnome-terminal', '-e'],
         'gnome-terminal': ['gnome-terminal', '-e'],
         'auto': ['x-terminal-emulator', '-e']}


class AppCLI(TimerInterface):
    """Global controller instantiating and maintaining all parts of application : logic, CLI interface and View"""

    def __init__(self, mode=cli_modes[2], terminal=None, level=1, start_parsing=True, start_pull_output=True,
                 save_on_exit=True, use_last_coreconfig=True, target_coreconfig=None, check_files=True,
                 mail_infos=None):
        """

        Args:
            mode(str): a constant string corresponding to the desired View mode : nouout, outpiped or outsreen
            terminal(str): if outscreen, indicates the terminal emulator to use for view screen
            level(int): the detail level for displayed resource in view
            start_parsing(bool): make the current terminal as the CLI interface directly after all parts instantiated
            start_pull_output(bool): start the view display directly after all parts instantiated
            save_on_exit(bool): whether state of app components should be saved in their attributed file at exiting
            use_last_coreconfig(bool): whether should load from files given in last_coreconfig.xml
            target_coreconfig(str): the master file to use for configuration (not used if use_last_coreconfig is true)
            check_files(str): whether a verification of existence of used files should be done before app running
            mail_infos(str tuple): mail information given by the user, form (email, email_pwd, mail_server)
        """
        self.mode = self.correct_mode(mode)
        self.level = level
        self.save_on_exit = save_on_exit # Save core components state at regular app exiting
        self.poss_display = ["app", "routine", "indep", "netmap", "timer", "library", "config",
                             "events", "threats", "modifs", "feedback"]
        self.to_disp = "app"
        # Check whether essential files are in place
        self.filemanager = FilesManager()
        if check_files:
            self.filemanager.check_all_files()
        # Instantiate app configuration and components
        self.timer = TimerThread(name="MainTimer")
        self.timer.subscribe(self)
        if target_coreconfig is not None:
            fullpath = self.filemanager.complete_path('configs', target_coreconfig)
            self.coreconfig = get_coreconfig_from_file(filepath=fullpath, timer=self.timer, mail_infos=mail_infos)
        elif use_last_coreconfig:
            dflt_path_last_cfg = self.filemanager.get_res_path("last_cfg")
            self.coreconfig = get_coreconfig_from_file(filepath=dflt_path_last_cfg, timer=self.timer,
                                                       mail_infos=mail_infos)
        else:
            self.coreconfig = CoreConfig(timer=self.timer)
            self.coreconfig.set_mailinfos_tuple(mail_infos)
        self.core = Core(self.coreconfig, handle_sigint=False)
        self.paths = self.coreconfig.paths

        self.output = self.config_output(terminal)  # Init output controller object depending on mode selected
        self.cli = CLIparser(self.core, core_controller=self)
        signal.signal(signal.SIGINT, self.interrupt_handler)

        self.start_app(start_parsing, start_pull_output)

    # ----- Control application execution/interactive CLI -----

    def start_app(self, start_parsing=True, start_display=True):
        if start_display:
            self.start_display_output()
        if start_parsing:
            # blocking on input waiting
            self.cli.start_parsing()

    def interrupt_handler(self, sig, frame):
        log_feedback_available(f"AppController : handling interrupt signal {sig}")
        self.stop_app()

    def stop_app(self, oppose_to_saving=False):
        self.cli.stop_parsing()
        self.timer.unsub(self)
        self.output.exit()
        if not(oppose_to_saving) and self.save_on_exit:
            self.save_app_state()
        self.core.quit()

    # ----- Save application components and config into files -----

    def save_routine(self, filepath=None):
        from src.parsers.routineParser import write_routine_XML
        filepath = filepath if filepath is not None else self.coreconfig.paths['routine']
        full_path = self.filemanager.complete_path('routines', filepath)
        write_routine_XML(self.core.routine, filepath=full_path)
        return full_path

    def set_current_routine(self, new_filepath):
        self.coreconfig.paths['routine'] = new_filepath

    def save_netmap(self, filepath=None):
        from src.parsers.netmapParser import write_netmap_XML
        filepath = filepath if filepath is not None else self.coreconfig.paths['netmap']
        full_path = self.filemanager.complete_path('netmaps', filepath)
        write_netmap_XML(self.core.netmap, filepath=full_path)
        return full_path

    def set_current_netmap(self, new_filepath):
        self.coreconfig.paths['netmap'] = new_filepath

    def save_coreconfig(self, filepath=None, routine_path=None, netmap_path=None):
        from src.parsers.coreConfigParser import config_to_YAML
        routine_path = routine_path if routine_path is not None else self.coreconfig.paths['routine']
        netmap_path = netmap_path if netmap_path is not None else self.coreconfig.paths['netmap']
        filepath = filepath if filepath is not None else self.coreconfig.paths['config']
        full_path = self.filemanager.complete_path('configs', filepath)
        config_to_YAML(self.coreconfig,
                       filepath=full_path,
                       XML_path_routine=self.filemanager.complete_path('routines', routine_path),
                       XML_path_netmap=self.filemanager.complete_path('netmaps', netmap_path))
        return full_path

    def set_current_coreconfig(self, new_filepath):
        self.coreconfig.paths['config'] = new_filepath

    def save_app_state(self, config_path=None, routine_path=None, netmap_path=None):
        self.save_routine(routine_path)
        self.save_netmap(netmap_path)
        self.save_coreconfig(config_path, routine_path, netmap_path)

    def save_target(self, target, filepath):
        pass

    # ----- Managing the view (other terminal, graphical text field, ..)

    def correct_mode(self, mode):
        return mode if mode in cli_modes else cli_modes[2]

    def config_output(self, terminal=None):
        if isinstance(self.mode, int):
            ind = min(max(self.mode, 0), len(cli_modes))
            self.mode = cli_modes[ind]
        if self.mode == 'noout':
            return NoOutput()
        elif self.mode == 'outpiped':
            return PipeOutput()
        elif self.mode == 'outscreen':
            return ConsoleOutput(terminal)
        elif self.mode == 'tkinter':
            return TkinterOutput(self)

    def start_display_output(self):
        self.output.start_reading()

    def stop_display_output(self):
        self.output.stop_reading()

    def exit_view(self):
        self.output.stop_reading()
        self.output.exit()

    def reset_view(self):
        self.output.stop_reading()
        self.output.exit()
        self.output.start_reading()

    def change_view_mode(self, new_mode, terminal=None):
        self.timer.unsub(self)
        self.exit_view()
        self.mode = self.correct_mode(new_mode)
        self.output = self.config_output(terminal)
        self.start_display_output()
        self.timer.subscribe(self)

    def set_level(self, new_lvl):
        if 0 <= new_lvl <= 10:
            self.level = new_lvl

    def get_level(self):
        return self.level

    def set_current_todisplay(self, target):
        if target in self.poss_display:
            self.to_disp = target
            return True
        return False

    def get_current_todisplay(self):
        str_to_disp = self.core.get_display(self.to_disp, level=self.level)
        return str_to_disp if str_to_disp != '' else f"< blank display returned for {self.to_disp}>"

    # ----- Using timer to regenerate display content and refresh displayed output -----

    def is_decrementable(self):
        return self.output.is_reading()

    def decr(self):
        to_disp = self.get_current_todisplay()
        self.output.write(to_disp)
        self.output.pull_output()

    def __str__(self):
        return f"Controller of application in CLI mode  (working:{self.output.is_reading()}), app view handled by\n" \
               f"{self.output}\n" \
               f"displaying {self.to_disp}"


# --- Manipulation of app View ---

class BaseOutput:
    """Object managing the View part of the application, allowing user to see what's going on during its execution

    The view can be presented in various ways, but is basically a string to write somewhere and after perhaps read it
    to retrieve display information to user. This string is the representation of the targeted resource to view,
    selected by the user in function of what he would like to observe.
    """

    def __init__(self):
        self.reading = False

    def write(self, to_output):
        """Define the way the information to display should be manipulated, called regularly if set as 'reading'

        Args:
            to_output(str): the string to display, representation of the selected resource
        """
        pass

    def pull_output(self):
        """Action triggered after each writing, likely displaying the information visually to the user"""
        pass

    def start_reading(self):
        self.reading = True

    def stop_reading(self):
        self.reading = False

    def is_reading(self):
        """Whether the View should be updated with new display information"""
        return self.reading

    def exit(self):
        """Stop the displaying activity and all underlying processes involved in"""
        pass

    def __str__(self):
        return "Base class for an object allowing manipulation of application View"


class NoOutput(BaseOutput):

    def is_reading(self):
        return False

    def __str__(self):
        return "NoOutput object - information taken from app core are not automatically displayed"


class PipeOutput(BaseOutput):
    """Feed information to normally display in a readable pipe, usable by the user as he pleases

    Especially useful for user in a non graphical environment (using app remotely with ssh for example)
    """

    def __init__(self):
        super().__init__()
        self.PIPE_PATH = "/tmp/output_monitor"

    def write(self, to_output):
        with open(self.PIPE_PATH, 'w') as pipe_w:
            pipe_w.write(to_output)

    def start_reading(self):
        self.reading = True
        if os.path.exists(self.PIPE_PATH):
            os.remove(self.PIPE_PATH)
        os.mkfifo(self.PIPE_PATH)

    def exit(self):
        self.stop_reading()
        if os.path.exists(self.PIPE_PATH):
            os.remove(self.PIPE_PATH)
        log_feedback_available(f"PipeOutput : stop feeding the pipe {self.PIPE_PATH} and removing it")

    def __str__(self):
        return "PipeOutput object - informations are sent in a pipe, which you can do whatever with (recommanded" \
               " use watch command on it).\nPipe descriptor : " + self.PIPE_PATH


class ConsoleOutput(BaseOutput):
    """Usable view in a graphical environment, displaying the targeted resource regularly

    In background, feed a pipe but also spawn a terminal emulator in a new window, running 'watch' Linux command on
    its content to update the view of the resource to display."""

    def __init__(self, terminal=None):
        super().__init__()
        from src.utils.misc_fcts import verify_program
        self.PIPE_PATH = "/tmp/output_monitor"
        self.popen = None
        self.terminal_key = 'xterm' if terminal is None else terminal
        self.terminal_cmd = terms.get(self.terminal_key, [self.terminal_key])
        verify_program(self.terminal_cmd[0])

    def write(self, to_output):
        # Write where this object want to bufferise the information to display
        with open(self.PIPE_PATH, 'w') as pipe_w:
            pipe_w.write(to_output)

    def pull_output(self):
        # Take the information in buffer where write() placed it and display it
        # already done each 0.5 sec by watch command
        pass

    def start_reading(self):
        self.reading = True
        if os.path.exists(self.PIPE_PATH):
            os.remove(self.PIPE_PATH)
        os.mkfifo(self.PIPE_PATH)
        self.popen = subprocess.Popen(self.terminal_cmd+['watch', '-t', '-n 0,5', 'cat %s' % self.PIPE_PATH],
                                      stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

    def exit(self):
        self.stop_reading()
        if self.popen is not None:
            self.popen.terminate()
            if self.popen.poll() is None:
                self.popen.kill()
        log_feedback_available(f"ConsoleOutput : killing the terminal process ({self.terminal_cmd}) that was watching"
                               f"pipe {self.PIPE_PATH}")

    def __str__(self):
        return f"ConsoleOutput spawning '{self.terminal_key}' terminal monitoring app state pulling info from pipe\n" \
               f"{self.PIPE_PATH} using watch command to regularly display it"


class TkinterOutput:

    def __init__(self, appcli):
        # textual field for output display and graphical interface to control appcli (level, res to disp,..)
        self.appcli = appcli

    def write(self, to_output):
        pass

    def pull_output(self):
        pass

    def start_reading(self):
        pass

    def stop_reading(self):
        pass

    def __str__(self):
        return "TkinterOutput : display in a more friendly way app informations, with some GUI interactions on it"


if __name__ == "__main__":
    ctrler = AppCLI()
