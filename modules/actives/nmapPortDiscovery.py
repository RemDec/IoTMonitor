from modules.abcActiveModule import *
from src.utils.misc_fcts import get_ip, log_feedback_available
from src.parsers.nmapOutputParser import NmapParser, cpes_to_dict, iplist_to_nmap
from src.net.virtualInstance import PortTable
from lxml import etree


class AModNmapPortDisc(ActiveModule):

    def __init__(self, params=None, netmap=None):
        """Active Module whose purpose is used host ports discovery and service running on it.

        Written from skeleton.
        """
        super().__init__(netmap)
        self.m_id = "nmapports"
        self.CMD = "nmap"
        self.PARAMS = {'options': ("", False, ""),
                       'nbrports': ("50", True, "--top-ports "),
                       'version': ("false", True, "-sV"),
                       'XMLfile': ("/tmp/nmap_portdisc.xml", True, "-oX "),
                       'IP': (get_ip(mask=24), True, "")
                       }
        self.desc_PARAMS = {'options': "Others options to pass to nmap scan",
                            'nbrports': "How many of top most used ports should be probed",
                            'version': "Should try to guess running version of services (heavy in time)",
                            'XMLfile': "The temp file where scan output will be written",
                            "IP": "Target IP address(es) acceptable as Nmap syntax"}
        self.set_params(params)
        self.max_exec_time = 340

    def get_description(self):
        return f"[{self.m_id}] Nmap scan focusing on used ports discovery, attempting on a nbr of top most common ports"

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
        div_port_attrs = ('product', 'version', 'extrainfo', 'conf')
        changed_vi = 0
        changed_table = 0
        for host_elmt in hosts:
            mac, ip, _ = parser.addr_from_host(host_elmt)
            hostname = parser.hostname_from_host(host_elmt)
            state = parser.state_from_host(host_elmt)
            table = {}
            for port_elmt in parser.portlist_from_host(host_elmt):
                # Main informations
                port_fields = parser.get_host_fields(port_elmt, fields=('state', 'service', 'script'))
                port_state = port_fields['state'][0].get('state')
                conf = int(port_fields['service'][0].get('conf', 10))
                if port_state in ['closed', 'filtered'] and conf <= 3:
                    # Avoid abusive information feedback certainly wrong
                    continue
                prot, port_nbr = port_elmt.get('protocol'), port_elmt.get('portid')
                port_service_elmt = port_fields['service'][0]
                port_service = port_service_elmt.get('name')
                # Diverse
                div_portinfos = parser.get_attr_dict_from_elmt(port_service_elmt, attrs=div_port_attrs)
                div_portinfos.update(cpes_to_dict(port_service_elmt.findall('cpe')))
                # Filling dict from which PortTable is built
                table[int(port_nbr)] = (port_service, prot.upper(), port_state, div_portinfos)
            # Updating or creating corresponding VI based on retrieved informations
            mapid = self.netmap.get_similar_vi(mac=mac, ip=ip, hostname=hostname)
            if mapid is None:
                port_table = PortTable(table)
                mapid, vi = self.netmap.create_vi(mac=mac, ip=ip, hostname=hostname, ports=port_table)
                vi.set_state(state)
                self.netmap.register_modif('VI '+mapid, obj_type='virt_inst', obj_id=mapid, modificator=self.m_id,
                                           old_state='Non-existing VI',
                                           new_state='New VI instance with PortTable:\n'+port_table.detail_str(1),
                                           logit_with_lvl=20)
                changed_vi += 1
                changed_table += 1
            else:
                vi = self.netmap.get_vi(mapid)
                vi.set_state(state)
                old = vi.detail_str(2)
                old_portstable = vi.get_ports_table().detail_str(level=3)
                changed_this_vi = vi.complete_fields(mac=mac, ip=ip, hostname=hostname)
                changed_this_portstable = vi.complete_ports_table(table)
                changed_vi += int(changed_this_vi)
                changed_table += int(changed_this_portstable)
                if changed_this_vi:
                    new = vi.detail_str(2)
                    self.netmap.register_modif('VI ' + mapid, obj_type='virt_inst', obj_id=mapid, modificator=self.m_id,
                                               old_state=old, new_state=new, logit_with_lvl=20)
                if changed_this_portstable:
                    new_portstable = vi.get_ports_table().detail_str(level=3)
                    self.netmap.register_modif('PortsTable VI ' + mapid, obj_type='virt_inst', obj_id=mapid,
                                               modificator=self.m_id, old_state=old_portstable,
                                               new_state=new_portstable, logit_with_lvl=20)
        name = f"Module [{self.m_id}]"
        if changed_vi+changed_table:
            super().did_modification(changed_vi+changed_table)
            log_feedback_available(f"{name} created/updated {changed_vi} VIs and {changed_table} of their ports tables")
        else:
            log_feedback_available(f"{name} didn't find any new information amongst {len(hosts)} hosts analyzed")

    def distrib_output(self, script_output, rel_to_vi=[]):
        # function called by ending exec thread with script_output as a tuple summarizing how it ended
        if isinstance(script_output[0], int):
            code, popen = script_output
            output = popen.stdout
            # if code OK, should parse results to integrate in app (netmap, alert threats, ..)
            log_feedback_available(f"Module [{self.m_id}] execution returned (code {code})", logitin='info', lvl='debug')
            if self.netmap is not None:
                self.parse_output(output)
        elif isinstance(script_output[0], Exception):
            # pull info from exception
            py_except, popen = script_output
            log_feedback_available(f"Module [{self.m_id}] execution raised exception :{py_except}",
                                   logitin='error', lvl='error')

    def launch(self, rel_to_vi=[]):
        super().purge_threadlist()
        cmd = self.CMD + ' '
        for param, val in self.params.items():
            if param == 'version':
                cmd += '-sV ' if val == 'true' else ''
            elif param == 'IP':
                iplist = val
                if len(rel_to_vi) > 0 and self.netmap is not None:
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
        return ScriptThread(callback_fct=self.distrib_output, rel_to_vi=rel_to_vi,
                            max_exec_time=self.max_exec_time)

    def get_default_timer(self):
        return 60


if __name__ == '__main__':
    nmap = AModNmapPortDisc(params={'IP': get_ip(), 'nbrports': "10"})
    nmap.launch()