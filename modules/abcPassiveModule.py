from modules.abcModule import *
from src.utils.timer import *
from src.utils.misc_fcts import get_infoname_py, log_feedback_available
from src.utils.constants import MAX_INTERRUPT_TRIES, MAX_TIME_WAIT_PIPE
from time import sleep
import threading
import subprocess


class PassiveModule(Module):
    """Abstract class defining requirements for a module abstracting a program associated with passive archetype

    Some methods in parent class Module should also be implemented in concrete Module classes inheriting PassiveModule.
    This class is abstract but provides concrete facilities to manage execution scheme of program recognized as passive.
    Such facilities are related with threads management, because execution of the underlying Module program should be
    done in a new thread to dissociate from main execution flow. By inheriting this class you have access to, but you
    are free to use it or no (if you want to implement you own Module linked threads management).
    """

    def __init__(self, timer, netmap):
        super().__init__()
        self.timer = timer
        self.netmap = netmap
        # thlist of instancied pairs at launch call (bg_thread, comm_thread)
        self.pair_threads = []

    @abc.abstractmethod
    def new_bg_thread(self):
        pass

    @abc.abstractmethod
    def new_comm_thread(self, rel_to_vi=[]):
        pass

    @abc.abstractmethod
    def set_read_interval(self, duration):
        pass

    @abc.abstractmethod
    def get_read_interval(self):
        pass

    def is_active(self):
        return False

    def is_running(self):
        return self.nbr_alive_subproc() + self.nbr_reading_comm() > 0

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

    def terminate_threads(self, wait_interv=0.001):
        # order all threads to terminate (bgs first and comms after)
        self.interrupt_thlist()
        i = 0
        while i < MAX_INTERRUPT_TRIES:
            if self.purge_thlist():
                # all threads finished their tasks
                break
            # relaunch terminate signal on each pair thread
            self.interrupt_thlist()
            i += 1
            if wait_interv > 0:
                sleep(wait_interv)
        if i >= MAX_INTERRUPT_TRIES:
            log_feedback_available(f"Some module underlying process remains unterminable : {self}",
                                   logitin='error', lvl=40)
            return False
        return True

    def nbr_alive_subproc(self):
        return len([bg for bg in self.get_bg_threads() if not bg.under_proc_state()[0]])

    def nbr_reading_comm(self):
        return len([comm for comm in self.get_comm_threads() if not comm.must_read])

    def str_pair_threads(self, header=None):
        if header is None:
            s = f"[{self.get_module_id()}] Pair list of active threads in this module instance\n"
        else:
            s = header
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
        return f"[{self.get_module_id()}] BGth[{self.nbr_alive_subproc()}/{len(self.get_bg_threads())}]"

    def __str__(self):
        modifs, threats = super().get_nbr_events()
        s = f"[{self.get_module_id()}] Module instance that lead following events:\n" \
            f"    Threats {threats} /!\\  Modifications {modifs} -o-\n"
        s += self.str_pair_threads(header="    Thread lists associated with this instance :\n")
        return s


class BackgroundThread(threading.Thread):
    
    def __init__(self, output_stream=None):
        super().__init__()
        self.output_stream = output_stream
        self.pipe_w = None
        self.popen = None
        self.cmd = []

    def run(self):
        cmd_as_shell = isinstance(self.cmd, str)
        log_feedback_available(f"Starting {super().getName()}", logitin='info')
        self.popen = subprocess.Popen(self.cmd,
                                      stdout=subprocess.PIPE if self.output_stream is None else self.output_stream,
                                      stderr=subprocess.STDOUT,
                                      shell=cmd_as_shell)
        self.pipe_w = self.popen.stdout
        # waiting for popen cmd exit would be a waste of resources (since it should run continuously)

    def under_proc_state(self):
        if self.popen is None:
            return False, -1
        ret = self.popen.poll()
        if ret is None:
            return False, self.popen.pid
        else:
            return True, ret

    def wait_for_output_pipe(self, steps=4, time=MAX_TIME_WAIT_PIPE):
        time = min(time, 5)
        step_time = max(time / steps, 0.1)
        c = 0
        while self.get_output_pipe() is None:
            if c > time:
                log_feedback_available(f"Unable to get output pipe for {super().getName()}", logitin='error')
                return None
            sleep(step_time)
            c += step_time
        return self.get_output_pipe()

    def get_output_pipe(self):
        return self.pipe_w

    def start(self, cmd):
        self.cmd = cmd
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        super().setName(f"Background thread running {cmd_str}")
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
            cmd = ' '.join(self.cmd) if isinstance(self.cmd, list) else self.cmd
        ended, code_or_pid = self.under_proc_state()
        s = f"Background thread for cmd {cmd}"
        if ended:
            s += f" (bg proc exited with code {code_or_pid})"
        else:
            s += f" (bg proc still working/unlaunched, pid {code_or_pid})"
        s += f"\n  |_ writing output in {self.pipe_w}"
        return s


class CommunicationThread(threading.Thread, TimerInterface):

    def __init__(self, read_fct=None, rel_to_vi=[], timer=None, read_timer=0):
        super().__init__()
        self.read_fct = read_fct
        self.rel_to_vi = rel_to_vi
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
            try:
                self.decr_threads.remove(threading.current_thread())
            except ValueError:
                pass

    def call_parsing_fct(self, output):
        if self.read_fct is not None:
            self.read_fct(output, self.rel_to_vi)
        else:
            log_feedback_available(f"Read function is None for commthread {super().getName()}", logitin='error')

    def read_pipe(self):
        # start program running in exec thread output treatment
        # logging.getLogger('discover').info("call")
        self.call_parsing_fct(self.pipe_r.read1())

    def close_pipe(self):
        if self.pipe_r is not None:
            self.pipe_r.close()

    def run(self):
        log_feedback_available(f"Starting {super().getName()}", logitin='info')
        self.set_reading()

    def start(self, pipe_output):
        self.pipe_r = pipe_output
        super().setName(f"Communication thread reading every {self.read_t}sec in pipe {self.pipe_r}")
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
            logging.getLogger("debug").warning("Dumb thread alive after join() call in interrupt procedure")
        self.decr_threads = []

    def __str__(self):
        fname, modname = get_infoname_py(self.read_fct)
        s = f"Communication thread calling {fname} of [{modname}] (decrementable {self.must_read}, timer {self.timer}),\n" \
            f"  |_ currently {len(self.decr_threads)} dumb reading threads on output {self.pipe_r}"
        return s
