from abcModule import *
from utils.timer import *
import threading, subprocess, pipes


class PassiveModule(Module):

    @abc.abstractmethod
    def get_bg_thread(self, output_stream):
        pass

    @abc.abstractmethod
    def get_comm_thread(self, timer, read_interv):
        pass

    def is_active(self):
        return False

    def treat_params(self, defaults, given_params):
        final_par = {}
        for par, val in defaults.items():
            if given_params.get(par):
                final_par[par] = given_params[par]
            elif val[1]:
                final_par[par] = val[0]
        return final_par
    
    
class BackgroundThread(threading.Thread):
    
    def __init__(self, output_stream=None):
        super().__init__()
        self.output_stream = output_stream
        self.pipe_w = None
        self.popen = None

    def run(self):
        print(super().getName())
        if self.output_stream is not None:
            self.popen = subprocess.Popen(self.cmd, stdout=self.output_stream, stderr=subprocess.STDOUT)
        else:
            self.popen = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.pipe_w = self.popen.stdout
        print(super().getName() + "\n  |> launched subprocess outputing in", self.pipe_w)

    def get_pipe_output(self):
        return self.pipe_w

    def start(self, cmd):
        self.cmd = cmd
        super().setName(f"Background thread ({threading.currentThread().ident}) running {' '.join(cmd)}")
        super().start()
        return self.pipe_w
        

class CommunicationThread(threading.Thread, TimerInterface):

    def __init__(self, read_fct=None, timer=None, read_timer=0):
        super().__init__()
        self.read_fct = read_fct
        self.timer = timer
        self.init_read_t = read_timer if read_timer > 0 else 20
        self.read_t = self.init_read_t
        self.pipe_r = None
        self.must_read = False

    def is_decrementable(self):
        return self.must_read

    def decr(self):
        if self.read_t > 0:
            self.read_t -= 1
        else:
            self.must_read = False
            self.read_pipe()
            # ended treatment, wait next trigger
            self.read_t = self.init_read_t
            self.must_read = True

    def read_pipe(self):
        # start program running in exec thread output treatment
        self.call_parsing_fct(self.pipe_r.read1())

    def call_parsing_fct(self, output):
        if self.read_fct is not None:
            self.read_fct(output)
        else:
            print(f"No read fct defined, redirect stdout {output}")

    def close_pipe(self):
        if self.pipe_r is not None:
            self.pipe_r.close()

    def run(self):
        print(super().getName())
        self.set_reading()

    def start(self, pipe_output):
        self.pipe_r = pipe_output
        super().setName(f"Communication thread ({threading.currentThread().ident}) with pipe {self.pipe_r} as given param (read every {self.read_t}s)")
        super().start()

    def set_reading(self, run=True, t=None):
        if t is not None:
            self.read_t = t
            self.init_read_t = t
        self.must_read = run
        if run:
            if self.timer is None:
                self.timer = TimerThread(autostart=True)
            self.timer.subscribe(self)
