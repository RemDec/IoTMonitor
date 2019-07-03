from modules.abcFacilityPassiveModule import FacilityActiveModule
from src.parsers.ipOutputParser import IpParser, is_ipv4
from src.utils.misc_fcts import get_ip, log_feedback_available
import re


class PModFping(FacilityActiveModule):

    def __init__(self, params=None, timer=None, netmap=None):
        super().__init__(read_interval=35, params=params, timer=timer, netmap=netmap)

    def get_module_id(self):
        return "fping"

    def get_description(self):
        return f"[{self.get_module_id()}] Module looping pinging multiple hosts in the network, " \
               f"determining their state/reachability"

    def get_cmd(self):
        return f"fping -l -A -d"

    def get_scheme_params(self):
        return {'period': ('30000', True, '-p '),
                'interval': ('10', True, '-i '),
                'retry': ('1', True, '-r '),
                'netIP': (get_ip(mask='24'), True, '-g '),
                'indivIP': (get_ip(), False, '')}

    def get_desc_params(self):
        return {'period': 'time (ms) between reping each individual host',
                'interval': 'time (ms) between different host pings',
                'retry': 'number of retries for each host',
                'netIP': 'entire network in which all hosts will be pinged',
                'indivIP': 'specific IP(s) to target given one per one (overwrite netIP ones)'}

    def build_final_cmd(self, rel_to_vi=[]):
        scheme = self.get_scheme_params()
        ip_str = ''
        if self.params.get('indivIP') is not None:
            ip_str += self.params.get('indivIP')
        if rel_to_vi is not None and self.netmap is not None:
            ip_str += ' '.join(self.netmap.get_IPs_from_mapids(rel_to_vi))
        if len(ip_str) == 0:
            # No specific IP given, use whole subnetwork
            ip_str += scheme.get('netIP')[2] + self.params.get('netIP')
        cmd = self.get_cmd()
        for param in self.params:
            if not(param in ['indivIP', 'netIP']):
                cmd += ' ' + scheme.get(param)[2] + self.params[param]
        return cmd + ' ' + ip_str

    def parse_output(self, output, rel_to_vi=[]):
        if self.netmap is None:
            return
        str_out = output.decode()
        lines = str_out.strip().split('\n')
        if len(lines) > 1:  # first and last lines may be incomplete and so not well formatted
            lines.pop(0)
            lines.pop()
        modified = []
        for line in lines:
            parsed = self.parse_host(line)
            if parsed is not None:
                ip, hostname, state = parsed
                mapid = self.netmap.get_similar_VI(ip=ip)
                if mapid is None:
                    if state == 'up':
                        mapid, vi = self.netmap.create_VI(create_event=True, creator=self.get_module_id(),
                                                          ip=ip, hostname=hostname)
                        vi.set_state(state)
                        modified.append(mapid)
                else:
                    vi = self.netmap.get_VI(mapid)
                    old_state = vi.state
                    vi.set_state(state)
                    changed = vi.complete_fields(ip=ip, hostname=hostname)
                    if old_state != state or changed:
                        self.netmap.register_modif(f"VI {mapid}", obj_type='virt_inst', obj_id=mapid,
                                                   modificator=self.get_module_id(),
                                                   old_state=f"Network state:{old_state}\n{vi.detail_str(level=1)}",
                                                   new_state=f"Network state:{state}\n{vi.detail_str(level=1)}",
                                                   logit_with_lvl=20)
                        modified.append(mapid)
        nbr_modifs = len(set(modified))
        if nbr_modifs > 0:
            log_feedback_available(f"Module [{self.get_module_id()}] updated state and/or fields of {nbr_modifs} VIs")

    def parse_host(self, host_line):
        # Line for a reached host : 'mymodem (192.168.1.1)        : [0], 84 bytes, 5.14 ms (5.14 avg, 0% loss)'
        # or '192.168.1.6 (192.168.1.6)     : [1], 84 bytes, 293 ms (253 avg, 0% loss)'
        # For an unreachable : 'ICMP Host Unreachable from 192.168.1.50 for ICMP Echo sent to 192.168.1.3 (192.168.1.3)'
        if re.search(r'Unreachable', host_line, re.IGNORECASE):
            ips = IpParser(host_line).find_IPs(duplicates=False)
            if len(ips) == 0:
                return None
            return ips[-1], None, 'down'
        else:
            split = IpParser(host_line).isolate_IPs()
            if len(split) == 4:  # same IP is provided in place of hostname
                return split[2][1], None, 'up'
            if len(split) == 3:  # find hostname in first piece of split
                ip = split[1][1]
                hostname = split[0][1].split(' ')[0]
                return ip, hostname, 'up'


if __name__ == '__main__':
    from time import sleep
    from src.utils.timer import TimerThread
    timer = TimerThread(autostart=True)
    fping = PModFping(timer=timer, params={'period': '1000', 'netIP': '192.168.1.0/28'})
    fping.set_read_interval(5)
    print(fping.build_final_cmd())
    fping.launch()
    sleep(10)
    timer.stop()
