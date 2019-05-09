from modules.abcActiveModule import *
from src.utils.misc_fcts import get_ip
from src.parsers.nmapOutputParser import NmapParser
from src.net.virtualInstance import PortTable


class AModNmapPortDisc(ActiveModule):

    def __init__(self, params=None, netmap=None):
        super().__init__(netmap)
        self.m_id = "nmapports"
        self.CMD = "nmap"
        self.PARAMS = {'options': ("", False, ""),
                       'nbrports': ("50", True, "--top-ports "),
                       'version': ("true", True, "-sV"),
                       'XMLfile': ("/tmp/xml_nmap_portdisc.xml", True, "-oX "),
                       'IP': (get_ip(mask=24), True, "")
                       }
        self.desc_PARAMS = {'options': "Others options to pass to nmap scan",
                            'nbrports': "How many of top most used ports should be probed",
                            'version': "Should try to guess running version of services",
                            'XMLfile': "The temp file where scan output will be written",
                            "IP": "Target IP address(es) acceptable as Nmap syntax"}
        self.set_params(params)
        self.max_exec_time = 340

    def get_cmd(self):
        return self.CMD

    def get_params(self):
        return self.params, self.PARAMS, self.desc_PARAMS

    def set_params(self, params):
        self.params = super().treat_params(self.PARAMS, {} if params is None else params)

    def parse_output(self, IO_buffer):
        parser = NmapParser(IO_buffer)
        hosts_infos = parser.get_hosts_fields(fields=('port', ))
        for host_elmt, children in hosts_infos:
            ip, mac, _ = parser.addr_from_host(host_elmt)
            state = host_elmt.find('status').get('state')
            table = {}
            for port_elmt in children['port']:
                prot, port_nbr = port_elmt.get('protocol'), port_elmt.get('portid')
                port_state = port_elmt.find('state').get('state')
                port_service = port_elmt.find('service').get('name')
                table[int(port_nbr)] = (port_service, prot.upper(), port_state)
            if self.netmap is not None:
                mapid = self.netmap.get_similar_VI(mac=mac, ip=ip)
                if mapid is None:
                    self.netmap.create_VI(mac=mac, ip=ip, ports=PortTable(table))[1].set_state(state)
                else:
                    vi = self.netmap.get_VI(mapid)
                    vi.complete_fields(mac=mac, ip=ip)
                    vi.complete_ports_table(table)

    def distrib_output(self, script_output):
        # function called by ending exec thread with script_output as a tuple summarizing how it ended
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout
            # if code OK, should parse results to integrate in app (netmap, alert threats, ..)
            logging.getLogger("debug").debug(f"Module [{self.m_id}] execution returned (code {code})")
            self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            # pull info from exception
            py_except, popen = script_output
            logging.getLogger("debug").debug(f"Module [{self.m_id}] execution raised exception :{py_except}")

    def launch(self):
        super().purge_threadlist()
        cmd = self.CMD + ' '
        for param, val in self.params.items():
            if param == 'version':
                cmd += '-sV ' if val == 'true' else ''
            else:
                cmd += self.PARAMS[param][2] + val + ' '
        cmd += '> /dev/null && cat ' + self.params['XMLfile']
        s_thread = self.get_script_thread()
        s_thread.start(cmd)
        super().register_thread(s_thread)

    def stop(self):
        super().terminate_threads()

    def get_script_thread(self):
        return ScriptThread(callback_fct=self.distrib_output, max_exec_time=self.max_exec_time, cmd_as_shell=True)

    def get_default_timer(self):
        return 60

    def get_description(self):
        return f"[{self.m_id}] Nmap scan focusing on used ports discovery, attempting on a nbr of top most common ports"

    def get_module_id(self):
        return self.m_id


if __name__ == '__main__':
    nmap = AModNmapPortDisc(params={'IP': get_ip(), 'nbrports': "10"})
    nmap.launch()