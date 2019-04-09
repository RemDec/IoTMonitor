from abcActiveModule import *
import shlex


class AModArbitraryCmd(ActiveModule):

    def __init__(self, params=None, netmap=None, logger=None):
        super().__init__()
        self.m_id = "arbcmd"
        self.PARAMS = {"prog": ("echo", True, ""),
                       "args": ("No or bad command given to arbitrary module [arbcmd]", False, "")}
        self.netmap = netmap
        self.logger = logger

        self.set_params(params)

    def set_params(self, params):
        # fix missing execution params with defaults
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def parse_output(self, output):
        pass

    def distrib_output(self, script_output):
        # function called by ending exec thread
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout.read()
            # if code OK, should parse results to integrate in app (netmap, alert threats, ..)
            print(f"Module [{self.m_id}] arbitrary execution of {popen.args} returned (code {code}):\n{output}")
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            # pull info from exception
            py_except, popen = script_output
            print(f"Module [{self.m_id}] execution raised exception : {py_except}")

    def launch(self):
        # start a thread for cmd + params execution
        super().purge_threadlist()
        s_thread = self.get_script_thread()
        if self.params.get("args") is None:
            self.params["args"] = self.PARAMS["args"][0] if self.params["prog"] == "echo" else ""
        args_split = shlex.split(self.params["args"])
        s_thread.start([self.params["prog"]] + args_split)
        super().register_thread(s_thread)

    def stop(self):
        super().terminate_threads()

    def get_script_thread(self):
        # instancing generic thread defined in superclass for active modules
        return ScriptThread(callback_fct=self.distrib_output, max_exec_time=30)

    def get_default_timer(self):
        return 60

    def get_description(self):
        return f"[{self.m_id}] Blackbox module executing any command given"

    def get_module_id(self):
        return self.m_id


if __name__ == '__main__':
    arb = AModArbitraryCmd({"prog": "sleep", "args":"10"})
    arb2 = AModArbitraryCmd({"prog": "sleep", "args":"20"})
    print("Thread list before start :", arb.str_threads())
    arb.launch()
    arb2.launch()
    import time
    time.sleep(1)
    print("Thread list with one active : ", arb.str_threads())
    arb.stop()
    print("Thread list just after interrupt with one active : ", arb.str_threads())
    time.sleep(1)
    arb.terminate_threads()
    print("Thread list after clearing dead thread : ", arb.str_threads())