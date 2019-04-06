from abcModule import *
import threading, subprocess

class ActiveModule(Module):

    @abc.abstractmethod
    def get_default_timer(self, t):
        pass

    @abc.abstractmethod
    def get_script_thread(self):
        pass

    def is_active(self):
        return True

    def treat_params(self, defaults, given_params):
        final_par = {}
        for par, val in defaults.items():
            if given_params.get(par):
                final_par[par] = given_params[par]
            elif val[1]:
                final_par[par] = val[0]
        return final_par


class ScriptThread(threading.Thread):

    def __init__(self, callback_fct=None):
        threading.Thread.__init__(self)
        self.callback_fct = callback_fct

    def run(self):
        print(super().getName())
        end_proc = subprocess.run(self.cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True)
        if self.callback_fct is not None:
            self.callback_fct(end_proc)

    def start(self, cmd):
        self.cmd = cmd
        super().setName(f"Thread ({threading.currentThread().ident}) running {' '.join(cmd)}")
        super().start()
