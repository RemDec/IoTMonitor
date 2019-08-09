from modules.abcActiveModule import *
from src.utils.misc_fcts import get_ip, log_feedback_available
from src.parsers.nmapOutputParser import NmapParser, iplist_to_nmap
from lxml import etree


desc_PARAMS = {"IP": "Target IP address(es) acceptable as Nmap syntax",
               "SYNports": "Ports targeted for SYN probing",
               "UDPports": "Ports targeted for UDP probing",
               "XMLfile": "The temp file where scan output will be written",
               "options": "other options compatible with -sn to pass to nmap"}


class AModNmapExplorer(ActiveModule):
    """Active Module designed to explore the network and discover which equipments are active on it.

    Generally discover all MAC and IP addresses of responding equipments quickly. Written from skeleton.
    """

    def __init__(self, params=None, netmap=None):
        super().__init__(netmap)
        self.m_id = "nmapexplo"
        self.CMD = "nmap -sn"
        subnetwork = get_ip(mask='24')
        self.PARAMS = {
                       "SYNports": ("21,22,23,80,443,3389", True, "-PS"),
                       "UDPports": ("53,135,137,161", True, "-PU"),
                       "XMLfile": ("/tmp/nmapexplo.xml", True, "-oX "),
                       "options": ("", False, ""),
                       "IP": (subnetwork, True, "")
                       }
        self.desc_PARAMS = desc_PARAMS

        self.set_params(params)

    def get_description(self):
        return f"[{self.m_id}] Nmap scan to discover hosts (-sn mode, no port scanning)" \
               f" by SYN/UDP probing on common ports (really fast)"

    def get_module_id(self):
        return self.m_id

    def get_cmd(self):
        return self.CMD

    def get_params(self):
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def parse_output(self, output):
        if self.netmap is None:
            return
        try:
            parser = NmapParser(output.read().encode())
        except etree.XMLSyntaxError:
            return
        hosts = parser.get_hosts()
        changed = 0
        for host in hosts:
            state = host.find('status').get('state', 'unknown')
            mac, ip, other = parser.addr_from_host(host, lambda a: [('manufacturer', a.get('vendor'))])
            hostname = parser.hostname_from_host(host)
            div = {'manufacturer': other['manufacturer']} if other.get('manufacturer') is not None else {}
            if self.netmap is not None:
                mapid = self.netmap.get_similar_vi(mac=mac, ip=ip, hostname=hostname)
                if mapid is None:
                    mapid, vi = self.netmap.create_vi(mac=mac, ip=ip, hostname=hostname, div=div)
                    changed += 1
                    vi.set_state(state)
                    self.netmap.register_modif('VI ' + mapid, elmt_id=mapid, modificator=self.m_id,
                                               old_state='Non-existing VI', new_state='New VI instance',
                                               logit_with_lvl=20)
                    import logging
                    logging.getLogger('discover').info(ip)
                else:
                    vi = self.netmap.get_vi(mapid)
                    vi.set_state(state)
                    old = vi.detail_str(2)
                    changed_this_vi = vi.complete_fields(mac=mac, ip=ip, hostname=hostname, div=div)
                    if changed_this_vi:
                        self.netmap.register_modif('VI ' + mapid, elmt_id=mapid,
                                                   modificator=self.m_id, old_state=old, new_state=vi.detail_str(2),
                                                   logit_with_lvl=20)
                        changed += 1
        name = f"Module [{self.m_id}]"
        if changed:
            self.did_modification(nbr=changed)
            log_feedback_available(f"{name} created/updated {changed} VIs")
        else:
            log_feedback_available(f"{name} didn't find any new information amongst {len(hosts)} hosts analyzed")

    def distrib_output(self, script_output, rel_to_vi=[]):
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout
            log_feedback_available(f"Module [{self.m_id}] execution returned (code {code})", logitin='info', lvl='info')
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            py_except, popen = script_output
            log_feedback_available(f"Module [{self.m_id}] execution raised exception :{py_except}",
                                   logitin='error', lvl='error')

    def launch(self, rel_to_vi=[]):
        logging.getLogger('discover').info('call')
        super().purge_threadlist()
        cmd = self.CMD + ' '
        for param, val in self.params.items():
            if param == 'IP':
                iplist = val
                if len(rel_to_vi) > 0 and self.netmap is not None:
                    # Replace IPs to consider by specified ones
                    iplist = iplist_to_nmap(self.netmap.get_IPs_from_mapids(rel_to_vi))
                cmd += iplist + ' '
            else:
                cmd += self.PARAMS[param][2] + val + ' '
        cmd += '> /dev/null && cat ' + self.params['XMLfile']
        s_thread = self.get_script_thread()
        s_thread.start(cmd)
        super().register_thread(s_thread)

    def stop(self):
        super().terminate_threads()

    def get_script_thread(self, rel_to_vi=[]):
        return ScriptThread(callback_fct=self.distrib_output, rel_to_vi=rel_to_vi, max_exec_time=60)

    def get_default_timer(self):
        return 60

    def install_info(self):
        return {'program': "nmap", 'version': "7.01",
                'install': {'apt': "nmap",
                            'yum': "nmap",
                            'snap': "nmap"
                            }
                }


if __name__ == '__main__':
    from src.logging.eventsCenter import *
    EventsCenter()
    nmap = AModNmapExplorer()
    print(nmap)
    nmap.launch()
    print("Directly after launching :\n", nmap)
    from time import sleep
    sleep(1)
    print("Waited a few second for launching thread :\n", nmap)
    sleep(15)
    print("After waiting :\n", nmap)