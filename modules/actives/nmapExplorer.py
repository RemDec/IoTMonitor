from modules.abcActiveModule import *
from src.utils.misc_fcts import get_ip
from src.parsers.nmapOutputParser import NmapParser
from lxml import etree


desc_PARAMS = {"IP": "Target IP address(es) acceptable as Nmap syntax",
               "SYNports": "Ports targeted for SYN probing",
               "UDPports": "Ports targeted for UDP probing",
               "XMLfile": "The temp file where scan output will be written",
               "options": "other options compatible with -sn to pass to nmap"}


class AModNmapExplorer(ActiveModule):

    def __init__(self, params=None, netmap=None):
        super().__init__(netmap)
        self.m_id = "nmapexplo"
        self.CMD = "nmap -sn"
        subnetwork = get_ip(mask='24')
        self.PARAMS = {"options": ("", False, ""),
                       "SYNports": ("21,22,23,80,443,3389", True, "-PS"),
                       "UDPports": ("53,135,137,161", True, "-PU"),
                       "XMLfile": ("/tmp/xml_nmapexplo.xml", True, "-oX "),
                       "IP": (subnetwork, True, "")
                       }
        self.desc_PARAMS = desc_PARAMS

        self.set_params(params)

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
            parser = NmapParser(output)
        except etree.XMLSyntaxError:
            import logging
            logging.getLogger('error').exception("Nmapparser were unable to parse XML tree result of nmapExplorer")
            return
        hosts = parser.get_hosts()
        changed = 0
        for host in hosts:
            state = host.find('status').get('state', 'unknown')
            mac, ip, other = parser.addr_from_host(host, lambda a: [('manufacturer', a.get('vendor'))])
            hostname = parser.hostname_from_host(host)
            div = {'manufacturer': other['manufacturer']} if other.get('manufacturer') is not None else {}
            if self.netmap is not None:
                mapid = self.netmap.get_similar_VI(mac=mac, ip=ip, hostname=hostname)
                if mapid is None:
                    mapid, vi = self.netmap.create_VI(mac=mac, ip=ip, hostname=hostname, div=div)
                    changed += 1
                    vi.set_state(state)
                    self.netmap.register_modif('VI '+mapid, obj_type='virt_inst', obj_id=mapid, modificator=self.m_id,
                                               old_state='Non-existing VI', new_state='New VI instance',
                                               logit_with_lvl=20)
                else:
                    vi = self.netmap.get_VI(mapid)
                    old = vi.detail_str(2)
                    changed_this_vi = vi.complete_fields(mac=mac, ip=ip, hostname=hostname, div=div)
                    if changed_this_vi:
                        self.netmap.register_modif('VI ' + mapid, obj_type='virt_inst', obj_id=mapid,
                                                   modificator=self.m_id, old_state=old, new_state=vi.detail_str(2),
                                                   logit_with_lvl=20)
                        changed += 1
        name = f"Module [{self.m_id}]"
        if changed:
            logging.log_feedback(f"{name} created/updated {changed} VIs")
        else:
            logging.log_feedback(f"{name} didn't find any new information amongst {len(hosts)} hosts analyzed")

    def distrib_output(self, script_output, rel_to_vi=[]):
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout
            logging.log_feedback(f"Module [{self.m_id}] execution returned (code {code})", logitin='info', lvl='info')
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            py_except, popen = script_output
            logging.log_feedback(f"Module [{self.m_id}] execution raised exception :{py_except}",
                                 logitin='error', lvl='error')

    def launch(self, rel_to_vi=[]):
        super().purge_threadlist()
        cmd = self.CMD + ' '
        for param, val in self.params.items():
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

    def get_description(self):
        return f"[{self.m_id}] Nmap scan to discover hosts (-sn mode, no port scanning)" \
               f" by SYN/UDP probing on common ports (need sudo)"

    def get_module_id(self):
        return self.m_id


if __name__ == '__main__':
    from src.logging.eventsCenter import *
    EventsCenter()
    print(logging.log_feedback)
    nmap = AModNmapExplorer()
    print(nmap)
    nmap.launch()
    print("Directly after launching :\n", nmap)
    from time import sleep
    sleep(1)
    print("Waited a few second for launching thread :\n", nmap)
    sleep(15)
    print("After waiting :\n", nmap)