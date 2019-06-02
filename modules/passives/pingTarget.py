from modules.abcPassiveModule import *
from src.utils.misc_fcts import log_feedback_available, treat_params, get_ip
import shlex

desc_PARAMS = {"IP": "Target IP adress(es) in ping command syntax",
               "interv": "Interval between each ping",
               "nbr": "Integer if should ping limited times",
               "divargs": "Other acceptable args for ping command"}


class PModPing(PassiveModule):
    """Passive Module used to confirm that an equipment behind an IP address is still responding (ICMP echo requests)

    """
    def __init__(self, read_interval=10, params=None, timer=None, netmap=None):
        super().__init__(timer, netmap)
        self.m_id = "pingit"
        self.CMD = "ping"
        self.PARAMS = {"nbr": ("", False, "-c"),
                       "interv": ("5", False, "-i"),
                       "divargs": ("", False, ""),
                       "IP": (get_ip(), True, "")}
        self.desc_PARAMS = desc_PARAMS
        self.read_interval = read_interval
        self.params = params
        self.set_params(params)

    def get_cmd(self):
        return self.CMD

    def get_params(self):
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        # fix missing execution params with defaults
        self.params = treat_params(self.PARAMS, {} if params is None else params)

    def new_bg_thread(self):
        return BackgroundThread()

    def new_comm_thread(self, timer=None, rel_to_vi=[]):
        timer = timer if timer is not None else self.timer
        return CommunicationThread(self.distrib_output, rel_to_vi, timer, self.get_read_interval())

    def set_read_interval(self, duration):
        self.read_interval = duration

    def get_read_interval(self):
        return self.read_interval

    def distrib_output(self, buffer_read, rel_to_vi=[]):
        log_feedback_available(f"[{self.m_id}] DATA from bg thread output of length {len(buffer_read.decode())}")

    def launch(self, rel_to_vi=[]):
        cmd = [self.CMD]
        for param, val in self.params.items():
            if param != "divargs":
                cmd.append(self.PARAMS[param][2] + val)
        if "divargs" in self.params:
            cmd.append(shlex.split(self.params["divargs"]))
        bg_thread = self.new_bg_thread()
        read_thread = self.new_comm_thread(self.timer, rel_to_vi)
        bg_thread.start(cmd)
        pipe = bg_thread.get_output_pipe()
        while pipe is None:
            sleep(0.3)
            pipe = bg_thread.get_output_pipe()
        read_thread.start(pipe)
        super().register_threadpair((bg_thread, read_thread))

    def stop(self):
        super().terminate_threads()

    def get_description(self):
        return f"[{self.m_id}] Module pinging constantly a given target"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id


if __name__ == '__main__':
    ping = PModPing(read_interval=2, timer=TimerThread())
    ping.launch()
    ping.timer.launch()
    from time import sleep
    for i in range(6):
        sleep(1)
        print("\n##############################\n", ping)
    print("####### TERMINATING MODULE #######")
    ping.terminate_threads()
    print(ping)
    # Timer thread still alive independently (looping)
    ping.timer.stop()
