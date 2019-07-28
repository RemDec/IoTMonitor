from modules.abcPassiveModule import *
from src.utils.misc_fcts import log_feedback_available, get_ip
from ipaddress import ip_address
import shlex
import re

desc_PARAMS = {"IP": "Target IP adress in ping command syntax (only one specifiable)",
               "interv": "Interval between each ping (seconds)",
               "divargs": "Other acceptable args for ping command"}

IPv4_addr = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'


class PModPing(PassiveModule):
    """Passive Module used to confirm that an equipment behind an IP address is still responding (ICMP echo requests).

    Written using skeleton.
    """

    def __init__(self, read_interval=10, params=None, timer=None, netmap=None):
        super().__init__(timer, netmap)
        self.m_id = "pingit"
        self.CMD = "ping"
        self.PARAMS = {"interv": ("5", True, "-i "),
                       "divargs": ("", False, ""),
                       "IP": (get_ip(), True, "")}
        self.desc_PARAMS = desc_PARAMS
        self.read_interval = read_interval
        self.params = params
        self.set_params(params)

    def get_description(self):
        return f"[{self.m_id}] Module pinging constantly a given target"

    def get_module_id(self):
        return self.m_id

    def get_cmd(self):
        return self.CMD

    def get_params(self):
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def new_bg_thread(self):
        return BackgroundThread()

    def new_comm_thread(self, timer=None, rel_to_vi=[]):
        timer = timer if timer is not None else self.timer
        return CommunicationThread(self.distrib_output, rel_to_vi, timer, self.get_read_interval())

    def set_read_interval(self, duration):
        self.read_interval = duration

    def get_read_interval(self):
        return self.read_interval

    def parse_host_state(self, most_recent):
        if most_recent is not None:
            foundip = re.findall(IPv4_addr, most_recent)
            ip = None
            state = None
            if len(foundip) > 0:
                try:
                    ip_address(foundip[0])
                except ValueError:
                    return None, None
                ip = foundip[0]
            if re.search(r'time=', most_recent):
                state = 'up'
            if re.search(r'[Uu]nreachable', most_recent):
                state = 'down'
            return ip, state
        return None, None

    def distrib_output(self, buffer_read, rel_to_vi=[]):
        str_out = buffer_read.decode()
        lines = str_out.strip().split('\n')
        most_recent = lines[-1] if len(lines) > 0 else None
        ip, state = self.parse_host_state(most_recent)
        if not(None in [self.netmap, ip, state]):
            mapid = self.netmap.get_similar_vi(ip=ip)
            if mapid is None:
                mapid, vi = self.netmap.create_vi(create_event=True, creator=self.m_id, ip=ip)
            else:
                vi = self.netmap.get_vi(mapid)
            old_state = vi.state
            if old_state == state:
                log_feedback_available(f"Module [{self.m_id}] didn't modify {ip} state ({state})")
                return
            vi.set_state(state)
            self.netmap.register_modif('VI ' + mapid, elmt_type='virt_inst', elmt_id=mapid, modificator=self.m_id,
                                       old_state=f"Network state: {old_state}", new_state=f"Network state: {vi.state}",
                                       logit_with_lvl=20)
            log_feedback_available(f"Module [{self.m_id}] determined new state for {ip} : {state}")

    def launch(self, rel_to_vi=[]):
        cmd = [self.CMD]
        for param, val in self.params.items():
            if param != "divargs":
                if param == 'IP':
                    target_ip = val
                    if len(rel_to_vi) > 0:
                        list_ips = self.netmap.get_IPs_from_mapids(rel_to_vi)
                        if len(list_ips) > 0 and list_ips[0] is not None:
                            target_ip = list_ips[0]
                    cmd.append(target_ip)  # Doesn't need prefix
                else:
                    cmd.append(self.PARAMS[param][2] + val)

        if self.params.get('divars', '') != '':
            cmd.append(shlex.split(self.params["divargs"]))
        bg_thread = self.new_bg_thread()
        read_thread = self.new_comm_thread(self.timer, rel_to_vi)
        bg_thread.start(cmd)
        pipe = bg_thread.wait_for_output_pipe()
        read_thread.start(pipe)
        super().register_threadpair((bg_thread, read_thread))

    def stop(self):
        super().terminate_threads()

    def install_info(self):
        return {'program': "ping", 'version': "s20121221",
                'install': {'apt': None,
                            'yum': None,
                            'snap': None
                            }
                }


if __name__ == '__main__':
    from src.net.netmap import Netmap
    netmap = Netmap()
    netmap.create_vi(mac='2D-8E-53-17-26-D9', ip='192.168.0.1', hostname='myfalseVI')
    ping = PModPing(read_interval=2, params={'IP': '192.168.0.1', 'interv': '3'}, timer=TimerThread(), netmap=netmap)
    ping.launch()
    ping.timer.launch()
    from time import sleep
    for i in range(6):
        sleep(2)
        print("\n##############################\n", ping)
    print("####### TERMINATING MODULE #######")
    ping.terminate_threads()
    print(ping)
    # Timer thread still alive independently (looping)
    ping.timer.stop()
