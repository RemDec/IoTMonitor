from modules.abcModule import *
from src.utils.timer import *
from src.utils.misc_fcts import get_infoname_py
from time import sleep
import threading
import subprocess


class PassiveModule(Module):

    def __init__(self, timer, netmap):
        self.timer = timer
        self.netmap = netmap
        # thlist of instancied pairs at launch call (bg_thread, comm_thread)
        self.pair_threads = []
        self.max_shutdown_time = 5

    @abc.abstractmethod
    def new_bg_thread(self, output_stream):
        pass

    @abc.abstractmethod
    def new_comm_thread(self, timer, read_interv):
        pass

    @abc.abstractmethod
    def set_read_interval(self, duration):
        pass

    @abc.abstractmethod
    def get_read_interval(self):
        pass

    def is_active(self):
        return False

    def get_bg_threads(self):
        return [th_pair[0] for th_pair in self.pair_threads]

    def get_comm_threads(self):
        return [th_pair[1] for th_pair in self.pair_threads]

    def register_threadpair(self, th_pair):
        bg, comm = th_pair
        if bg not in self.get_bg_threads() and comm not in self.get_comm_threads():
            self.pair_threads.append((bg, comm))

    def purge_thlist(self):
        alive_list = []
        for bg, comm in self.pair_threads:
            bg_proc_status = bg.under_proc_state()
            if bg_proc_status[0]:
                # bg process finished (returned an exit code)
                if comm.is_alive() or comm.is_dumbparsing():
                    # main reading thread didn't exit yet or dumb thread doing output parsing task
                    alive_list.append((bg, comm))
            else:
                # bg process underlying bg thread still running
                alive_list.append((bg, comm))
        self.pair_threads = alive_list
        return len(self.pair_threads) == 0

    def interrupt_thlist(self):
        # interrupt firstly threads at writing side (killing bg processes)
        for thread in self.get_bg_threads():
            thread.interrupt()
        # interrupt after reading threads
        for thread in self.get_comm_threads():
            thread.interrupt()

    def terminate_threads(self, wait_interv=0):
        # order all threads to terminate (bgs first and comms after)
        self.interrupt_thlist()
        i = 0
        while i < self.max_shutdown_time:
            if self.purge_thlist():
                # all threads finished their tasks
                break
            # relaunch terminate signal on each pair thread
            self.interrupt_thlist()
            i += 1
            if wait_interv:
                sleep(wait_interv)
        if i > self.max_shutdown_time:
            print("Some module remains unterminable :", self)
            return False
        return True

    def nbr_alive_subproc(self):
        return len([bg for bg in self.get_bg_threads() if not bg.under_proc_state()[0]])

    def nbr_reading_comm(self):
        return len([comm for comm in self.get_comm_threads() if not comm.must_read])

    def str_pair_threads(self):
        s = f"[{self.get_module_id()}] Pair list of active threads in this module instance\n"
        for i, (bg, comm) in enumerate(self.pair_threads):
            s += f">>>>>>> Threadpair {i} <<<<<<<\n"
            s += f"----- Background ({bg.is_alive()}) -----\n"
            s += str(bg) + "\n"
            s += f"----- Communicator ({comm.is_alive()}) -----\n"
            s += str(comm) + "\n"
        if len(self.pair_threads) == 0:
            s += f"   [ empty thread tuples list (bg, comm) ]\n"
        return s

    def str_summary(self):
        s = f"[{self.get_module_id()}] ~ BG[{self.nbr_alive_subproc()}/{len(self.get_bg_threads())}]" \
            f" COMM[{self.nbr_reading_comm()}/{len(self.get_comm_threads())}]"
        return s

    def __str__(self):
        return self.str_pair_threads()

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
        logging.getLogger("debug").debug(f"Starting thread : {super().getName()}")
        if self.output_stream is not None:
            self.popen = subprocess.Popen(self.cmd, stdout=self.output_stream, stderr=subprocess.STDOUT)
        else:
            self.popen = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.pipe_w = self.popen.stdout
        logging.getLogger("debug").debug(f"{super().getName()}\n  |> launched subprocess outputing in {self.pipe_w}")
        # waiting for popen cmd exit would be a waste of resources (since it should run continuously)

    def under_proc_state(self):
        if self.popen is None:
            return False, -1
        ret = self.popen.poll()
        if ret is None:
            return False, self.popen.pid
        else:
            return True, ret

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

    def __str__(self):
        if self.cmd is None:
            cmd = "unknown (must be passed with start())"
        else:
            cmd = ' '.join(self.cmd)
        ended, code_or_pid = self.under_proc_state()
        s = f"Background thread for cmd {cmd}"
        if ended:
            s += f" (bg proc exited with code {code_or_pid})"
        else:
            s += f" (bg proc still working/unlaunched, pid {code_or_pid})"
        s += f"\n  |_ writing output in {self.pipe_w}"
        return s


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

    def is_dumbparsing(self):
        return len(self.decr_threads) > 0

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
        if not new_dumb_thread:
            # we are at the end of dumb decr() thread
            self.decr_threads.remove(threading.current_thread())

    def call_parsing_fct(self, output):
        if self.read_fct is not None:
            self.read_fct(output)
        else:
            print(f"No read fct defined, redirect stdout {output}")

    def read_pipe(self):
        # start program running in exec thread output treatment
        self.call_parsing_fct(self.pipe_r.read1())

    def close_pipe(self):
        if self.pipe_r is not None:
            self.pipe_r.close()

    def run(self):
        logging.getLogger("debug").debug(f"Starting thread :{super().getName()}")
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
                logging.getLogger("debug").warning(f"No timer provided to comm thread {self}")
                self.timer = TimerThread(autostart=True, name="InstantiatedTimer")
            self.timer.subscribe(self)

    def interrupt(self):
        self.set_reading(run=False)
        self.timer.unsub(self)
        remaining = False
        for thread in self.decr_threads:
            if thread.is_alive():
                thread.join(1)
                if thread.is_alive():
                    remaining = True
        if remaining:
            print("Warning dumb thread alive after interrupt->join", self.decr_threads)
        self.decr_threads = []

    def __str__(self):
        fname, modname = get_infoname_py(self.read_fct)
        s = f"Communication thread calling {fname} of [{modname}] (decrementable {self.must_read}, timer {self.timer}),\n" \
            f"  |_ currently {len(self.decr_threads)} dumb reading threads on output {self.pipe_r}"
        return s
