from abcModule import *
from utils.timer import *
from time import sleep
import threading, subprocess


class PassiveModule(Module):

    def __init__(self):
        self.bg_threads = []
        self.comm_threads = []
        self.max_shutdown_time = 5

    @abc.abstractmethod
    def get_bg_thread(self, output_stream):
        pass

    @abc.abstractmethod
    def get_comm_thread(self, timer, read_interv):
        pass

    def is_active(self):
        return False

    def get_list_relative(self, th):
        if isinstance(th, BackgroundThread):
            return self.bg_threads
        if isinstance(th, CommunicationThread):
            return self.comm_threads

    def register_thread(self, th):
        th_list = self.get_list_relative(th)
        if not th in th_list:
            th_list.append(th)

    def purge_thlists(self):
        self.bg_threads = [th for th in self.bg_threads if th.is_alive()]
        self.comm_threads = [th for th in self.comm_threads if th.is_alive()]

    def purge_bglist(self):
        self.bg_threads = [th for th in self.bg_threads if th.is_alive()]

    def purge_commlist(self):
        self.comm_threads = [th for th in self.comm_threads if th.is_alive()]

    def interrupt_thlist(self, thlist):
        for thread in thlist:
            thread.interrupt()
        
    def terminate_threads(self):
        # close first reading side
        self.interrupt_thlist(self.bg_threads)
        i = 0
        while i < self.max_shutdown_time:
            self.purge_bglist()
            if len(self.bg_threads) == 0:
                self.interrupt_thlist(self.comm_threads)
                break
            i+=1
        if i > self.max_shutdown_time:
            print("Some module remains unterminable :", self)
        else:
            self.purge_commlist()

    def str_threads(self, thlist):
        s = ""
        for thread in thlist:
            state = "A" if thread.is_alive() else "N"
            s += "------" + state + "------\n" + str(thread)
        if s == "":
            s = "[[" + self.get_module_id() + "]empty thread list]"
        return s

    def __str__(self):
        s = f"Threads lists of passive module [{self.get_module_id()}] :\n"
        s += f"    |\n"
        s += f"    | Background threads list (length {len(self.bg_threads)})\n"
        s += self.str_threads(self.bg_threads) + "\n"
        s += f"    |\n"
        s += f"    | Communicator threads list (length {len(self.comm_threads)})\n"
        s += self.str_threads(self.comm_threads)
        return s

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

    def get_output_pipe(self):
        return self.pipe_w

    def start(self, cmd):
        self.cmd = cmd
        super().setName(f"Background thread ({threading.currentThread().ident}) running {' '.join(cmd)}")
        super().start()
        return self.pipe_w

    def interrupt(self):
        if self.popen is not None and self.popen.poll() is None:
            self.popen.terminate()
            if self.popen.poll() is None:
                self.popen.kill()


class CommunicationThread(threading.Thread, TimerInterface):

    def __init__(self, read_fct=None, timer=None, read_timer=0):
        super().__init__()
        self.read_fct = read_fct
        self.timer = timer
        self.init_read_t = read_timer if read_timer > 0 else 20
        self.read_t = self.init_read_t
        self.pipe_r = None
        self.must_read = False
        self.decr_threads = []

    def get_dumb_name(self):
        return f"DumbThread [{len(self.decr_threads)}]"

    def is_decrementable(self):
        return self.must_read

    def decr(self, new_dumb_thread=True):
        if self.read_t > 0:
            self.read_t -= 1
        else:
            if new_dumb_thread:
                # should restart this reading + parsing work in a new dump thread running decr()
                dumb_thread = threading.Thread(target=self.decr,
                                               name=self.get_dumb_name(),
                                               kwargs={'new_dumb_thread': False})
                self.decr_threads.append(dumb_thread)
                dumb_thread.start()
                return
            self.must_read = False
            self.read_pipe()
            # ended treatment, wait next trigger
            self.read_t = self.init_read_t
            self.must_read = True
        if not(new_dumb_thread):
            # we are at the end of dumb decr() thread
            self.decr_threads.remove(threading.current_thread())

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

    def interrupt(self):
        self.set_reading(run=False)
        self.timer.unsub(self)
        remaining = False
        for thread in self.decr_threads:
            thread.join(1)
            if thread.is_alive():
                remaining = True
        if remaining:
            print("Warning dumb thread alive after interrupt->join", self.decr_threads)
        self.decr_threads = []
