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
        subnetwork = get_ip(mask='24')
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
        try:
            parser = NmapParser(output)
        except etree.XMLSyntaxError:
            return
        hosts = parser.get_hosts()
        for host in hosts:
            state = host.find('status').get('state')
            ip, mac, other = parser.addr_from_host(host, lambda a: [('manuf', a.get('vendor'))])
            manuf = other['manuf']
            if self.netmap is not None:
                mapid = self.netmap.get_similar_VI(mac=mac, ip=ip)
                if mapid is None:
                    self.netmap.create_VI(mac=mac, ip=ip, div={'manufacturer': manuf})[1].set_state(state)
                else:
                    self.netmap.get_VI(mapid).complete_fields(mac=mac, ip=ip, div={'manufacturer': manuf})

    def distrib_output(self, script_output, rel_to_vi=[]):
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout
            logging.getLogger("debug").debug(f"Module [{self.m_id}] execution returned (code {code})")
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            py_except, popen = script_output
            logging.getLogger("debug").debug(f"Module [{self.m_id}] execution raised exception :{py_except}")

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
    nmap = AModNmapExplorer()
    print(nmap)
    nmap.launch()
    print("Directly after launching :\n", nmap)
    from time import sleep
    sleep(1)
    print("Waited a few second for launching thread :\n", nmap)
    sleep(15)
    print("After waiting :\n", nmap)