from modules.abcActiveModule import *
from src.utils.misc_fcts import log_feedback_available
# permits CLI arguments smart parsing
import shlex


class AModArbitraryCmd(ActiveModule):
    """Active Module used to call any program accessible in the system, without any special output treatment

    It can be used to automatise diverse tasks by including it in the routine as any other module
    Written from skeleton.
    """

    def __init__(self, params=None, netmap=None):
        super().__init__(netmap)
        self.m_id = "arbcmd"
        self.PARAMS = {"prog": ("echo", True, ""),
                       "args": ("No or bad command given to arbitrary module [arbcmd]", False, "")}
        self.desc_PARAMS = {"prog": "A command to execute available on the system",
                            "args": "CLI arguments to pass as one string (all in it)"}

        self.set_params(params)

    def get_description(self):
        return f"[{self.m_id}] Blackbox module executing any command given as prog parameter"

    def get_module_id(self):
        return self.m_id

    def get_cmd(self):
        return "arbitrary"

    def get_params(self):
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def parse_output(self, output):
        pass

    def distrib_output(self, script_output, rel_to_vi=[]):
        # function called by ending exec thread with script_output as a tuple summarizing how it ended
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout.read()
            # if code OK, should parse results to integrate in app (netmap, alert threats, ..)
            log_feedback_available(f"Module [{self.m_id}] execution returned (code {code})", logitin='info', lvl='info')
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            # pull info from exception
            py_except, popen = script_output
            log_feedback_available(f"Module [{self.m_id}] execution raised exception :{py_except}",
                                   logitin='error', lvl='error')

    def launch(self, rel_to_vi=[]):
        super().purge_threadlist()
        s_thread = self.get_script_thread()
        if self.params.get("args") is None:
            self.params["args"] = self.PARAMS["args"][0] if self.params["prog"] == "echo" else ""
        args_split = shlex.split(self.params["args"])
        s_thread.start([self.params["prog"]] + args_split)
        super().register_thread(s_thread)

    def stop(self):
        super().terminate_threads()
        super().purge_threadlist()

    def get_script_thread(self, rel_to_vi=[]):
        return ScriptThread(callback_fct=self.distrib_output, rel_to_vi=rel_to_vi, max_exec_time=30)

    def get_default_timer(self):
        return 60


if __name__ == '__main__':
    arb = AModArbitraryCmd({"prog": "sleep", "args": "10"})
    arb2 = AModArbitraryCmd({"prog": "sleep", "args": "20"})
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
