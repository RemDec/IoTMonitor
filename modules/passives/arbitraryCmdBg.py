from modules.abcPassiveModule import *
import shlex


class PModArbitraryCmdBg(PassiveModule):

    def __init__(self, params=None, timer=None, netmap=None):
        super().__init__()
        self.m_id = "arbcmd_bg"
        self.PARAMS = {"prog": ("watch", True, ""),
                       "args": ("-t -n1 echo repeated_text_default_arbcmd_bg", False, "")}
        self.desc_PARAMS = {"prog": "A command to execute available on the system",
                            "args": "CLI arguments to pass as one string (all in it)"}
        self.read_interval = 60
        self.timer = timer
        self.netmap = netmap

        self.set_params(params)

    def get_cmd(self):
        return "arbitrary"

    def get_params(self):
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        # fix missing execution params with defaults
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def new_bg_thread(self, output_stream=None):
        # a bg_thread spawns the cmd in a new child process and controls it (output, killing, ..)
        return BackgroundThread(output_stream)

    def new_comm_thread(self, timer=None, read_interv=0):
        # a comm_thread reading in bg_thread cmd output and parsing it regularly (triggered by timer)
        return CommunicationThread(self.distrib_output, timer, read_interv)

    def set_read_interval(self, duration):
        self.read_interval = duration

    def get_read_interval(self):
        return self.read_interval

    def distrib_output(self, buffer_read):
        # do some work with output of bg process (parsing, filling netmap, ..)
        logging.getLogger("debug").debug(f"[{self.m_id}] Data to treat -> {buffer_read.decode()}")

    def launch(self, output_stream=None, read_interv=0):
        if self.params.get("args") is None:
            self.params["args"] = self.PARAMS["args"][0] if self.params["prog"] == "watch" else ""
        args_split = shlex.split(self.params["args"])
        cmd = [self.params["prog"]] + args_split

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
        return bg_thread, read_thread

    def stop(self):
        # ask registered threads to smoothly terminate their activity
        super().terminate_threads()

    def get_description(self):
        return f"[{self.m_id}] Blackbox module executing a given program with constant output in background"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id


if __name__ == '__main__':
    cmd = PModArbitraryCmdBg()
    bg_thread, comm_thread = cmd.launch(read_interv=2)
    import time
    time.sleep(5)
    print("######################\n", cmd)
    time.sleep(10)
    cmd.stop()
    print("######## STOP PROCESS #######\n", cmd)
    comm_thread.timer.stop()
