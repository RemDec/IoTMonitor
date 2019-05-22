from modules.abcModule import *
from src.utils.misc_fcts import get_infoname_py
import threading
import subprocess


class ActiveModule(Module):

    def __init__(self, netmap):
        self.netmap = netmap
        self.curr_threads = []

    @abc.abstractmethod
    def get_default_timer(self):
        pass

    @abc.abstractmethod
    def get_script_thread(self, rel_to_vi=[]):
        pass

    def is_active(self):
        return True

    def register_thread(self, th):
        if th not in self.curr_threads:
            self.curr_threads.append(th)

    def purge_threadlist(self):
        self.curr_threads = [th for th in self.curr_threads if th.is_alive()]

    def terminate_threads(self, wait_for_purge=0):
        for thread in self.curr_threads:
            thread.interrupt()
        if wait_for_purge:
            from time import sleep
            sleep(wait_for_purge)
        self.purge_threadlist()

    def get_nbr_running(self):
        # count threads which underlying script subprocess not yet exited
        return len([th for th in self.curr_threads if not th.under_proc_state()[0]])

    def str_threads(self):
        s = f"[{self.get_module_id()}] List of active threads in this module instance\n"
        for i, thread in enumerate(self.curr_threads):
            state = "Alive" if thread.is_alive() else "Terminated"
            s += f">>>>>>> Thread {i} ({state}) <<<<<<<\n"
            s += str(thread) + "\n"
        if len(self.curr_threads) == 0:
            s += "   [ empty thread list ]\n"
        return s

    def str_summary(self):
        s = f"[{self.get_module_id()}] ~ Thlist[{self.get_nbr_running()}/{len(self.curr_threads)}]"
        return s

    def __str__(self):
        return self.str_threads()

    def treat_params(self, defaults, given_params):
        final_par = {}
        for par, val in defaults.items():
            if given_params.get(par):
                # Parameter is given as is
                final_par[par] = given_params[par]
            elif val[1]:
                # Ungiven parameter but mandatory -> take default
                final_par[par] = val[0]
        return final_par


class ScriptThread(threading.Thread):

    def __init__(self, callback_fct=None, rel_to_vi=[], max_exec_time=120):
        threading.Thread.__init__(self)
        self.callback_fct = callback_fct
        self.max_exec_time = max_exec_time
        self.cmd = []
        self.popen = None
        self.rel_to_vi = rel_to_vi

    def run(self):
        cmd_as_shell = isinstance(self.cmd, str)
        logging.getLogger("debug").feedback(f"Starting thread : {super().getName()}")
        logging.getLogger("debug").debug(f"Starting thread : {super().getName()}")
        self.popen = subprocess.Popen(self.cmd, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, universal_newlines=True,
                                      shell=cmd_as_shell)
        try:
            return_code = self.popen.wait(timeout=self.max_exec_time)
            if self.callback_fct is not None:
                self.callback_fct((return_code, self.popen), rel_to_vi=self.rel_to_vi)
        except subprocess.TimeoutExpired as timeout:
            if self.callback_fct is not None:
                self.callback_fct((timeout, self.popen), rel_to_vi=self.rel_to_vi)

    def start(self, cmd):
        self.cmd = cmd
        super().setName(f"Thread ({threading.currentThread().ident}) running {self.cmd_to_str()}")
        super().start()

    def interrupt(self):
        self.callback_fct = None
        if self.popen is not None and self.popen.poll() is None:
            self.popen.terminate()
            if self.popen.poll() is None:
                self.popen.kill()

    def under_proc_state(self):
        if self.popen is None:
            return False, -1
        ret = self.popen.poll()
        if ret is None:
            return False, self.popen.pid
        else:
            return True, ret

    def cmd_to_str(self):
        if isinstance(self.cmd, str):
            return self.cmd
        elif isinstance(self.cmd, list):
            return ' '.join(self.cmd)
        else:
            return str(self.cmd)

    def __str__(self):
        ended, code_or_pid = self.under_proc_state()
        fname, modname = get_infoname_py(self.callback_fct)
        s = f"Script thread (max duration:{self.max_exec_time}s) for cmd {self.cmd_to_str()}"
        if ended:
            s += f"\n  |_ script subprocess exited with return code {code_or_pid}"
        else:
            if code_or_pid > -1:
                state = f"still working with pid {code_or_pid}"
            else:
                state = f"launching, pid not yet allocated"
            s += f"\n  |_ script subprocess {state})"
        s += f"\n  |_ treat output with callback function {fname} of [{modname}]"
        return s
