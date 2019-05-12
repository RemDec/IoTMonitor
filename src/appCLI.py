from src.coreConfig import CoreConfig
from src.parsers.parserCLI import CLIparser
from src.appcore import Core
from src.utils.timer import TimerInterface, TimerThread
import subprocess
import os


class AppCLI(TimerInterface):

    def __init__(self, mode=1, level=1, spawn_display=True, save_on_exit=True):
        self.mode = mode
        self.level = level
        self.save_on_exit = save_on_exit
        self.poss_display = ["app", "routine", "indep", "netmap", "timer", "library",
                             "events", "threats", "modifs"]
        self.to_disp = "app"
        self.output = self.config_output()
        self.timer = TimerThread(name="MainTimer")
        self.timer.subscribe(self)
        self.coreconfig = CoreConfig(timer=self.timer)
        self.core = Core(self.coreconfig)

        self.cli = CLIparser(self.core, core_controller=self)
        self.start_app(spawn_display)

    # ----- Control application execution/interactive CLI -----

    def start_app(self, spawn_display=True):
        if spawn_display:
            self.start_display_output()
        # blocking on input waiting
        self.cli.start_parsing()

    def stop_app(self):
        self.cli.stop_parsing()
        self.output.exit()
        if self.save_on_exit:
            pass
        self.core.quit()

    # ----- Managing independent display interface (other terminal, graphical text field, ..)

    def config_output(self):
        if self.mode == 0:
            pass
        elif self.mode == 1:
            return ConsoleOutput()
        elif self.mode == 2:
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
        return self.output.is_reading

    def decr(self):
        to_disp = self.get_current_todisplay()
        self.output.write(to_disp)
        self.output.pull_output()

    def __str__(self):
        return f"Controller of application in CLI mode, app view handled by\n" \
               f"{self.output}\n" \
               f"displaying {self.to_disp} (working:{self.output.is_reading})"


class ConsoleOutput:

    def __init__(self):
        self.PIPE_PATH = "/tmp/output_monitor"
        self.is_reading = False
        self.popen = None
        self.terminal = 'xterm'

    def write(self, to_output):
        # print("Before write", to_output)
        with open(self.PIPE_PATH, 'w') as pipe_w:
            pipe_w.write(to_output)

    def pull_output(self):
        # already done each 0.5 sec by watch command
        pass

    def start_reading(self):
        self.is_reading = True
        if os.path.exists(self.PIPE_PATH):
            os.remove(self.PIPE_PATH)
        os.mkfifo(self.PIPE_PATH)
        self.popen = subprocess.Popen([self.terminal, '-e', 'watch', '-t', '-n 0,5', 'cat %s' % self.PIPE_PATH])

    def stop_reading(self):
        self.is_reading = False

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
            # already done each 0.5 sec by watch command
            pass

        def start_reading(self):
            pass

        def stop_reading(self):
            pass


if __name__ == "__main__":
    ctrler = AppCLI()
