from modules.abcActiveModule import *
# import logging is done in superclass abcModule


class AModNameMod(ActiveModule):

    def __init__(self, params=None, netmap=None):
        super().__init__(netmap)
        self.m_id = "default"
        self.CMD = ""
        self.PARAMS = {}
        # where mapping param_name -> (defaultValue, isMandatory, prefix)
        self.desc_PARAMS = {}
        # where mapping param_name -> string_description
        self.set_params(params)

        self.max_exec_time = 60
        # how long should be an execution of the cmd underlying program (max in secs)

    def get_cmd(self):
        # module underlying program as it would be called in CLI (string used as command)
        return self.CMD

    def get_params(self):
        # additional parameters given following the command
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        # fix missing execution params with defaults
        # self.params is dict (paramName:paramValue)
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def parse_output(self, txt_output):
        # how script output should act on application (netmap filling, alert raising, logging,..)
        pass

    def distrib_output(self, script_output):
        # function called by ending exec thread with script_output as a tuple summarizing how it ended
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout.read()
            # if code OK, should parse results to integrate in app (netmap, alert threats, ..)
            logging.getLogger("debug").debug(f"Module [{self.m_id}] execution returned (code {code}):\n{output}")
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            # pull info from exception
            py_except, popen = script_output
            logging.getLogger("debug").debug(f"Module [{self.m_id}] execution raised exception :{py_except}")

    def launch(self):
        super().purge_threadlist()
        cmd = [self.CMD]
        for param, val in self.params.items():
            # getting potential prefix and appending cmd arg value (-flag val)
            cmd.append(self.PARAMS[param][2] + val)

        # start a thread for cmd + params execution
        s_thread = self.get_script_thread()
        s_thread.start(cmd)
        super().register_thread(s_thread)

    def stop(self):
        # kill all threads (running cmd in a subprocess) instantiated from this instance
        super().terminate_threads()

    def get_script_thread(self):
        # instancing generic thread defined in superclass for active modules
        return ScriptThread(callback_fct=self.distrib_output, max_exec_time=self.max_exec_time)

    def get_default_timer(self):
        # how frequent should be executed in automated queue of routine
        return 60

    def get_description(self):
        return f"[{self.m_id}] Skeleton for writing an active module"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id
