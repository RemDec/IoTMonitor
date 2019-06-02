from modules.abcPassiveModule import PassiveModule, BackgroundThread, CommunicationThread
from src.utils.misc_fcts import log_feedback_available, treat_params
from time import sleep
import abc


class FacilityActiveModule(PassiveModule):

    def __init__(self, read_interval=20, params=None, timer=None, netmap=None):
        super().__init__(timer, netmap)
        self.read_interval = read_interval
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
    def parse_output(self, output, rel_to_vi=[]):
        pass

    # ------------- Pre-implemented -------------
    # Already implemented methods, avoiding redundant writing. If you want to custom it just rewrite it in the subclass.

    #   Methods concerning execution of underlying program in a new thread, using facilities of parent class

    def work_before_launching(self, cmd_to_exec, bg_thread, comm_thread, rel_to_vi=[]):
        pass

    def launch(self, rel_to_vi=[]):
        super().purge_thlist()
        cmd_to_exec = self.build_final_cmd(rel_to_vi)
        bg_thread = self.new_bg_thread()
        comm_thread = self.new_comm_thread()
        self.work_before_launching(cmd_to_exec, bg_thread, comm_thread, rel_to_vi)
        bg_thread.start(cmd_to_exec)
        pipe = bg_thread.get_output_pipe()
        i = 0
        while pipe is None:
            if i == 10:
                log_feedback_available(f"[{self.get_module_id()}] Unable to get output pipe of {bg_thread}")
                return
            # Need to wait underlying process to instantiate its output stream
            sleep(0.3)
            i += 1
            pipe = bg_thread.get_output_pipe()
        comm_thread.start(pipe)
        super().register_threadpair((bg_thread, comm_thread))

    def treat_exception(self, exception, popen_object):
        log_feedback_available(f"Module [{self.get_module_id()}] execution raised exception :{exception}")

    def distrib_output(self, read_output, rel_to_vi=[]):
        self.parse_output(read_output, rel_to_vi)

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

    def new_bg_thread(self):
        return BackgroundThread()

    def new_comm_thread(self, rel_to_vi=[]):
        return CommunicationThread(self.distrib_output, rel_to_vi, self.timer, self.get_read_interval())

    def set_read_interval(self, duration):
        self.read_interval = duration

    def get_read_interval(self):
        return self.read_interval
