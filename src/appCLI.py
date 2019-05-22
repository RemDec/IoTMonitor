from src.coreConfig import CoreConfig
from src.parsers.parserCLI import CLIparser
from src.appcore import Core
from src.utils.timer import TimerInterface, TimerThread
from src.coreConfig import get_coreconfig_from_file
from src.utils.filesManager import FilesManager
import subprocess
import os


cli_modes = ('noout', 'outpiped', 'outscreen', 'tkinter')


class AppCLI(TimerInterface):

    def __init__(self, mode=cli_modes[2], level=1, start_pull_output=True, save_on_exit=True,
                 use_last_coreconfig=True, target_coreconfig=None):
        self.mode = mode
        self.level = level
        self.save_on_exit = save_on_exit # Save core components state at regular app exiting
        self.poss_display = ["app", "routine", "indep", "netmap", "timer", "library",
                             "events", "threats", "modifs"]
        self.to_disp = "app"
        self.output = self.config_output()  # Init output controller object depending on mode selected
        self.filemanager = FilesManager()
        self.paths = {'config': self.filemanager.get_res_path('last_cfg'),
                      'routine': self.filemanager.get_res_path('last_routine'),
                      'netmap': self.filemanager.get_res_path('last_netmap')}
        self.timer = TimerThread(name="MainTimer")
        self.timer.subscribe(self)
        if target_coreconfig is not None:
            self.coreconfig = get_coreconfig_from_file(filepath=target_coreconfig, timer=self.timer)
        elif use_last_coreconfig:
            self.coreconfig = get_coreconfig_from_file(filepath=self.filemanager.get_res_path("last_cfg"), timer=self.timer)
        else:
            self.coreconfig = CoreConfig(timer=self.timer)
        self.core = Core(self.coreconfig)

        self.cli = CLIparser(self.core, core_controller=self)
        self.start_app(start_pull_output)

    # ----- Control application execution/interactive CLI -----

    def start_app(self, start_display=True):
        if self.mode != 'noout' and start_display:
            self.start_display_output()
        # blocking on input waiting
        self.cli.start_parsing()

    def stop_app(self):
        self.cli.stop_parsing()
        self.timer.unsub(self)
        self.output.exit()
        if self.save_on_exit:
            self.save_app_state()
        self.core.quit()

    # ----- Save application components and config into files -----

    def save_routine(self, filepath=None):
        from src.parsers.routineParser import write_routine_XML
        filepath = filepath if filepath is not None else self.paths['routine']
        write_routine_XML(self.core.routine, filepath=self.filemanager.complete_path('routines', filepath))

    def save_netmap(self, filepath=None):
        from src.parsers.netmapParser import write_netmap_XML
        filepath = filepath if filepath is not None else self.paths['netmap']
        write_netmap_XML(self.core.netmap, filepath=filepath)

    def save_coreconfig(self, filepath=None, routine_path=None, netmap_path=None):
        from src.parsers.coreConfigParser import config_to_YAML
        routine_path = routine_path if routine_path is not None else self.paths['routine']
        netmap_path = netmap_path if netmap_path is not None else self.paths['netmap']
        filepath = filepath if filepath is not None else self.paths['config']
        config_to_YAML(self.coreconfig, filepath=filepath, XML_path_routine=routine_path, XML_path_netmap=netmap_path)

    def save_app_state(self, config_path=None, routine_path=None, netmap_path=None):
        self.save_routine(routine_path)
        self.save_netmap(netmap_path)
        self.save_coreconfig(config_path, routine_path, netmap_path)

    def save_target(self, target, filepath):
        pass

    # ----- Managing independent display interface (other terminal, graphical text field, ..)

    def config_output(self):
        if isinstance(self.mode, int):
            ind = min(max(self.mode, 0), len(cli_modes))
            self.mode = cli_modes[ind]
        if self.mode == 'noout':
            return NoOutput()
        elif self.mode == 'outpiped':
            return PipeOutput()
        elif self.mode == 'outscreen':
            return ConsoleOutput()
        elif self.mode == 'tkinter':
            return TkinterOutput(self)

    def start_display_output(self):
        self.output.start_reading()

    def stop_display_output(self):
        self.output.stop_reading()

    def set_level(self, new_lvl):
        if 0 <= new_lvl <= 2:
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
        return f"Controller of application in CLI mode, app view handled by\n" \
               f"{self.output}\n" \
               f"displaying {self.to_disp} (working:{self.output.is_reading()})"


class NoOutput:

    def __init__(self):
        pass

    def write(self, to_output):
        pass

    def pull_output(self):
        pass

    def start_reading(self):
        pass

    def stop_reading(self):
        pass

    def is_reading(self):
        return False

    def exit(self):
        pass

    def __str__(self):
        return "NoOutput object - informations taken from app core are not automatically displayed"


class PipeOutput:

    def __init__(self):
        self.PIPE_PATH = "/tmp/output_monitor"
        self.reading = False

    def write(self, to_output):
        self.reading = True
        with open(self.PIPE_PATH, 'w') as pipe_w:
            pipe_w.write(to_output)

    def pull_output(self):
        # Let the user make it's own utility of information in pipe
        pass

    def start_reading(self):
        if os.path.exists(self.PIPE_PATH):
            os.remove(self.PIPE_PATH)
        os.mkfifo(self.PIPE_PATH)

    def is_reading(self):
        return self.reading

    def stop_reading(self):
        self.reading = False

    def exit(self):
        self.stop_reading()
        if os.path.exists(self.PIPE_PATH):
            os.remove(self.PIPE_PATH)

    def __str__(self):
        return "PipeOutput object - informations are sent in a pipe, which you can do whatever with (recommanded" \
               " use watch command on it).\nPipe descriptor : " + self.PIPE_PATH


class ConsoleOutput:

    def __init__(self):
        self.PIPE_PATH = "/tmp/output_monitor"
        self.reading = False
        self.popen = None
        self.terminal = 'xterm'

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
        self.popen = subprocess.Popen([self.terminal, '-geometry', '150x70+0+0', '+aw', '-e', 'watch', '-t', '-n 0,5', 'cat %s' % self.PIPE_PATH])

    def stop_reading(self):
        self.reading = False

    def is_reading(self):
        return self.reading

    def exit(self):
        self.stop_reading()
        if self.popen is not None:
            self.popen.terminate()
            if self.popen.poll() is None:
                self.popen.kill()

    def __str__(self):
        return f"ConsoleOutput spawning {self.terminal} monitoring app state pulling info from pipe\n" \
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
