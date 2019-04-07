from abcModule import *
import threading, subprocess


class ActiveModule(Module):

    def __init__(self):
        self.curr_threads = []

    @abc.abstractmethod
    def get_default_timer(self):
        pass

    @abc.abstractmethod
    def get_script_thread(self):
        pass

    def is_active(self):
        return True

    def register_thread(self, th):
        self.curr_threads.append(th)

    def purge_threads(self):
        self.curr_threads = [th for th in self.curr_threads if th.is_alive()]

    def terminate_threads(self, wait_for_purge=0):
        for thread in self.curr_threads:
            thread.interrupt()
        if wait_for_purge:
            from time import sleep
            sleep(wait_for_purge)
        self.purge_threads()

    def str_threads(self):
        s = ""
        for thread in self.curr_threads:
            state = "A" if thread.is_alive() else "N"
            s += "\n------" + state + "------\n" + str(thread)
        if s == "":
            s = "[[" + self.get_module_id() + "]empty thread list]"
        return s

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

    def __init__(self, callback_fct=None, max_exec_time=180):
        threading.Thread.__init__(self)
        self.callback_fct = callback_fct
        self.max_exec_time = max_exec_time
        self.cmd = []
        self.popen = None

    def run(self):
        print(super().getName())
        self.popen = subprocess.Popen(self.cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True)
        try:
            return_code = self.popen.wait(timeout=self.max_exec_time)
            if self.callback_fct is not None:
                self.callback_fct( (return_code, self.popen) )
        except subprocess.TimeoutExpired as timeout:
            if self.callback_fct is not None:
                self.callback_fct( (timeout, self.popen) )

    def start(self, cmd):
        self.cmd = cmd
        super().setName(f"Thread ({threading.currentThread().ident}) running {' '.join(cmd)}")
        super().start()

    def interrupt(self):
        if self.popen is not None and self.popen.poll() is None:
            self.popen.terminate()
            if self.popen.poll() is None:
                self.popen.kill()