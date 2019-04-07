from abcModule import *
import threading, subprocess, pipes


class PassiveModule(Module):

    @abc.abstractmethod
    def get_bg_thread(self):
        pass

    @abc.abstractmethod
    def get_comm_thread(self):
        pass

    @abc.abstractmethod
    def get_pipe(self):
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
    
    def __init__(self):
        super().__init__()
        self.pipe = None
        self.pipe_w = None

    def run(self):
        print(super().getName())
        pipe_w = pipes.Template().open(self.pipe, 'w')
        self.popen = subprocess.Popen(self.cmd, stdout=pipe_w)
        print("Passive bg end")

    def start(self, cmd, pipe):
        self.cmd = cmd
        self.pipe = pipe
        super().setName(f"Passive module bg thread ({threading.currentThread().ident}) running {' '.join(cmd)} and writing {pipe}")
        super().start()
        

class CommunicationThread(threading.Thread):

    def __init__(self, read_fct=None, read_timer=0):
        super().__init__()
        self.read_fct = read_fct
        self.init_read_t = read_timer if read_timer>0 else 100
        self.read_t = self.init_read_t
        self.fd_pos = 0
        self.output = None
        self.pipe = None
        self.pipe_r = None
        self.decrementable = False

    def decr(self):
        if self.read_t > 0:
            self.read_t -= 1
        else:
            # start program output treatment
            try:
                self.decrementable = False
                if self.pipe_r is None:
                    self.pipe_r = pipes.Template.open(self.pipe, 'r')
                self.fd_pos = self.output.seek(self.fd_pos)
                # read + parsing + log
                if self.output is not None:
                    current_output = self.output.read()
                    if self.read_fct is not None:
                        self.read_fct(current_output)
                    else:
                        print(f"No read fct defined, redirect stdout {current_output}")
                self.fd_pos = self.output.tell()
                # ended treatment, wait next trigger
                self.read_t = self.init_read_t
                self.decrementable = True
            except FileNotFoundError as e:
                print(e)

    def close_pipe(self):
        if self.pipe_r is not None:
            self.pipe_r.close()

    def run(self):
        print(super().getName())
        self.output = self.pipe.open('r')
        self.decrementable = True

    def start(self, pipe):
        self.pipe = pipe
        super().setName(f"Communication thread ({threading.currentThread().ident}) with pipe {pipe}")
        super().start()
