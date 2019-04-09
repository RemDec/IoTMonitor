from abcPassiveModule import *


class PModNameMod(PassiveModule):

    def __init__(self, params=None, timer=None, netmap=None, logger=None):
        super().__init__()
        self.m_id = "default"
        self.CMD = ""
        self.PARAMS = {}
        # where one param <-> (defaultValue, isMandatory, prefix)
        self.read_interval = 60
        # time between each reading on the output of background subprocess running cmd

        self.timer = timer
        self.netmap = netmap
        self.logger = logger

        self.set_params(params)

    def set_params(self, params):
        # fix missing execution params with defaults
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def new_bg_thread(self, output_stream=None):
        # a bg_thread spawns the cmd in a new child process and controls it (output, killing, ..)
        return BackgroundThread(output_stream)

    def new_comm_thread(self, timer=None, read_interv=0):
        # a comm_thread reading in bg_thread cmd output and parsing it regularly (triggered by timer)
        if read_interv == 0:
            read_interv = self.read_interval
        return CommunicationThread(self.distrib_output, timer, read_interv)

    def set_read_interval(self, duration):
        self.read_interval = duration

    def get_read_interval(self):
        return self.read_interval

    def distrib_output(self, buffer_read):
        # do some work with output of bg process (parsing, filling netmap, ..)
        print("Data to treat ->", buffer_read.decode())

    def launch(self, output_stream=None, read_interv=0):
        # spawn 2 threads: bg managing subprocess cmd and comm pulling and treating its output
        cmd = [self.CMD]
        for param, val in self.params.items():
            cmd.append(self.PARAMS[param][2] + val)
        bg_thread = self.new_bg_thread(output_stream)
        read_thread = self.new_comm_thread(self.timer, read_interv)
        # launching bg thread that is running cmd and directing output to given output_stream or pipe
        bg_thread.start(cmd)
        pipe = bg_thread.get_output_pipe()
        # waiting bg thread to link an output stream file (pipe)
        while pipe is None:
            sleep(0.3)
            pipe = bg_thread.get_output_pipe()
        # spawn reading thread that subscribes to a timer to read output each read_interv time
        read_thread.start(pipe)
        # Register those 2 threads to this module instance threadlist
        super().register_threadpair((bg_thread, read_thread))

    def stop(self):
        # ask registered threads to smoothly terminate their activity
        super().terminate_threads()

    def get_description(self):
        return f"[{self.m_id}] Skeleton for writing a passive module"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id
