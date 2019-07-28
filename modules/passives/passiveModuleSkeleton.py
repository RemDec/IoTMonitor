from modules.abcPassiveModule import *


class PModNameMod(PassiveModule):
    """This class is a skeleton to copy/paste in order to implement a new Passive Module with detailed operations.

    If you don't want implement it from scratch based on this skeleton, you can subclass abcFacilityPassiveModule that
    already fully implements usage of facilities provided by ActiveModule (namely the management of underlying program
    in threads). It provides less fine-grained control but is easier than fill this skeleton. However, in this
    skeleton the facilities are used by default but you are free to implement your own, while all methods in this class
    do the right job assigned to by the interface (eg. get_module_id() should return an unique string among all existing
    modules, launch() should start an execution of the underlying program in a dissociated thread, etc.).

    """

    def __init__(self, params=None, timer=None, netmap=None):
        super().__init__(timer, netmap)
        self.m_id = "skel_passive"
        self.CMD = ""
        self.PARAMS = {}
        # where PARAMS is the params scheme mapping param_code -> (defaultValue, isMandatory, prefix)
        self.desc_PARAMS = {}
        # where a textual description is provided mapping param_code -> string_description
        self.read_interval = 60
        # time between each reading on the output of background subprocess running cmd

        self.set_params(params)

    def get_description(self):
        return f"[{self.m_id}] Skeleton for writing a passive module"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id

    def get_cmd(self):
        # a string which it would be used to call the program in the system environment in CLI (likely callname in PATH)
        return self.CMD

    def get_params(self):
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        # fix missing execution params with defaults
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def new_bg_thread(self):
        # a bg_thread spawns the underlying program in a new child process and controls it (output, killing, ..)
        return BackgroundThread()

    def new_comm_thread(self, timer=None, read_interv=0, rel_to_vi=[]):
        # a comm_thread reads bg_thread underlying program output and parses it regularly (triggered by timer)
        if read_interv == 0:
            read_interv = self.get_read_interval()
        timer = timer if timer is not None else self.timer
        return CommunicationThread(self.distrib_output, rel_to_vi, timer, read_interv)

    def set_read_interval(self, duration):
        self.read_interval = duration

    def get_read_interval(self):
        return self.read_interval

    def distrib_output(self, buffer_read, rel_to_vi=[]):
        # do some work with output of bg process (parsing, filling netmap, ..)
        logging.getLogger("debug").debug("Data to treat ->", buffer_read.decode())

    def launch(self, rel_to_vi=[], read_interv=0):
        # spawns 2 threads: bg managing subprocess running underlying program and comm pulling and treating its output
        cmd = [self.CMD]
        # building final command from current parameters and the defined scheme
        for param, val in self.params.items():
            cmd.append(self.PARAMS[param][2] + val)
        bg_thread = self.new_bg_thread()
        read_thread = self.new_comm_thread(self.timer, read_interv, rel_to_vi)
        # launching bg thread that is running cmd and capturing its output stream to pass it to comm thread reading in
        bg_thread.start(cmd)
        # waiting bg thread to link an output stream file (pipe)
        pipe = bg_thread.wait_for_output_pipe()
        # spawn reading thread that automatically subscribes to a timer to read output each read_interv time
        read_thread.start(pipe)
        # Register those 2 threads to this module instance threadlist (facility)
        super().register_threadpair((bg_thread, read_thread))

    def stop(self):
        # ask registered threads to smoothly terminate their activity
        super().terminate_threads()

    def install_info(self):
        # help for underlying program installation in the system. May be empty or with None values, see doc abcModule
        return {'program': None, 'version': None,
                'install': {'apt': None,
                            'yum': None,
                            'snap': None
                            }
                }
