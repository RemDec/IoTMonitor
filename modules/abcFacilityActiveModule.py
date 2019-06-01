from modules.abcActiveModule import ActiveModule, ScriptThread
from src.utils.misc_fcts import log_feedback_available, treat_params
import abc


class FacilityActiveModule(ActiveModule):

    def __init__(self, params=None, netmap=None):
        super().__init__(netmap)
        self.params = params
        # care to have defined self.scheme in subclass before calling super().__init__(.) because this constructor calls
        # set_params which needs self.get_scheme_params() to be called (or define scheme as a returned constant in it)
        self.set_params(params)

    # ------------- To implement -------------

    @abc.abstractmethod
    def get_module_id(self):
        pass

    @abc.abstractmethod
    def get_cmd(self):
        pass

    @abc.abstractmethod
    def get_description(self):
        pass

    @abc.abstractmethod
    def get_scheme_params(self):
        pass

    @abc.abstractmethod
    def get_desc_params(self):
        pass

    @abc.abstractmethod
    def build_final_cmd(self, rel_to_vi=[]):
        pass

    @abc.abstractmethod
    def parse_output(self, output_stream, rel_to_vi=[]):
        pass

    # ------------- Pre-implemented -------------
    # Already implemented methods, avoiding redundant writing. If you want to custom it just rewrite it in the subclass.

    #   Methods concerning execution of underlying program in a new thread, using facilities of parent class

    def work_before_launching(self, cmd_to_exec, exec_script_thread, rel_to_vi=[]):
        pass

    def launch(self, rel_to_vi=[]):
        super().purge_threadlist()
        cmd_to_exec = self.build_final_cmd(rel_to_vi)
        exec_script_thread = self.get_script_thread(rel_to_vi)
        self.work_before_launching(cmd_to_exec, exec_script_thread, rel_to_vi)
        exec_script_thread.start(cmd_to_exec)
        super().register_thread(exec_script_thread)

    def treat_exception(self, exception, popen_object):
        log_feedback_available(f"Module [{self.get_module_id()}] execution raised exception :{exception}")

    def distrib_output(self, script_output, rel_to_vi=[]):
        if isinstance(script_output[0], int):
            code, popen = script_output
            log_feedback_available(f"Module [{self.get_module_id()}] execution returned (code {code})")
            self.parse_output(popen.stdout, rel_to_vi)
        elif isinstance(script_output[0], Exception):
            self.treat_exception(script_output[0], script_output[1])

    def stop(self):
        super().terminate_threads()

    #   Accessors for module configurations and scheme definition for underlying program parameters

    def get_curr_params(self):
        return self.params

    def get_params(self):
        return self.get_curr_params(), self.get_scheme_params(), self.get_desc_params()

    def set_params(self, given_params):
        scheme = self.get_scheme_params()
        self.params = treat_params(scheme, {} if given_params is None else given_params)

    def get_default_timer(self):
        return 60

    def get_max_exec_time(self):
        return 120

    def get_script_thread(self, rel_to_vi=[]):
        return ScriptThread(callback_fct=self.distrib_output, rel_to_vi=rel_to_vi,
                            max_exec_time=self.get_max_exec_time())
