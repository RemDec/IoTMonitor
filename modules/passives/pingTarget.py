from abcPassiveModule import *
from time import sleep
import shlex


class PModPing(PassiveModule):

    def __init__(self, read_interval=10, params=None, timer=None, netmap=None, logger=None):
        super().__init__()
        self.m_id = "pingit"
        self.CMD = "ping"
        self.PARAMS = { "nbr": ("", False, "-c"),
                        "interv": ("", False, "-i"),
                        "divargs": ("", False, ""),
                        "IP": ("192.168.1.1", True, "")}
        # where one param <-> (defaultValue, isMandatory, prefix)
        self.read_interv = read_interval
        self.timer = timer
        self.netmap = netmap
        self.logger = logger

        self.set_params(params)

    def set_params(self, params):
        # fix missing execution params with defaults
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def get_bg_thread(self, output_stream=None):
        return BackgroundThread(output_stream)

    def get_comm_thread(self, timer=None, read_interv=0):
        if read_interv == 0:
            read_interv = self.read_interv
        return CommunicationThread(self.distrib_output, timer, read_interv)

    def distrib_output(self, buffer_read):
        print(f"DATA from bg thread output length {len(buffer_read.decode())}")
        print(f"CALLED FROM {threading.current_thread()}")

    def launch(self, output_stream=None, read_interv=0):
        cmd = [self.CMD]
        for param, val in self.params.items():
            if param != "divargs":
                cmd.append(self.PARAMS[param][2] + val)
        if "divargs" in self.params:
            cmd.append(shlex.split(self.params["divargs"]))
        bg_thread = self.get_bg_thread(output_stream)
        read_thread = self.get_comm_thread(self.timer, read_interv)
        bg_thread.start(cmd)
        pipe = bg_thread.get_output_pipe()
        while pipe is None:
            sleep(0.3)
            pipe = bg_thread.get_output_pipe()
        read_thread.start(pipe)
        super().register_thread(bg_thread)
        super().register_thread(read_thread)

    def stop(self):
        super().terminate_threads()

    def get_description(self):
        return f"[{self.m_id}] Module pinging constantly a given target"

    def get_module_id(self):
        # unique short string identifying this module
        return self.m_id


if __name__ == '__main__':
    ping = PModPing(read_interval=5)
    ping.launch()
    from time import sleep
    for i in range(10):
        sleep(1)
        print("\n##############################\n", ping)