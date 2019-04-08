from abcPassiveModule import *


class PModNameMod(PassiveModule):

    def __init__(self, params=None, timer=None, netmap=None, logger=None):
        super().__init__()
        self.m_id = "default"
        self.CMD = ""
        self.PARAMS = {}
        # where one param <-> (defaultValue, isMandatory, prefix)
        self.timer = timer
        self.netmap = netmap
        self.logger = logger

        self.set_params(params)

    def set_params(self, params):
        # fix missing execution params with defaults
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def get_bg_thread(self, output_stream=None):
        return BackgroundThread(output_stream)

    def distrib_output(self, buffer_read):
        print(buffer_read)

    def get_comm_thread(self, timer=None, read_interv=0):
        return CommunicationThread(self.distrib_output, timer, read_interv)

    def launch(self, output_stream=None, read_interv=0):
        # spawn 2 threads: bg managing subprocess cmd and comm pulling and treating its output
        cmd = [self.CMD]
        for param, val in self.params.items():
            cmd.append(self.PARAMS[param][2] + val)
        bg_thread = self.get_bg_thread(output_stream)
        read_thread = self.get_comm_thread(self.timer, read_interv)

        bg_thread.start(cmd)
        pipe = bg_thread.get_output_pipe()
        # waiting bg thread to link an output stream file (pipe)
        while pipe is None:
            sleep(0.3)
            pipe = bg_thread.get_output_pipe()
        read_thread.start(pipe)
        super().register_thread(bg_thread)
        super().register_thread(read_thread)

    def stop(self):
        # ask registered threads to smoothly terminate their activity
        super().terminate_threads()

    def get_description(self):
        return f"[{self.m_id}] Skeleton for writing a passive module"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id
