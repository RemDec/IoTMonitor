from src.parserCLI import *
from src.utils.timer import *
from src.utils.logger import *
from src.appcore import *
import subprocess, os


class AppCLI(TimerInterface):

    def __init__(self, mode=1, level=0, spawn_display=True):
        self.mode = mode
        self.level = level
        self.to_disp = "app"
        self.output = self.config_output()
        self.timer = TimerThread(name="MainTimer")
        self.timer.subscribe(self)
        self.core = Core(timer=self.timer)

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

    def set_current_todisplay(self, target):
        self.to_disp = target

    def get_current_todisplay(self):
        if self.to_disp == "app":
            return self.get_todisplay_app()
        elif self.to_disp == "routine":
            pass
        elif self.to_disp == "netmap":
            pass
        elif self.to_disp == "indep":
            pass
        elif self.to_disp == "library":
            pass

    def get_todisplay_app(self):
        return self.core.__str__()

    # ----- Using timer to regenerate display content and refresh displayed output -----

    def is_decrementable(self):
        return self.output.is_reading

    def decr(self):
        to_disp = self.get_current_todisplay()
        # print("Decr appCLI to send output", to_disp)
        self.output.write(to_disp)
        self.output.pull_output()


class ConsoleOutput:

    def __init__(self):
        self.PIPE_PATH = "/tmp/output_monitor"
        self.is_reading = False
        self.popen = None

    def write(self, to_output):
        # print("Before write", to_output)
        with open(self.PIPE_PATH, 'w') as pipe_w:
            pipe_w.write(to_output)

    def pull_output(self):
        # already done each 0.5 sec by watch command
        pass

    def start_reading(self):
        self.is_reading = True
        os.remove(self.PIPE_PATH)
        os.mkfifo(self.PIPE_PATH)
        self.popen = subprocess.Popen(['xterm', '-e', 'watch', '-n 0,5', 'cat %s' % self.PIPE_PATH])

    def stop_reading(self):
        self.is_reading = False

    def exit(self):
        self.stop_reading()
        if self.popen is not None:
            self.popen.terminate()


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
