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
        
    def run(self):
        print(super().getName())
        
    def start(self, cmd, pipe):
        self.cmd = cmd
        self.pipe = pipe
        super().setName(f"Passive module bg thread ({threading.currentThread().ident}) running {' '.join(cmd)} and writing {pipe}")
        super().start()
        

class CommunicationThread(threading.Thread):

    def __init__(self, read_timer=0):
        super().__init__()
        self.read_t = read_timer if read_timer>0 else 100
        self.fd_pos = 0
        self.output = None
        self.decrementable = False

    def run(self):
        print(super().getName())
        self.output = self.pipe.open('r')
        self.decrementable = True


    def decr(self):
        if self.read_t > 0:
            self.read_t -= 1
        else:
            self.decrementable = False
            self.fd_pos = self.output.seek(self.fd_pos)
            #read + parsing + log
            self.fd_pos = self.output.tell()

    def start(self, pipe):
        self.pipe = pipe
        super().setName(f"Communication thread ({threading.currentThread().ident}) with pipe {pipe}")
        super().start()
