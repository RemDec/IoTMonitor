from modules.abcFacilityActiveModule import FacilityActiveModule
from src.parsers.nmapOutputParser import NmapParser, cpes_to_dict, iplist_to_nmap
from src.net.virtualInstance import PortTable
from src.utils.misc_fcts import get_ip, log_feedback_available
from lxml import etree
import logging


class AModNmapVulners(FacilityActiveModule):
    """Active Module pulling service version infos from host accessible ports and searching known vulnerabilities.

    It performs an online search in Vulners database that contains some CVEs entries to match to version of services.
    This is implemented in the NSE script nmap-vulners. Vulnerabilities are returned in the XML output but in one block,
    requiring extra parsing to get individual CVE information and instantiating corresponding threat, registering it
    in the application and alerting it by mail.
    Written using provided facility for active modules.
    """

    def __init__(self, params=None, netmap=None):
        self.scheme = {'ports': ('usetop', False, '-p'),
                       'nbrports': ('5', True, '--top-ports '),
                       'XMLfile': ('/tmp/nmap_vulners.xml', True, '-oX '),
                       'options': ('', False, ''),
                       'IP': (get_ip(mask=24), True, "")
                       }
        self.desc = {'ports': "Specific port numbers to target, unspecified implies using top most generally used",
                     'nbrports': "The number of top most used ports considered if specific ports are not specified",
                     'XMLfile': "The temp file where scan output will be written",
                     "options": "other options compatible with -sn to pass to nmap",
                     "IP": "Target IP address(es) acceptable as Nmap syntax"
                     }
        super().__init__(params, netmap)

    def get_description(self):
        return f"[{self.get_module_id()}] Nmap scan using NSE script nmap-vulners (v1.2-release), checking for" \
               f" services CVE in online DB but also good at services discovery"

    def get_module_id(self):
        return "nmapvulners"

    def get_cmd(self):
        return "nmap -sV -script=nmap-vulners"

    def get_scheme_params(self):
        return self.scheme

    def get_desc_params(self):
        return self.desc

    def build_final_cmd(self, rel_to_vi=[]):
        use_spec_ports = False
        cmd = self.get_cmd() + ' '
        for param, val in self.get_curr_params().items():
            if param == 'IP':
                iplist = val
                if len(rel_to_vi) > 0 and self.netmap is not None:
                    # Replace IPs to consider by specified ones
                    iplist = iplist_to_nmap(self.netmap.get_IPs_from_mapids(rel_to_vi))
                cmd += iplist + ' '
            elif param == 'ports':
                if val != 'usetop':
                    use_spec_ports = True
                    cmd += self.scheme[param][2] + val + ' '
            elif param == 'nbrports' and use_spec_ports:
                continue  # Do not use and include the top-port flag in the command
            else:
                cmd += self.scheme[param][2] + val + ' '
        cmd += '> /dev/null && cat ' + self.get_curr_params()['XMLfile']
        return cmd

    def work_before_launching(self, cmd_to_exec, exec_script_thread, rel_to_vi=[]):
        from os import remove
        try:
            remove(self.get_curr_params().get('XMLfile'))
        except FileNotFoundError:
            pass

    def parse_output(self, output_stream, rel_to_vi=[]):
        if self.netmap is None:
            return
        try:
            parser = NmapParser(output_stream.read().encode())
        except etree.XMLSyntaxError:
            return
        hosts = parser.get_hosts()
        threats = []
        for host_elmt in hosts:
            mac, ip, _ = parser.addr_from_host(host_elmt)
            hostname = parser.hostname_from_host(host_elmt)
            state = parser.state_from_host(host_elmt)
            table, vulns = self.fill_ports_table_and_vulners_output(parser, host_elmt)
            mapid = self.netmap.get_similar_vi(mac=mac, ip=ip, hostname=hostname)
            # Updating or creating corresponding VI based on retrieved informations
            if mapid is None:
                port_table = PortTable(table)
                mapid, vi = self.netmap.create_vi(mac=mac, ip=ip, hostname=hostname, ports=port_table)
                vi.set_state(state)
                self.netmap.register_modif('VI ' + mapid, elmt_id=mapid, modificator=self.get_module_id(),
                                           old_state='Non-existing VI',
                                           new_state='New VI instance with PortTable:\n'+port_table.detail_str(1),
                                           logit_with_lvl=20)
                super().did_modification()
            else:
                vi = self.netmap.get_vi(mapid)
                vi.set_state(state)
                old = vi.detail_str(2)
                old_portstable = vi.get_ports_table().detail_str(level=3)
                changed_fields, changed_ports = False, False
                if vi.complete_fields(mac=mac, ip=ip, hostname=hostname):
                    new = vi.detail_str(2)
                    self.netmap.register_modif('VI ' + mapid, elmt_id=mapid, modificator=self.get_module_id(),
                                               old_state=old, new_state=new, logit_with_lvl=20)
                    changed_fields = True
                if vi.complete_ports_table(table):
                    new_portstable = vi.get_ports_table().detail_str(level=3)
                    self.netmap.register_modif('PortsTable VI ' + mapid, elmt_id=mapid,
                                               modificator=self.get_module_id(), old_state=old_portstable,
                                               new_state=new_portstable, logit_with_lvl=20)
                    changed_ports = True
                if changed_fields or changed_ports:
                    super().did_modification()
            # Registering CVE as threat events
            for portnum in vulns:
                service_cpe, list_CVEs_infos = vulns.get(portnum)
                for dict_infos in list_CVEs_infos:
                    msg = f"Threat found registered as {dict_infos.get('code', 'CVE')}"
                    patch = f"Online CVE details : {dict_infos.get('url', 'no url')}"
                    lvl = float(dict_infos.get('severity', 1))
                    threat = self.netmap.register_threat(self.get_module_id(), level=lvl, mapid=mapid,
                                                         msg=msg, patch=patch, logit_with_lvl=40)
                    if threat is not None:  # The threat was not reported yet
                        threats.append(threat)

        if len(threats):
            super().found_threat(len(threats))
            msg = f"Module [{self.get_module_id()}] found {len(threats)} vulnerabilities/threats"
            log_feedback_available(msg)
            # Sending recap email with threats
            threats = list(map(lambda th: th.detail_str(4), threats))
            msg += "\n Description of discovered threats :\n\n" + '\n\n'.join(threats)
            logging.getLogger('mail').critical(msg)
        else:
            log_feedback_available(f"Module [{self.get_module_id()}] did not find any (new) threat")

    def fill_ports_table_and_vulners_output(self, parser, host_elmt):
        # Returns a dict from which PortTable of host is built and a second dict with found CVE(s) for each port
        table = {}
        vulns = {}
        div_port_attrs = ('product', 'version', 'extrainfo', 'conf')
        for port_elmt in parser.portlist_from_host(host_elmt):
            port_fields = parser.get_host_fields(port_elmt, fields=('service', 'script'))
            # Main port information (num, service, protocol, state)
            portnum, portservice, protocol, portstate = parser.maininfos_from_port(port_elmt)
            # Checking for vuln found by Vulners script
            script_elmts = port_fields['script']
            for script in script_elmts:
                if script.get('id') == 'vulners':
                    # Update vulns dict with portnum -> corresp CVE entries
                    self.treat_vulnscript_output(portnum, script, vulns)
            # Test relevant
            port_service_elmt = port_fields['service'][0]
            conf = int(port_service_elmt.get('conf', 10))
            if portstate in ['closed', 'filtered'] and conf <= 3:
                # Avoid abusive information feedback certainly wrong
                continue
            # Diverse
            div_portinfos = parser.get_attr_dict_from_elmt(port_service_elmt, attrs=div_port_attrs)
            div_portinfos.update(cpes_to_dict(port_service_elmt.findall('cpe')))
            # Filling dict from which PortTable is built
            table[int(portnum)] = (portservice, protocol.upper(), portstate, div_portinfos)
        return table, vulns

    def treat_vulnscript_output(self, portnum, script_elmt, vulns_dict):
        # Split CVEs list in individual entries, update dict value corresponding to portnum with new parsed CVE(s) list
        all_cves_infos = []
        service_cpe = 'cpe:/a:'
        for cpe_table in script_elmt.findall('table'):
            service_cpe = cpe_table.get('key')
            for cve_table in cpe_table.findall('table'):
                cve_dict = dict.fromkeys(['code', 'severity', 'url'], 'unknown')
                for elem in cve_table.findall('elem'):
                    key = elem.get('key')
                    if key == 'id':
                        cve_dict['code'] = elem.text
                    elif key == 'cvss':
                        cve_dict['severity'] = elem.text
                if cve_dict['code'] != 'unknown':
                    cve_dict['url'] = 'https://vulners.com/cve/' + cve_dict['code']
                all_cves_infos.append(cve_dict)
        vulns_dict[portnum] = (service_cpe, all_cves_infos)

    def treat_vulnscript_output_old(self, portnum, script_elmt, vulns_dict):
        # Split CVEs list in individual entries, update dict value corresponding to portnum with new parsed CVE(s) list
        service_cpe_elmt = script_elmt.find('elem')
        service_cpe = service_cpe_elmt.get('key')
        vulns_txt = service_cpe_elmt.text.strip()
        CVEs = vulns_txt.split('\n\t')
        all_CVEs_infos = []
        for CVE in CVEs:
            CVEcode, severity, url = CVE.split('\t\t')
            all_CVEs_infos.append({'code': CVEcode, 'severity': severity, 'url': url})
        vulns_dict[portnum] = (service_cpe, all_CVEs_infos)

    def install_info(self):
        return {'program': "nmap", 'version': "7.01",
                'install': {'apt': "nmap",
                            'yum': "nmap",
                            'snap': "nmap"
                            }
                }


if __name__ == '__main__':
    # from src.utils.moduleManager import ModDescriptor
    from src.net.netmap import Netmap
    vulners = AModNmapVulners(params={'nbrports': '2', 'IP': '192.168.0.5'}, netmap=Netmap())
    vulners.launch()
    # desc = ModDescriptor(mod_inst=vulners, include_nondefault_param=True)
    # desc.modinfos_to_xml()
