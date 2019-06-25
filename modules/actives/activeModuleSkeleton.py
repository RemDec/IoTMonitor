from modules.abcActiveModule import *
# import logging is done in superclass abcModule
from src.utils.misc_fcts import log_feedback_available


class AModNameMod(ActiveModule):
    """This class is a skeleton to copy/paste in order to implement a new Active Module with detailed operations.

    If you don't want implement it from scratch based on this skeleton, you can subclass abcFacilityActiveModule that
    already fully implements usage of facilities provided by ActiveModule (namely the management of underlying program
    in threads). It provides less fine-grained control but is easier than fill this skeleton. However, in this
    skeleton the facilities are used by default but you are free to implement your own, while all methods in this class
    do the right job assigned to by the interface (eg. get_module_id() should return an unique string among all existing
    modules, launch() should start an execution of the underlying program in a dissociated thread, etc.).

    """

    def __init__(self, params=None, netmap=None):
        super().__init__(netmap)
        self.m_id = "skel_active"
        self.CMD = ""
        self.PARAMS = {}
        # where PARAMS is the params scheme mapping param_code -> (defaultValue, isMandatory, prefix)
        self.desc_PARAMS = {}
        # where a textual description is provided mapping param_code -> string_description

        self.set_params(params)
        self.max_exec_time = 40
        # how long should be an execution of the cmd underlying program (max in secs) before interrupt

    def get_description(self):
        # a short description of module utility
        return f"[{self.m_id}] Skeleton for writing an active module"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id

    def get_cmd(self):
        # a string which it would be used to call the program in the system environment in CLI (likely callname in PATH)
        return self.CMD

    def get_params(self):
        # additional parameters given following the command
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        # fix missing execution params with defaults
        # self.params is the dict (param_code -> param_value) from which is built the final command to call the
        # underlying program in the system considering the parameters values to process
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def parse_output(self, output):
        # how script output should act on application (netmap filling, alert raising, logging,..)
        logging.getLogger("debug").debug("Data to treat ->", output.decode())

    def distrib_output(self, script_output, rel_to_vi=[]):
        # function called by ending exec thread with script_output as a tuple summarizing how it ended
        if isinstance(script_output[0], int):
            # popen is the subprocess overlayer object as manipulated by subprocess.py, from which access to output
            code, popen = script_output
            output = popen.stdout.read()
            # Logging through feedback system (capturing it to be displayed in app and really logged after)
            log_feedback_available(f"Module [{self.m_id}] execution returned (code {code})", logitin='info', lvl='info')
            # if code OK, should parse results to integrate in app (netmap, alert threats, ..)
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            # pull info from exception and log it
            py_except, popen = script_output
            log_feedback_available(f"Module [{self.m_id}] execution raised exception :{py_except}",
                                   logitin='error', lvl='error')

    def launch(self, rel_to_vi=[]):
        # Start a new thread as given by get_script_thread() and pass it the command, built from get_cmd() that
        # is the callname of the program (as you would call it on CLI) and current params (reformated as desired in
        # this function before). Final cmd can be a list or a string, see doc of run(.) in threading.py
        super().purge_threadlist()
        cmd = [self.CMD]
        for param, val in self.params.items():
            # getting potential prefix and appending cmd arg value (-flag val) from params scheme
            cmd.append(self.PARAMS[param][2] + val)

        # start a thread for cmd + params execution
        s_thread = self.get_script_thread()
        s_thread.start(cmd)
        super().register_thread(s_thread)

    def stop(self):
        # kill all threads (running cmd in a subprocess) instantiated from this instance
        super().terminate_threads()

    def get_script_thread(self, rel_to_vi=[]):
        # instantiating generic thread defined in superclass facilities for active modules that you can rewrite
        return ScriptThread(callback_fct=self.distrib_output, rel_to_vi=rel_to_vi,
                            max_exec_time=self.max_exec_time)

    def get_default_timer(self):
        # how frequent should be executed in automated queue of routine by default (sec)
        return 60
